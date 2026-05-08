/**
 * LiteLLM proxy provider. Talks to a LiteLLM gateway that exposes an
 * OpenAI-compatible `/v1/chat/completions` endpoint and routes the request to
 * the appropriate vendor (Claude / GPT / Gemini / Llama / etc.) based on the
 * `model` field.
 *
 * Activated when `LITELLM_BASE_URL` is set. The route handler prepends this
 * provider to the failover chain so all traffic flows through the gateway.
 *
 * Reference: https://docs.litellm.ai/docs/proxy/quick_start
 */
import type { ChatArgs, LLMChunk, LLMProvider } from "./types";
import { LLMProviderError } from "./types";
import { RefStreamBuffer } from "./provider";

interface OpenAIStreamLine {
  choices?: { delta?: { content?: string | null }; finish_reason?: string | null }[];
}

export class LiteLLMProvider implements LLMProvider {
  readonly name = "litellm";
  readonly defaultModel = process.env.LITELLM_MODEL ?? "claude-sonnet-4-6";

  private get baseUrl(): string | undefined {
    return process.env.LITELLM_BASE_URL;
  }

  isAvailable(): boolean {
    return Boolean(this.baseUrl);
  }

  async *streamChat(args: ChatArgs): AsyncIterable<LLMChunk> {
    const baseUrl = this.baseUrl;
    if (!baseUrl) {
      throw new LLMProviderError(this.name, "auth", "LITELLM_BASE_URL missing");
    }
    const url = baseUrl.replace(/\/+$/, "") + "/v1/chat/completions";
    const headers: Record<string, string> = {
      "content-type": "application/json",
      accept: "text/event-stream",
    };
    const apiKey = process.env.LITELLM_API_KEY;
    if (apiKey) headers["authorization"] = `Bearer ${apiKey}`;

    const body = {
      model: args.model ?? this.defaultModel,
      stream: true,
      max_tokens: 1024,
      messages: [
        { role: "system" as const, content: args.system },
        ...args.messages.map((m) => ({ role: m.role, content: m.content })),
      ],
    };

    let res: Response;
    try {
      res = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
        signal: args.signal,
      });
    } catch (err) {
      const e = err as { message?: string };
      throw new LLMProviderError(
        this.name,
        e.message?.includes("aborted") ? "timeout" : "server_error",
        e.message ?? String(err),
      );
    }

    if (!res.ok || !res.body) {
      const status = res.status;
      const txt = await res.text().catch(() => "");
      throw new LLMProviderError(this.name, classify(status), `${status} ${txt.slice(0, 200)}`, status);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    const buf = new RefStreamBuffer();
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const evt = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        for (const line of evt.split("\n")) {
          if (!line.startsWith("data:")) continue;
          const data = line.slice(5).trim();
          if (!data || data === "[DONE]") continue;
          try {
            const parsed = JSON.parse(data) as OpenAIStreamLine;
            const delta = parsed.choices?.[0]?.delta?.content;
            if (typeof delta === "string" && delta.length > 0) {
              const out = buf.feed(delta);
              if (out.text) yield { type: "content", text: out.text };
              for (const r of out.refs) yield { type: "citation", source: r };
            }
          } catch {
            /* malformed line — skip */
          }
        }
      }
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
