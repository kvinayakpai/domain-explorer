/**
 * In-memory LRU cache for chat completions.
 *
 * Cache key  = SHA256({ system, messages, persona, model }).
 * Cache hit  = previously-recorded `LLMChunk[]` is replayed verbatim with the
 *              `cached` flag flipped on the trailing `done` event so the UI
 *              can show a "Cached" badge.
 *
 * Goals:
 *  - Sub-100ms feel on repeated demo questions.
 *  - Bounded memory (default 200 entries, 1h TTL).
 *  - `Cache.warm()` lets the canned-answer layer pre-seed entries so even
 *    first-touch demo flows feel instant.
 */
import { createHash } from "node:crypto";
import type { ChatArgs, LLMChunk } from "./types";

interface CacheEntry {
  chunks: LLMChunk[];
  expires: number;
}

export interface CacheOptions {
  max?: number;
  ttlMs?: number;
}

export class ResponseCache {
  private readonly max: number;
  private readonly ttlMs: number;
  private readonly map = new Map<string, CacheEntry>();

  constructor(opts: CacheOptions = {}) {
    this.max = opts.max ?? 200;
    this.ttlMs = opts.ttlMs ?? 60 * 60 * 1000; // 1 hour
  }

  /** Build the deterministic cache key for an outbound request. */
  static keyFor(args: ChatArgs): string {
    const payload = JSON.stringify({
      system: args.system,
      messages: args.messages,
      persona: args.persona ?? null,
      model: args.model ?? null,
    });
    return createHash("sha256").update(payload).digest("hex");
  }

  size(): number {
    return this.map.size;
  }

  clear(): void {
    this.map.clear();
  }

  /** Look up a cached response. Returns null on miss / expiry. */
  get(args: ChatArgs): LLMChunk[] | null {
    const key = ResponseCache.keyFor(args);
    const entry = this.map.get(key);
    if (!entry) return null;
    if (entry.expires < Date.now()) {
      this.map.delete(key);
      return null;
    }
    // LRU: re-insert to mark as most recently used.
    this.map.delete(key);
    this.map.set(key, entry);
    return entry.chunks;
  }

  /** Store a full chunk list under the request's key. */
  set(args: ChatArgs, chunks: LLMChunk[]): void {
    const key = ResponseCache.keyFor(args);
    this.map.set(key, { chunks, expires: Date.now() + this.ttlMs });
    // Evict oldest entries past the cap.
    while (this.map.size > this.max) {
      const oldest = this.map.keys().next().value;
      if (typeof oldest === "string") this.map.delete(oldest);
      else break;
    }
  }

  /**
   * Pre-seed the cache with a canned answer. Used by `canned.ts` so a
   * matched substring resolves to the exact same chunk replay as a normal
   * cache hit — the UI doesn't have to special-case canned answers.
   */
  warm(args: ChatArgs, completion: string, citations: string[] = []): void {
    const chunks: LLMChunk[] = [];
    const step = 48;
    for (let i = 0; i < completion.length; i += step) {
      chunks.push({ type: "content", text: completion.slice(i, i + step) });
    }
    for (const c of citations) chunks.push({ type: "citation", source: c });
    chunks.push({ type: "done", provider: "cache", cached: true });
    this.set(args, chunks);
  }

  /**
   * Replay a cached chunk list as an async iterable. The trailing `done`
   * event is annotated with `cached: true` so callers can surface a badge.
   */
  async *replay(chunks: LLMChunk[]): AsyncIterable<LLMChunk> {
    for (const c of chunks) {
      if (c.type === "done") {
        yield { ...c, cached: true };
      } else {
        yield c;
      }
    }
  }
}

/** Module-level singleton — process-wide cache for the route handler. */
let _instance: ResponseCache | null = null;
export function sharedCache(): ResponseCache {
  if (!_instance) _instance = new ResponseCache();
  return _instance;
}
