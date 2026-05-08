import { NextRequest } from "next/server";
import { buildGrounding, renderGroundingForLlm } from "@/lib/grounding";
import { systemPromptFor } from "@/lib/assistant-prompts";
import { chat, type LLMChunk } from "@/lib/llm";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

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

/**
 * Bridge an `LLMChunk` async iterable onto the SSE wire format the existing
 * client expects. Adds a `header` event (mode + grounding records) up-front so
 * the UI can show the "live / demo / cached" badge immediately.
 */
function streamFromLlm(opts: {
  iter: AsyncIterable<LLMChunk>;
  recordsUsed: string[];
}): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const send = (event: string, payload: unknown) => {
        controller.enqueue(
          encoder.encode(`event: ${event}\ndata: ${JSON.stringify(payload)}\n\n`),
        );
      };

      // Initial header — we don't yet know which provider answered, so default
      // to "live" and let the trailing `done` event update the UI badge.
      send("header", { kind: "header", mode: "live", recordsUsed: opts.recordsUsed });

      try {
        for await (const chunk of opts.iter) {
          if (chunk.type === "content") {
            if (chunk.text) send("delta", { text: chunk.text });
          } else if (chunk.type === "citation") {
            send("citation", { source: chunk.source, label: chunk.label });
          } else if (chunk.type === "done") {
            send("done", {
              provider: chunk.provider,
              cached: Boolean(chunk.cached),
              latencyMs: chunk.latencyMs,
            });
          }
        }
      } catch (e) {
        send("error", { message: String((e as Error)?.message ?? e) });
      } finally {
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
  // Pick a vertical-tailored system prompt based on the resolved persona's
  // vertical (BFSI, Insurance, Healthcare, ...). Falls back to the generic
  // variant when no persona is selected.
  const verticalPrompt = systemPromptFor(grounding.persona?.vertical);
  // The new citation-discipline rule: the model MUST emit `[REF:<id>]` markers
  // after each claim. The streaming layer in `lib/llm/provider.ts` parses
  // these out and forwards them as separate `citation` SSE events.
  const citationGuidance =
    "EVERY claim must be followed by a [REF:<id>] tag where <id> is a registry " +
    "entry (subdomain id, KPI id, source system id, glossary term). The " +
    "frontend will replace these tags with citations.";
  const systemPrompt = `${verticalPrompt}\n\n${groundingText}\n\n${citationGuidance}`;

  const messages = [
    ...(body.history ?? []).map((h) => ({ role: h.role, content: h.content })),
    { role: "user" as const, content: message },
  ];

  const iter = chat({
    system: systemPrompt,
    messages,
    persona: grounding.persona?.key,
    vertical: grounding.persona?.vertical,
    signal: req.signal,
  });

  return streamFromLlm({ iter, recordsUsed: grounding.recordsUsed });
}
