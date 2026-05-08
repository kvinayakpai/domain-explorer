/**
 * Mock provider for tests and the offline demo. Always succeeds, always emits
 * a deterministic short response. Useful as the last entry in
 * `LLM_PROVIDERS` so the demo never breaks.
 */
import type { ChatArgs, LLMChunk, LLMProvider } from "./types";

export interface MockOptions {
  /**
   * If set, every call throws this error before yielding anything. Used in
   * tests to verify the failover layer routes around a broken provider.
   */
  throwError?: Error;
  /**
   * Override the default reply. Defaults to a short echo of the last user
   * message so tests can assert on the content.
   */
  reply?: (args: ChatArgs) => string;
  /** Optional citations to emit after the content. */
  citations?: string[];
  /** Override the provider name (useful when stacking multiple mocks). */
  name?: string;
}

export class MockProvider implements LLMProvider {
  readonly name: string;
  readonly defaultModel = "mock-1";
  private readonly opts: MockOptions;

  constructor(opts: MockOptions = {}) {
    this.opts = opts;
    this.name = opts.name ?? "mock";
  }

  isAvailable(): boolean {
    return true;
  }

  async *streamChat(args: ChatArgs): AsyncIterable<LLMChunk> {
    if (this.opts.throwError) throw this.opts.throwError;
    const reply =
      this.opts.reply?.(args) ??
      `Mock reply to: "${args.messages[args.messages.length - 1]?.content ?? ""}"`;
    // Chunk the reply to feel streamy without blocking on real timers.
    const step = 24;
    for (let i = 0; i < reply.length; i += step) {
      yield { type: "content", text: reply.slice(i, i + step) };
    }
    for (const c of this.opts.citations ?? []) {
      yield { type: "citation", source: c };
    }
    yield { type: "done", provider: this.name };
  }
}
