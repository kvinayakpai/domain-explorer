/**
 * OpenAI provider — uses the official `openai` npm package. Loaded lazily so
 * the explorer still builds when the SDK isn't installed (e.g. for the offline
 * demo).
 */
import type { ChatArgs, LLMChunk, LLMProvider } from "./types";
import { LLMProviderError } from "./types";
import { RefStreamBuffer } from "./provider";

interface OpenAIChatCompletionDelta {
  choices?: { delta?: { content?: string | null } }[];
}

interface OpenAIClient {
  chat: {
    completions: {
      create(args: {
        model: string;
        stream: true;
        messages: { role: "system" | "user" | "assistant"; content: string }[];
        max_tokens?: number;
        signal?: AbortSignal;
      }): Promise<AsyncIterable<OpenAIChatCompletionDelta>>;
    };
  };
}

interface OpenAICtor {
  new (cfg: { apiKey: string; baseURL?: string }): OpenAIClient;
}

interface OpenAIModule {
  default?: OpenAICtor;
  OpenAI?: OpenAICtor;
}

async function loadOpenAI(): Promise<OpenAICtor | null> {
  try {
    const mod = (await import("openai").catch(() => null)) as OpenAIModule | null;
    if (!mod) return null;
    return mod.default ?? mod.OpenAI ?? null;
  } catch {
    return null;
  }
}

export class OpenAIProvider implements LLMProvider {
  readonly name = "openai";
  readonly defaultModel = process.env.OPENAI_MODEL ?? "gpt-4o-mini";

  isAvailable(): boolean {
    return Boolean(process.env.OPENAI_API_KEY);
  }

  async *streamChat(args: ChatArgs): AsyncIterable<LLMChunk> {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      throw new LLMProviderError(this.name, "auth", "OPENAI_API_KEY missing");
    }
    const Ctor = await loadOpenAI();
    if (!Ctor) {
      throw new LLMProviderError(this.name, "unknown", "openai npm pkg not installed");
    }
    const client = new Ctor({ apiKey });

    const messages: { role: "system" | "user" | "assistant"; content: string }[] = [
      { role: "system", content: args.system },
      ...args.messages.map((m) => ({ role: m.role, content: m.content })),
    ];

    let stream: AsyncIterable<OpenAIChatCompletionDelta>;
    try {
      stream = await client.chat.completions.create({
        model: args.model ?? this.defaultModel,
        stream: true,
        messages,
        max_tokens: 1024,
        signal: args.signal,
      });
    } catch (err) {
      const e = err as { status?: number; message?: string };
      throw new LLMProviderError(this.name, classify(e.status), e.message ?? String(err), e.status);
    }

    const buf = new RefStreamBuffer();
    try {
      for await (const evt of stream) {
        const delta = evt.choices?.[0]?.delta?.content;
        if (typeof delta === "string" && delta.length > 0) {
          const { text, refs } = buf.feed(delta);
          if (text) yield { type: "content", text };
          for (const r of refs) yield { type: "citation", source: r };
        }
      }
    } catch (err) {
      const e = err as { status?: number; message?: string };
      throw new LLMProviderError(this.name, classify(e.status), e.message ?? String(err), e.status);
    }
    const { text, refs } = buf.flush();
    if (text) yield { type: "content", text };
    for (const r of refs) yield { type: "citation", source: r };
    yield { type: "done", provider: this.name };
  }
}

function classify(status?: number): "rate_limit" | "timeout" | "server_error" | "unknown" {
  if (!status) return "unknown";
  if (status === 429) return "rate_limit";
  if (status === 408 || status === 504) return "timeout";
  if (status >= 500) return "server_error";
  return "unknown";
}
