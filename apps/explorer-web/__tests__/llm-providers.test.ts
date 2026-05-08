import { describe, it, expect, beforeEach } from "vitest";
import { FailoverProvider } from "@/lib/llm/failover";
import { MockProvider } from "@/lib/llm/provider-mock";
import { ResponseCache, sharedCache } from "@/lib/llm/cache";
import { LLMProviderError } from "@/lib/llm/types";
import { extractRefs, RefStreamBuffer } from "@/lib/llm/provider";
import { findCanned, _resetCannedCacheForTests, loadCanned } from "@/lib/llm/canned";
import { configuredProviderNames, chat } from "@/lib/llm";
import type { ChatArgs, LLMChunk } from "@/lib/llm/types";

async function collect(iter: AsyncIterable<LLMChunk>): Promise<LLMChunk[]> {
  const out: LLMChunk[] = [];
  for await (const c of iter) out.push(c);
  return out;
}

describe("FailoverProvider", () => {
  it("falls through to the next provider on rate-limit", async () => {
    const broken = new MockProvider({
      name: "broken",
      throwError: new LLMProviderError("broken", "rate_limit", "429"),
    });
    const ok = new MockProvider({ name: "ok", reply: () => "from ok" });
    const failover = new FailoverProvider([broken, ok]);
    const out = await collect(
      failover.streamChat({ system: "s", messages: [{ role: "user", content: "hi" }] }),
    );
    const text = out
      .filter((c) => c.type === "content")
      .map((c) => (c as { text: string }).text)
      .join("");
    expect(text).toBe("from ok");
    expect(failover.getLastSuccess()).toBe("ok");
  });

  it("reroutes through last-success provider on the next call", async () => {
    const a = new MockProvider({
      name: "a",
      throwError: new LLMProviderError("a", "server_error", "500"),
    });
    const b = new MockProvider({ name: "b", reply: () => "b" });
    const c = new MockProvider({ name: "c", reply: () => "c" });
    const fo = new FailoverProvider([a, b, c]);
    await collect(fo.streamChat({ system: "s", messages: [{ role: "user", content: "x" }] }));
    expect(fo.getLastSuccess()).toBe("b");
    // Next call should put `b` at the head of the order.
    expect(fo.order()[0]).toBe("b");
  });

  it("propagates auth errors instead of failing over", async () => {
    const a = new MockProvider({
      name: "a",
      throwError: new LLMProviderError("a", "auth", "no key"),
    });
    const b = new MockProvider({ name: "b", reply: () => "b" });
    const fo = new FailoverProvider([a, b]);
    await expect(
      collect(fo.streamChat({ system: "s", messages: [{ role: "user", content: "x" }] })),
    ).rejects.toThrow(/auth/);
  });
});

describe("ResponseCache", () => {
  beforeEach(() => sharedCache().clear());

  it("hits the cache on a second identical query in under 50ms", async () => {
    const cache = new ResponseCache();
    const args: ChatArgs = {
      system: "s",
      messages: [{ role: "user", content: "the same question" }],
      persona: "p1",
    };
    cache.warm(args, "cached answer", ["pay.kpi.stp_rate"]);
    const start = Date.now();
    const hit = cache.get(args);
    const elapsed = Date.now() - start;
    expect(hit).not.toBeNull();
    expect(elapsed).toBeLessThan(50);
    const replay = await collect(cache.replay(hit!));
    const text = replay
      .filter((c) => c.type === "content")
      .map((c) => (c as { text: string }).text)
      .join("");
    expect(text).toBe("cached answer");
    const done = replay.find((c) => c.type === "done") as { cached?: boolean } | undefined;
    expect(done?.cached).toBe(true);
  });

  it("uses a deterministic key based on the args payload", () => {
    const a: ChatArgs = { system: "s", messages: [{ role: "user", content: "x" }] };
    const b: ChatArgs = { system: "s", messages: [{ role: "user", content: "x" }] };
    expect(ResponseCache.keyFor(a)).toBe(ResponseCache.keyFor(b));
    const c: ChatArgs = { system: "s", messages: [{ role: "user", content: "y" }] };
    expect(ResponseCache.keyFor(a)).not.toBe(ResponseCache.keyFor(c));
  });

  it("evicts oldest entries past the cap", () => {
    const cache = new ResponseCache({ max: 2 });
    const mk = (q: string): ChatArgs => ({
      system: "s",
      messages: [{ role: "user", content: q }],
    });
    cache.warm(mk("one"), "1");
    cache.warm(mk("two"), "2");
    cache.warm(mk("three"), "3");
    expect(cache.size()).toBe(2);
    expect(cache.get(mk("one"))).toBeNull();
    expect(cache.get(mk("three"))).not.toBeNull();
  });
});

describe("Canned answers", () => {
  beforeEach(() => _resetCannedCacheForTests());

  it("returns a canned entry on a matching substring", () => {
    const m = findCanned("What KPIs does the head of payments care about?");
    expect(m).not.toBeNull();
    expect(m!.entry.citations.length).toBeGreaterThan(0);
  });

  it("loads at least 50 canned entries from the on-disk JSON", () => {
    const all = loadCanned();
    expect(all.length).toBeGreaterThanOrEqual(50);
  });

  it("returns null when no substring matches", () => {
    const m = findCanned("zzz unrelated question that nobody would ever ask");
    expect(m).toBeNull();
  });
});

describe("Citation parsing", () => {
  it("strips [REF:<id>] markers and returns the ids", () => {
    const out = extractRefs("STP rate is high [REF:pay.kpi.stp_rate] now.");
    expect(out.text).toBe("STP rate is high  now.");
    expect(out.refs).toEqual(["pay.kpi.stp_rate"]);
  });

  it("handles refs split across streamed deltas via RefStreamBuffer", () => {
    const buf = new RefStreamBuffer();
    const a = buf.feed("STP is high [REF:pa");
    expect(a.refs).toEqual([]);
    expect(a.text).toBe("STP is high ");
    const b = buf.feed("y.kpi.stp_rate] now");
    expect(b.refs).toEqual(["pay.kpi.stp_rate"]);
    expect(b.text).toBe(" now");
    const c = buf.flush();
    expect(c.text).toBe("");
  });
});

describe("Provider configuration", () => {
  it("defaults to anthropic + mock when LLM_PROVIDERS is unset", () => {
    const prev = process.env.LLM_PROVIDERS;
    delete process.env.LLM_PROVIDERS;
    delete process.env.LITELLM_BASE_URL;
    expect(configuredProviderNames()).toEqual(["anthropic", "mock"]);
    if (prev !== undefined) process.env.LLM_PROVIDERS = prev;
  });

  it("prepends litellm when LITELLM_BASE_URL is set", () => {
    const prevBase = process.env.LITELLM_BASE_URL;
    const prevList = process.env.LLM_PROVIDERS;
    process.env.LITELLM_BASE_URL = "http://localhost:4000";
    process.env.LLM_PROVIDERS = "anthropic,mock";
    expect(configuredProviderNames()).toEqual(["litellm", "anthropic", "mock"]);
    if (prevBase === undefined) delete process.env.LITELLM_BASE_URL;
    else process.env.LITELLM_BASE_URL = prevBase;
    if (prevList === undefined) delete process.env.LLM_PROVIDERS;
    else process.env.LLM_PROVIDERS = prevList;
  });
});

describe("End-to-end chat()", () => {
  beforeEach(() => {
    sharedCache().clear();
    _resetCannedCacheForTests();
  });

  it("routes a canned-matching question to the canned path with citations", async () => {
    const out = await collect(
      chat({
        system: "test",
        messages: [
          { role: "user", content: "what kpis does the head of payments care about?" },
        ],
      }),
    );
    const cites = out.filter((c) => c.type === "citation");
    const done = out.find((c) => c.type === "done") as
      | { provider?: string; cached?: boolean }
      | undefined;
    expect(cites.length).toBeGreaterThanOrEqual(3);
    expect(done?.provider).toBe("canned");
  });
});
