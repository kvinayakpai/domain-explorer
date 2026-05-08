/**
 * Google Gemini provider — uses `@google/generative-ai`. Loaded lazily.
 *
 * Gemini's chat-history shape uses `parts: [{ text }]` and `role: "user" |
 * "model"` — we adapt our shared `LLMMessage[]` shape into that form here.
 */
import type { ChatArgs, LLMChunk, LLMProvider } from "./types";
import { LLMProviderError } from "./types";
import { RefStreamBuffer } from "./provider";

interface GeminiContent {
  role: "user" | "model";
  parts: { text: string }[];
}

interface GeminiStreamResult {
  stream: AsyncIterable<{ text(): string }>;
}

interface GeminiModel {
  generateContentStream(args: {
    contents: GeminiContent[];
    systemInstruction?: { role: "system"; parts: { text: string }[] };
  }): Promise<GeminiStreamResult>;
}

interface GeminiClient {
  getGenerativeModel(args: { model: string }): GeminiModel;
}

interface GoogleCtor {
  new (apiKey: string): GeminiClient;
}

interface GoogleModule {
  default?: GoogleCtor;
  GoogleGenerativeAI?: GoogleCtor;
}

async function loadGoogle(): Promise<GoogleCtor | null> {
  try {
    const mod = (await import("@google/generative-ai").catch(() => null)) as
      | GoogleModule
      | null;
    if (!mod) return null;
    return mod.GoogleGenerativeAI ?? mod.default ?? null;
  } catch {
    return null;
  }
}

export class GoogleProvider implements LLMProvider {
  readonly name = "google";
  readonly defaultModel = process.env.GOOGLE_MODEL ?? "gemini-1.5-flash";

  isAvailable(): boolean {
    return Boolean(process.env.GOOGLE_API_KEY);
  }

  async *streamChat(args: ChatArgs): AsyncIterable<LLMChunk> {
    const apiKey = process.env.GOOGLE_API_KEY;
    if (!apiKey) {
      throw new LLMProviderError(this.name, "auth", "GOOGLE_API_KEY missing");
    }
    const Ctor = await loadGoogle();
    if (!Ctor) {
      throw new LLMProviderError(this.name, "unknown", "@google/generative-ai not installed");
    }
    const client = new Ctor(apiKey);
    const model = client.getGenerativeModel({ model: args.model ?? this.defaultModel });

    const contents: GeminiContent[] = args.messages.map((m) => ({
      role: m.role === "assistant" ? "model" : "user",
      parts: [{ text: m.content }],
    }));

    let res: GeminiStreamResult;
    try {
      res = await model.generateContentStream({
        contents,
        systemInstruction: { role: "system", parts: [{ text: args.system }] },
      });
    } catch (err) {
      const e = err as { status?: number; message?: string };
      throw new LLMProviderError(this.name, classify(e.status), e.message ?? String(err), e.status);
    }

    const buf = new RefStreamBuffer();
    try {
      for await (const chunk of res.stream) {
        const t = chunk.text();
        if (typeof t === "string" && t.length > 0) {
          const { text, refs } = buf.feed(t);
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
