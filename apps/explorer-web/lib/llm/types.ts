/**
 * Vendor-agnostic LLM types used across `lib/llm/`.
 *
 * The public entry-point in `lib/llm/index.ts` is `chat(args)` which returns an
 * async iterable of `LLMChunk` events. Provider implementations (Anthropic /
 * OpenAI / Google / LiteLLM proxy / mock / canned) all conform to the same
 * `LLMProvider` interface so the route handler doesn't need to know which
 * vendor produced the answer.
 */

/** A single message in a chat history. */
export interface LLMMessage {
  role: "user" | "assistant";
  content: string;
}

/** Citation reference parsed out of `[REF:<id>]` tags or supplied by canned answers. */
export interface LLMCitation {
  /** A short id pointing into the registry (e.g. "pay.kpi.stp_rate"). */
  source: string;
  /** Optional human-readable label rendered in the UI footnote. */
  label?: string;
}

/** Streaming event emitted by `chat()`. */
export type LLMChunk =
  | { type: "content"; text: string }
  | { type: "citation"; source: string; label?: string }
  | { type: "done"; provider?: string; cached?: boolean; latencyMs?: number };

/** Arguments passed to `chat()` and to every provider's `streamChat()`. */
export interface ChatArgs {
  /** System prompt (already merged with grounding context by the caller). */
  system: string;
  /** Full conversation, ending with the latest user turn. */
  messages: LLMMessage[];
  /** Optional persona id used as a cache-key salt. */
  persona?: string;
  /** Abort signal — providers should pass this through to fetch / SDK calls. */
  signal?: AbortSignal;
  /** Optional per-call model override — providers ignore values they don't recognise. */
  model?: string;
}

/** Provider-level result. Implementations yield `LLMChunk` events. */
export interface LLMProvider {
  /** Stable identifier used in logs, badges, and cache keys. */
  readonly name: string;
  /** Default model id this provider routes to. */
  readonly defaultModel: string;
  /** Quick check: returns true if this provider is configured and can be tried. */
  isAvailable(): boolean;
  /** Stream chunks for the supplied chat args. Throws or yields no content on hard failure. */
  streamChat(args: ChatArgs): AsyncIterable<LLMChunk>;
}

/** Canned answer entry shape, mirrored in `data/canned-answers.json`. */
export interface CannedAnswer {
  /** Lower-case substring that triggers the canned answer when found in the user message. */
  matchSubstring: string;
  /** Optional persona id — when set, only fires when the active persona matches. */
  persona?: string;
  /** Vertical hint (used to widen matching: e.g. only fire for BFSI questions). */
  vertical?: string;
  /** Pre-baked answer text. May contain `[REF:<id>]` markers — they will be parsed out. */
  response: string;
  /** Citation ids surfaced as inline footnotes in the UI. */
  citations: string[];
}

/** Classification of a provider error so the failover layer knows whether to retry. */
export type LLMErrorKind = "rate_limit" | "timeout" | "server_error" | "auth" | "unknown";

export class LLMProviderError extends Error {
  public readonly kind: LLMErrorKind;
  public readonly provider: string;
  public readonly status?: number;
  constructor(provider: string, kind: LLMErrorKind, message: string, status?: number) {
    super(`[${provider}] ${kind}: ${message}`);
    this.provider = provider;
    this.kind = kind;
    this.status = status;
  }
}
