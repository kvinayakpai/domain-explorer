import { NextRequest } from "next/server";
import { buildGrounding, buildCannedAnswer, renderGroundingForLlm } from "@/lib/grounding";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const SYSTEM_PROMPT_BASE = `You are the Domain Explorer assistant. You answer questions grounded \
in a typed YAML registry of industry subdomains, personas, decisions, KPIs, source systems, and \
connector patterns. The user has selected a persona; treat their question as coming from that \
person's perspective and prioritise the decisions and KPIs they own.

Hard rules:
- Ground every claim in the GROUNDING CONTEXT below. If something is not in the context, say so.
- When listing KPIs, source systems, or connectors, prefer the records you were given.
- Be concise. Prefer short paragraphs and tight bullet lists over long prose.
- Never invent KPI ids or vendor products that aren't in the context.`;

interface ChatBody {
  message?: string;
  personaKey?: string;
  history?: { role: "user" | "assistant"; content: string }[];
}

function jsonError(status: number, message: string): Response {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { "content-type": "application/json" },
  });
}

/** Normalise the body into a safe shape. */
function readBody(raw: unknown): ChatBody {
  const obj = (raw ?? {}) as Record<string, unknown>;
  const message = typeof obj.message === "string" ? obj.message : "";
  const personaKey = typeof obj.personaKey === "string" ? obj.personaKey : undefined;
  const history = Array.isArray(obj.history)
    ? obj.history.flatMap((h) => {
        if (!h || typeof h !== "object") return [];
        const r = (h as Record<string, unknown>).role;
        const c = (h as Record<string, unknown>).content;
        if ((r === "user" || r === "assistant") && typeof c === "string") {
          return [{ role: r, content: c }];
        }
        return [];
      })
    : [];
  return { message, personaKey, history };
}

/** Stream a plain-text response in the SSE-ish format the client expects. */
function streamText(text: string, recordsUsed: string[], mode: "live" | "demo"): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      // Header event — tells the client which mode + grounding records are in use.
      const header = JSON.stringify({ kind: "header", mode, recordsUsed });
      controller.enqueue(encoder.encode(`event: header\ndata: ${header}\n\n`));
      // Chunk the canned answer into ~50-char windows so the UI gets a streamy feel.
      const step = 60;
      for (let i = 0; i < text.length; i += step) {
        const chunk = text.slice(i, i + step);
        controller.enqueue(
          encoder.encode(`event: delta\ndata: ${JSON.stringify({ text: chunk })}\n\n`),
        );
        // small async tick so the network actually flushes between chunks
        await new Promise((r) => setTimeout(r, 8));
      }
      controller.enqueue(encoder.encode(`event: done\ndata: {}\n\n`));
      controller.close();
    },
  });
  return new Response(stream, {
    headers: {
      "content-type": "text/event-stream; charset=utf-8",
      "cache-control": "no-cache, no-transform",
      "x-accel-buffering": "no",
    },
  });
}

/**
 * Try to load the Anthropic SDK lazily. Returns null if it isn't installed —
 * the route then falls back to canned mode.
 */
async function loadAnthropic(): Promise<unknown | null> {
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const mod: any = await import("@anthropic-ai/sdk").catch(() => null);
    if (!mod) return null;
    return mod.default ?? mod.Anthropic ?? mod;
  } catch {
    return null;
  }
}

async function streamFromAnthropic(opts: {
  apiKey: string;
  systemPrompt: string;
  history: { role: "user" | "assistant"; content: string }[];
  message: string;
  recordsUsed: string[];
}): Promise<Response | null> {
  const Anthropic = (await loadAnthropic()) as unknown as
    | (new (cfg: { apiKey: string }) => unknown)
    | null;
  if (!Anthropic) return null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const client: any = new (Anthropic as any)({ apiKey: opts.apiKey });

  const messages = [
    ...opts.history.map((h) => ({ role: h.role, content: h.content })),
    { role: "user" as const, content: opts.message },
  ];

  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      try {
        const header = JSON.stringify({
          kind: "header",
          mode: "live",
          recordsUsed: opts.recordsUsed,
        });
        controller.enqueue(encoder.encode(`event: header\ndata: ${header}\n\n`));

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const upstream: any = client.messages.stream({
          model: "claude-sonnet-4-6",
          max_tokens: 1024,
          system: opts.systemPrompt,
          messages,
        });
        upstream.on("text", (delta: string) => {
          controller.enqueue(
            encoder.encode(`event: delta\ndata: ${JSON.stringify({ text: delta })}\n\n`),
          );
        });
        upstream.on("error", (err: Error) => {
          controller.enqueue(
            encoder.encode(
              `event: error\ndata: ${JSON.stringify({ message: String(err?.message ?? err) })}\n\n`,
            ),
          );
          controller.close();
        });
        upstream.on("end", () => {
          controller.enqueue(encoder.encode(`event: done\ndata: {}\n\n`));
          controller.close();
        });
        await upstream.finalMessage().catch(() => undefined);
      } catch (e) {
        controller.enqueue(
          encoder.encode(
            `event: error\ndata: ${JSON.stringify({ message: String((e as Error)?.message ?? e) })}\n\n`,
          ),
        );
        controller.close();
      }
    },
  });
  return new Response(stream, {
    headers: {
      "content-type": "text/event-stream; charset=utf-8",
      "cache-control": "no-cache, no-transform",
      "x-accel-buffering": "no",
    },
  });
}

export async function POST(req: NextRequest) {
  let body: ChatBody;
  try {
    body = readBody(await req.json());
  } catch {
    return jsonError(400, "invalid JSON body");
  }
  const message = (body.message ?? "").trim();
  if (!message) return jsonError(400, "missing message");

  const grounding = buildGrounding({
    question: message,
    personaKey: body.personaKey,
  });
  const groundingText = renderGroundingForLlm(grounding);
  const systemPrompt = `${SYSTEM_PROMPT_BASE}\n\n${groundingText}`;

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (apiKey) {
    const live = await streamFromAnthropic({
      apiKey,
      systemPrompt,
      history: body.history ?? [],
      message,
      recordsUsed: grounding.recordsUsed,
    });
    if (live) return live;
    // SDK couldn't be loaded — fall through to canned mode.
  }

  const answer = buildCannedAnswer(message, grounding);
  return streamText(answer, grounding.recordsUsed, "demo");
}
