/**
 * Public entry-point for the multi-provider LLM abstraction.
 *
 * `chat(args)` returns an async iterable of `LLMChunk` events. The resolution
 * order is:
 *
 *   1. Canned answer (if the user message matches a substring in
 *      `data/canned-answers.json`) — bulletproof demo fallback.
 *   2. Cache hit (SHA256 of system + messages + persona + model).
 *   3. Failover provider chain configured by env:
 *        - `LITELLM_BASE_URL` set    → prepend the LiteLLM proxy.
 *        - `LLM_PROVIDERS=a,b,c`     → ordered list by name. Default
 *                                      "anthropic,mock" preserves the
 *                                      pre-existing behaviour.
 *
 * The cache is checked BEFORE invoking any provider — repeat asks return in
 * sub-100ms. Successful provider responses are recorded back into the cache.
 *
 * If no providers are configured (no API keys), only the canned + mock paths
 * fire — perfect for the offline demo.
 */
import { sharedCache } from "./cache";
import { findCanned, cannedToChunks } from "./canned";
import { FailoverProvider } from "./failover";
import { AnthropicProvider } from "./provider-anthropic";
import { OpenAIProvider } from "./provider-openai";
import { GoogleProvider } from "./provider-google";
import { LiteLLMProvider } from "./provider-litellm";
import { MockProvider } from "./provider-mock";
import type { ChatArgs, LLMChunk, LLMProvider } from "./types";

export type { ChatArgs, LLMChunk, LLMProvider };
export { LLMProviderError } from "./types";
export { ResponseCache, sharedCache } from "./cache";
export { FailoverProvider } from "./failover";
export { findCanned, cannedToChunks, loadCanned } from "./canned";
export { AnthropicProvider } from "./provider-anthropic";
export { OpenAIProvider } from "./provider-openai";
export { GoogleProvider } from "./provider-google";
export { LiteLLMProvider } from "./provider-litellm";
export { MockProvider } from "./provider-mock";

const PROVIDER_REGISTRY: Record<string, () => LLMProvider> = {
  anthropic: () => new AnthropicProvider(),
  openai: () => new OpenAIProvider(),
  google: () => new GoogleProvider(),
  litellm: () => new LiteLLMProvider(),
  mock: () => new MockProvider(),
};

/** Read the `LLM_PROVIDERS` env, prepend `litellm` if `LITELLM_BASE_URL` is set. */
export function configuredProviderNames(): string[] {
  const raw = (process.env.LLM_PROVIDERS ?? "anthropic,mock")
    .split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
  if (process.env.LITELLM_BASE_URL && !raw.includes("litellm")) {
    return ["litellm", ...raw];
  }
  return raw;
}

export function buildProviderChain(): FailoverProvider {
  const names = configuredProviderNames();
  const providers: LLMProvider[] = [];
  for (const n of names) {
    const factory = PROVIDER_REGISTRY[n];
    if (factory) providers.push(factory());
  }
  if (providers.length === 0) providers.push(new MockProvider());
  return new FailoverProvider(providers);
}

/** Inputs to `chat()` plus optional persona/vertical hints used for canned matching. */
export interface ChatCallArgs extends ChatArgs {
  /** Vertical hint used to bias canned-answer selection. */
  vertical?: string;
}

/**
 * Top-level chat entry. Returns an async iterable of `LLMChunk` events.
 * The route handler in `app/api/chat/route.ts` consumes this and translates
 * each chunk into an SSE frame.
 */
export async function* chat(args: ChatCallArgs): AsyncIterable<LLMChunk> {
  const lastUser = [...args.messages].reverse().find((m) => m.role === "user")?.content ?? "";
  const cache = sharedCache();
  const startedAt = Date.now();

  // 1. Canned answer (cheapest, fastest).
  const canned = findCanned(lastUser, args.persona, args.vertical);
  if (canned) {
    const chunks = cannedToChunks(canned.entry);
    // Seed the cache so further identical asks skip canned lookup too.
    cache.set(args, chunks);
    for (const c of chunks) {
      if (c.type === "done") {
        yield { ...c, latencyMs: Date.now() - startedAt };
      } else {
        yield c;
      }
    }
    return;
  }

  // 2. Cache hit.
  const hit = cache.get(args);
  if (hit) {
    for (const c of hit) {
      if (c.type === "done") {
        yield { ...c, cached: true, latencyMs: Date.now() - startedAt };
      } else {
        yield c;
      }
    }
    return;
  }

  // 3. Failover provider chain.
  const chain = buildProviderChain();
  const recorded: LLMChunk[] = [];
  let provider: string | undefined;
  for await (const chunk of chain.streamChat(args)) {
    recorded.push(chunk);
    if (chunk.type === "done") {
      provider = chunk.provider ?? chain.getLastSuccess() ?? undefined;
      yield { ...chunk, provider, latencyMs: Date.now() - startedAt };
    } else {
      yield chunk;
    }
  }
  // Only cache responses that produced real content.
  if (recorded.some((c) => c.type === "content")) {
    cache.set(args, recorded);
  }
}
