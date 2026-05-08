/**
 * Canned-answer fallback.
 *
 * Loads `data/canned-answers.json` and exposes:
 *   - `findCanned(message, persona?, vertical?)`: case-insensitive substring
 *     match — first hit wins, persona/vertical hints are preferred.
 *   - `streamCanned(entry)`: yields the entry as `LLMChunk` events so the
 *     route handler can plug it into the same SSE pipe used by live providers.
 *
 * The data file is the bulletproof fallback for the demo: even if every
 * provider is offline and the cache is cold, well-known questions still
 * stream a polished answer.
 */
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import type { CannedAnswer, ChatArgs, LLMChunk } from "./types";

let _cache: CannedAnswer[] | null = null;

function findDataRoot(): string {
  let dir = resolve(process.cwd());
  for (let i = 0; i < 8; i++) {
    if (existsSync(resolve(dir, "data", "canned-answers.json"))) {
      return resolve(dir, "data");
    }
    if (existsSync(resolve(dir, "data", "taxonomy"))) {
      return resolve(dir, "data");
    }
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return resolve(process.cwd(), "data");
}

export function loadCanned(): CannedAnswer[] {
  if (_cache) return _cache;
  const path = resolve(findDataRoot(), "canned-answers.json");
  if (!existsSync(path)) {
    _cache = [];
    return _cache;
  }
  try {
    const raw = readFileSync(path, "utf8");
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
      _cache = [];
      return _cache;
    }
    _cache = parsed.flatMap((entry) => {
      if (!entry || typeof entry !== "object") return [];
      const e = entry as Record<string, unknown>;
      const ms = e.matchSubstring;
      const r = e.response;
      if (typeof ms !== "string" || typeof r !== "string") return [];
      const cits = Array.isArray(e.citations)
        ? e.citations.filter((c): c is string => typeof c === "string")
        : [];
      const out: CannedAnswer = {
        matchSubstring: ms,
        response: r,
        citations: cits,
        ...(typeof e.persona === "string" ? { persona: e.persona } : {}),
        ...(typeof e.vertical === "string" ? { vertical: e.vertical } : {}),
      };
      return [out];
    });
    return _cache;
  } catch {
    _cache = [];
    return _cache;
  }
}

/** Reset the in-process cache. Tests use this to swap fixtures. */
export function _resetCannedCacheForTests(): void {
  _cache = null;
}

export interface CannedMatch {
  entry: CannedAnswer;
  index: number;
}

/**
 * Pick the best canned answer for the user message.
 *
 * Match preference:
 *   1. Persona-specific match (when both persona and substring align).
 *   2. Vertical-specific match.
 *   3. Plain substring match (first one wins).
 */
export function findCanned(
  message: string,
  persona?: string,
  vertical?: string,
): CannedMatch | null {
  const lower = message.toLowerCase();
  const entries = loadCanned();
  let plain: CannedMatch | null = null;
  let verticalMatch: CannedMatch | null = null;
  for (let i = 0; i < entries.length; i++) {
    const e = entries[i];
    if (!lower.includes(e.matchSubstring.toLowerCase())) continue;
    if (e.persona && persona && e.persona === persona) return { entry: e, index: i };
    if (e.vertical && vertical && e.vertical === vertical && !verticalMatch) {
      verticalMatch = { entry: e, index: i };
    }
    if (!plain && !e.persona && !e.vertical) plain = { entry: e, index: i };
  }
  return verticalMatch ?? plain;
}

/**
 * Yield a canned entry as a stream of `LLMChunk` events. Mirrors the shape
 * of a real provider so callers can `for-await` over either uniformly.
 */
export async function* streamCanned(entry: CannedAnswer): AsyncIterable<LLMChunk> {
  const step = 48;
  const text = entry.response;
  for (let i = 0; i < text.length; i += step) {
    yield { type: "content", text: text.slice(i, i + step) };
    // Tiny await so the network actually flushes. Tests use mocks that don't
    // hit the network so this is a no-op for them.
    await Promise.resolve();
  }
  for (const c of entry.citations) {
    yield { type: "citation", source: c };
  }
  yield { type: "done", provider: "canned" };
}

/** Convenience for the route handler — mirror cache.warm with chunk replay. */
export function cannedToChunks(entry: CannedAnswer): LLMChunk[] {
  const chunks: LLMChunk[] = [];
  const step = 48;
  for (let i = 0; i < entry.response.length; i += step) {
    chunks.push({ type: "content", text: entry.response.slice(i, i + step) });
  }
  for (const c of entry.citations) chunks.push({ type: "citation", source: c });
  chunks.push({ type: "done", provider: "canned" });
  return chunks;
}

/** Re-exported for convenience so the route handler can build a key. */
export type { ChatArgs };
