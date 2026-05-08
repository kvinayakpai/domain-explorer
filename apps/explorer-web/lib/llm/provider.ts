/**
 * Provider interface re-exports plus a few small helpers shared across the
 * concrete provider implementations.
 *
 * The interface itself lives in `types.ts` — this file exists so callers (and
 * tests) can import everything they need from a single module without pulling
 * in vendor SDKs.
 */
import type { ChatArgs, LLMChunk, LLMProvider } from "./types";

export type { LLMProvider, ChatArgs, LLMChunk };

/** Wrap a synchronous list of chunks in an async iterable. */
export async function* chunksFromList(chunks: LLMChunk[]): AsyncIterable<LLMChunk> {
  for (const c of chunks) {
    yield c;
  }
}

/**
 * Parse `[REF:<id>]` markers out of a streaming text fragment.
 *
 * Returns the text with the markers removed plus the list of refs that were
 * extracted. Used by every provider that emits free-form text — the route
 * handler then forwards each citation to the client as a separate
 * `event: citation` SSE event.
 */
export function extractRefs(text: string): { text: string; refs: string[] } {
  const refs: string[] = [];
  const cleaned = text.replace(/\[REF:([^\]\s]+)\]/g, (_m, id: string) => {
    refs.push(id.trim());
    return "";
  });
  return { text: cleaned, refs };
}

/**
 * Buffer fragments of streamed text to extract `[REF:...]` markers that span
 * multiple chunks. Useful inside provider streamers that receive token-level
 * deltas — call `feed()` for each delta and `flush()` once the upstream ends.
 */
export class RefStreamBuffer {
  private pending = "";
  feed(delta: string): { text: string; refs: string[] } {
    this.pending += delta;
    // If the buffer ends with a partial `[REF:` token, hold it back until we
    // see the closing `]` in a subsequent delta.
    const partialIdx = this.pending.lastIndexOf("[");
    let safe = this.pending;
    let held = "";
    if (partialIdx !== -1 && this.pending.indexOf("]", partialIdx) === -1) {
      // We have an unclosed marker — only emit what's before the partial.
      safe = this.pending.slice(0, partialIdx);
      held = this.pending.slice(partialIdx);
    } else {
      safe = this.pending;
      held = "";
    }
    this.pending = held;
    return extractRefs(safe);
  }
  flush(): { text: string; refs: string[] } {
    const out = extractRefs(this.pending);
    this.pending = "";
    return out;
  }
}
