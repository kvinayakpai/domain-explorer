/**
 * Failover meta-provider.
 *
 * Wraps an ordered list of `LLMProvider` instances. On rate-limit / timeout /
 * 5xx from one, falls through to the next. Tracks the last-success provider
 * so subsequent calls in the same process start from the known-good one
 * (saves a redundant retry burst when the previous primary is still
 * throttled).
 *
 * Behaviour:
 *  - The first provider in the list is the "preferred" one. Every call tries
 *    providers in: [last-success, ...rest-of-list-without-it].
 *  - A provider that throws an `LLMProviderError` of kind rate_limit /
 *    timeout / server_error is skipped and we try the next one.
 *  - A provider that throws an unrelated error (auth / unknown) is also
 *    skipped — but logged differently so the caller can tell.
 *  - If every provider fails, the final error is re-raised.
 *
 * The route handler uses this together with `cache.ts` and `canned.ts` so the
 * order of attempts is: canned → cache → failover[ litellm? → primary →
 * secondary → mock ].
 */
import type { ChatArgs, LLMChunk, LLMProvider } from "./types";
import { LLMProviderError } from "./types";

const FAILOVER_KINDS: ReadonlySet<string> = new Set([
  "rate_limit",
  "timeout",
  "server_error",
  "unknown",
]);

export class FailoverProvider implements LLMProvider {
  readonly name = "failover";
  readonly defaultModel = "auto";
  private readonly providers: LLMProvider[];
  private lastSuccess: string | null = null;

  constructor(providers: LLMProvider[]) {
    this.providers = providers.filter(Boolean);
    if (this.providers.length === 0) {
      throw new Error("FailoverProvider needs at least one provider");
    }
  }

  isAvailable(): boolean {
    return this.providers.some((p) => p.isAvailable());
  }

  /** Inspect the provider order in the next call. Useful in tests. */
  order(): string[] {
    return this.routeOrder().map((p) => p.name);
  }

  /** Return the provider that handled the last successful call (if any). */
  getLastSuccess(): string | null {
    return this.lastSuccess;
  }

  private routeOrder(): LLMProvider[] {
    if (!this.lastSuccess) return this.providers;
    const head = this.providers.find((p) => p.name === this.lastSuccess);
    if (!head) return this.providers;
    const rest = this.providers.filter((p) => p.name !== this.lastSuccess);
    return [head, ...rest];
  }

  async *streamChat(args: ChatArgs): AsyncIterable<LLMChunk> {
    const errors: { provider: string; err: unknown }[] = [];
    for (const provider of this.routeOrder()) {
      if (!provider.isAvailable()) {
        errors.push({ provider: provider.name, err: new Error("not available") });
        continue;
      }
      try {
        let yielded = false;
        for await (const chunk of provider.streamChat(args)) {
          yielded = true;
          yield chunk;
        }
        if (yielded) {
          this.lastSuccess = provider.name;
          return;
        }
        // Provider yielded nothing — treat as a soft failure.
        errors.push({ provider: provider.name, err: new Error("no chunks") });
      } catch (err) {
        errors.push({ provider: provider.name, err });
        if (err instanceof LLMProviderError && !FAILOVER_KINDS.has(err.kind)) {
          // Non-recoverable kind (e.g. auth) — stop trying further providers.
          throw err;
        }
        // Otherwise try the next provider.
      }
    }
    const summary = errors.map((e) => `${e.provider}: ${(e.err as Error)?.message ?? e.err}`).join("; ");
    throw new Error(`All providers failed — ${summary}`);
  }
}
