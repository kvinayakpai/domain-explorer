/**
 * Anthropic provider — uses the official `@anthropic-ai/sdk`. Loaded lazily so
 * that environments without the SDK installed (or running offline tests) don't
 * blow up at import-time.
 */
import type { ChatArgs, LLMChunk, LLMProvider } from "./types";
import { LLMProviderError } from "./types";
import { RefStreamBuffer } from "./provider";

interface AnthropicCtor {
  new (cfg: { apiKey: string }): AnthropicClient;
}

interface AnthropicClient {
  messages: {
    stream(args: {
      model: string;
      max_tokens: number;
      system: string;
      messages: { role: "user" | "assistant"; content: string }[];
    }): AnthropicStream;
  };
}

interface AnthropicStream {
  on(event: "text", listener: (delta: string) => void): void;
  on(event: "error", listener: (err: Error) => void): void;
  on(event: "end", listener: () => void): void;
  finalMessage(): Promise<unknown>;
}

interface AnthropicModule {
  default?: AnthropicCtor;
  Anthropic?: AnthropicCtor;
}

async function loadAnthropic(): Promise<AnthropicCtor | null> {
  try {
    const mod = (await import("@anthropic-ai/sdk").catch(() => null)) as
      | AnthropicModule
      | null;
    if (!mod) return null;
    return mod.default ?? mod.Anthropic ?? null;
  } catch {
    return null;
  }
}

export class AnthropicProvider implements LLMProvider {
  readonly name = "anthropic";
  readonly defaultModel = process.env.ANTHROPIC_MODEL ?? "claude-sonnet-4-6";

  isAvailable(): boolean {
    return Boolean(process.env.ANTHROPIC_API_KEY);
  }

  async *streamChat(args: ChatArgs): AsyncIterable<LLMChunk> {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      throw new LLMProviderError(this.name, "auth", "ANTHROPIC_API_KEY missing");
    }
    const Ctor = await loadAnthropic();
    if (!Ctor) {
      throw new LLMProviderError(this.name, "unknown", "@anthropic-ai/sdk not installed");
    }
    const client = new Ctor({ apiKey });

    // Build a queue-driven async iterable from the Anthropic event emitter.
    type Event =
      | { kind: "delta"; text: string }
      | { kind: "end" }
      | { kind: "error"; err: Error };
    const queue: Event[] = [];
    let resolver: ((e: Event) => void) | null = null;
    const push = (e: Event) => {
      if (resolver) {
        const r = resolver;
        resolver = null;
        r(e);
      } else queue.push(e);
    };
    const next = (): Promise<Event> =>
      queue.length > 0
        ? Promise.resolve(queue.shift()!)
        : new Promise<Event>((resolve) => {
            resolver = resolve;
          });

    const upstream: AnthropicStream = client.messages.stream({
      model: args.model ?? this.defaultModel,
      max_tokens: 1024,
      system: args.system,
      messages: args.messages,
    });
    upstream.on("text", (delta) => push({ kind: "delta", text: delta }));
    upstream.on("error", (err) => push({ kind: "error", err }));
    upstream.on("end", () => push({ kind: "end" }));
    // Don't await `finalMessage()` here — the event loop drives the queue.
    upstream.finalMessage().catch(() => undefined);

    const buf = new RefStreamBuffer();
    while (true) {
      const e = await next();
      if (e.kind === "delta") {
        const { text, refs } = buf.feed(e.text);
        if (text) yield { type: "content", text };
        for (const r of refs) yield { type: "citation", source: r };
      } else if (e.kind === "error") {
        const status = (e.err as { status?: number }).status;
        const kind = classify(status);
        throw new LLMProviderError(this.name, kind, e.err.message, status);
      } else {
        // end
        const { text, refs } = buf.flush();
        if (text) yield { type: "content", text };
        for (const r of refs) yield { type: "citation", source: r };
        yield { type: "done", provider: this.name };
        return;
      }
    }
  }
}

function classify(status?: number): "rate_limit" | "timeout" | "server_error" | "unknown" {
  if (!status) return "unknown";
  if (status === 429) return "rate_limit";
  if (status === 408 || status === 504) return "timeout";
  if (status >= 500) return "server_error";
  return "unknown";
}
