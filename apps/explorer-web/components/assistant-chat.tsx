"use client";
import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { suggestionsForVertical, type AssistantSuggestion } from "@/lib/assistant-suggestions";

interface PersonaOption {
  key: string;
  subdomainId: string;
  subdomainName: string;
  vertical: string;
  name: string;
  title: string;
  level: string;
}

interface CitationRef {
  source: string;
  label?: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  /** YAML records used to ground this assistant turn (optional). */
  recordsUsed?: string[];
  /** Mode tag: "live" (Claude API) or "demo" (canned fallback). */
  mode?: "live" | "demo";
  /** Inline citations parsed from `[REF:<id>]` tags or supplied by canned answers. */
  citations?: CitationRef[];
  /** The provider that produced this answer (anthropic / openai / google / canned / cache). */
  provider?: string;
  /** Whether this answer came from the response cache. */
  cached?: boolean;
  /** End-to-end latency in milliseconds (server-reported). */
  latencyMs?: number;
}

/** Map a provider name onto a friendly badge label. */
function providerLabel(p?: string, cached?: boolean): string {
  if (cached) return "Cached";
  switch (p) {
    case "anthropic":
      return "Claude";
    case "openai":
      return "GPT-4";
    case "google":
      return "Gemini";
    case "litellm":
      return "LiteLLM";
    case "canned":
      return "Demo Mode";
    case "mock":
      return "Mock";
    case "cache":
      return "Cached";
    default:
      return p ?? "";
  }
}

export function AssistantChat({ personas }: { personas: PersonaOption[] }) {
  const [personaKey, setPersonaKey] = React.useState<string>(personas[0]?.key ?? "");
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [draft, setDraft] = React.useState<string>("");
  const [sending, setSending] = React.useState(false);
  const [openGrounding, setOpenGrounding] = React.useState<number | null>(null);
  const [hoverCite, setHoverCite] = React.useState<{ msg: number; ref: number } | null>(null);
  const scrollRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const grouped = React.useMemo(() => {
    const m = new Map<string, PersonaOption[]>();
    for (const p of personas) {
      const arr = m.get(p.vertical) ?? [];
      arr.push(p);
      m.set(p.vertical, arr);
    }
    return Array.from(m.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  }, [personas]);

  const activePersona = personas.find((p) => p.key === personaKey);

  // Suggestion chips filtered by the active persona's vertical.
  // Falls back to the curated cross-vertical tour set when no persona
  // is selected (or the persona selector hasn't initialised yet).
  const suggestions = React.useMemo<AssistantSuggestion[]>(
    () => suggestionsForVertical(activePersona?.vertical, 6),
    [activePersona?.vertical],
  );

  async function send(text?: string) {
    const message = (text ?? draft).trim();
    if (!message || sending) return;
    setDraft("");
    setSending(true);
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    const userMsg: ChatMessage = { role: "user", content: message };
    const placeholder: ChatMessage = { role: "assistant", content: "" };
    setMessages((prev) => [...prev, userMsg, placeholder]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ message, personaKey, history }),
      });
      if (!res.ok || !res.body) {
        const errText = await res.text().catch(() => "request failed");
        setMessages((prev) =>
          replaceLastAssistant(prev, () => ({
            role: "assistant",
            content: `Error: ${errText}`,
            mode: "demo",
          })),
        );
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let receivedRecords: string[] | undefined;
      let mode: "live" | "demo" | undefined;
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buffer.indexOf("\n\n")) !== -1) {
          const chunk = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          const evt = parseSseEvent(chunk);
          if (!evt) continue;
          if (evt.event === "header") {
            try {
              const parsed = JSON.parse(evt.data) as {
                kind: string;
                mode: "live" | "demo";
                recordsUsed?: string[];
              };
              receivedRecords = parsed.recordsUsed;
              mode = parsed.mode;
            } catch {
              /* ignore */
            }
          } else if (evt.event === "delta") {
            try {
              const parsed = JSON.parse(evt.data) as { text: string };
              setMessages((prev) =>
                replaceLastAssistant(prev, (prior) => ({
                  ...prior,
                  content: prior.content + parsed.text,
                  recordsUsed: receivedRecords,
                  mode,
                })),
              );
            } catch {
              /* ignore */
            }
          } else if (evt.event === "citation") {
            try {
              const parsed = JSON.parse(evt.data) as { source: string; label?: string };
              if (parsed && typeof parsed.source === "string") {
                setMessages((prev) =>
                  replaceLastAssistant(prev, (prior) => {
                    const cites = prior.citations ?? [];
                    if (cites.find((c) => c.source === parsed.source)) return prior;
                    return {
                      ...prior,
                      citations: [...cites, { source: parsed.source, label: parsed.label }],
                    };
                  }),
                );
              }
            } catch {
              /* ignore */
            }
          } else if (evt.event === "done") {
            try {
              const parsed = JSON.parse(evt.data) as {
                provider?: string;
                cached?: boolean;
                latencyMs?: number;
              };
              setMessages((prev) =>
                replaceLastAssistant(prev, (prior) => ({
                  ...prior,
                  provider: parsed.provider,
                  cached: parsed.cached,
                  latencyMs: parsed.latencyMs,
                })),
              );
            } catch {
              /* ignore */
            }
          } else if (evt.event === "error") {
            try {
              const parsed = JSON.parse(evt.data) as { message?: string };
              setMessages((prev) =>
                replaceLastAssistant(prev, (prior) => ({
                  ...prior,
                  content: prior.content + `\n[error: ${parsed.message ?? "unknown"}]`,
                  recordsUsed: receivedRecords,
                  mode,
                })),
              );
            } catch {
              /* ignore */
            }
          }
        }
      }
    } catch (err) {
      const m = (err as Error)?.message ?? "send failed";
      setMessages((prev) =>
        replaceLastAssistant(prev, () => ({
          role: "assistant",
          content: `Error: ${m}`,
          mode: "demo",
        })),
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-[260px_1fr]">
      <aside className="space-y-3">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Persona</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <select
              value={personaKey}
              onChange={(e) => setPersonaKey(e.target.value)}
              className="w-full rounded-md border bg-background px-2 py-1.5 text-sm"
              aria-label="Select persona"
            >
              {grouped.map(([vertical, list]) => (
                <optgroup key={vertical} label={vertical}>
                  {list.map((p) => (
                    <option key={p.key} value={p.key}>
                      {p.name} — {p.subdomainName}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
            {activePersona ? (
              <p className="text-xs text-muted-foreground">
                {activePersona.title} · {activePersona.level}
              </p>
            ) : null}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">
              Try asking
              {activePersona ? (
                <span className="ml-1 font-normal text-muted-foreground">
                  · {activePersona.vertical}
                </span>
              ) : null}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {suggestions.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => {
                  // If the suggestion declares a persona key and that persona
                  // exists in the registry, re-select it before sending so
                  // the grounding step picks up the right vertical.
                  if (s.personaKey && personas.find((p) => p.key === s.personaKey)) {
                    setPersonaKey(s.personaKey);
                  }
                  void send(s.text);
                }}
                className="w-full rounded-md border px-2 py-1.5 text-left text-xs hover:bg-accent"
                disabled={sending}
                title={s.expectedAnswerSummary}
              >
                {s.text}
              </button>
            ))}
          </CardContent>
        </Card>
      </aside>
      <Card className="flex flex-col">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-base">
            <span>Conversation</span>
            <Badge className="bg-muted text-muted-foreground" aria-label="API mode hint">
              Multi-provider · KG-grounded
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-1 flex-col gap-3">
          <div
            ref={scrollRef}
            className="min-h-[280px] max-h-[60vh] flex-1 overflow-y-auto rounded-md border bg-muted/20 p-3 text-sm"
          >
            {messages.length === 0 ? (
              <p className="text-muted-foreground">
                Pick a persona and ask anything about their decisions, KPIs, or source systems.
              </p>
            ) : (
              <div className="space-y-3">
                {messages.map((m, i) => (
                  <div key={i} className={cn("flex flex-col gap-1", m.role === "user" ? "items-end" : "items-start")}>
                    <div
                      className={cn(
                        "max-w-[88%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm leading-relaxed shadow-sm",
                        m.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-card border",
                      )}
                    >
                      {m.content || (m.role === "assistant" && sending && i === messages.length - 1
                        ? "thinking…"
                        : "")}
                    </div>
                    {m.role === "assistant" && (m.provider || typeof m.latencyMs === "number") ? (
                      <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                        {m.provider ? (
                          <span
                            className={cn(
                              "rounded-full border px-1.5 py-0.5 font-medium",
                              m.cached
                                ? "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300"
                                : "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
                            )}
                            aria-label={`Provider: ${providerLabel(m.provider, m.cached)}`}
                          >
                            {providerLabel(m.provider, m.cached)}
                          </span>
                        ) : null}
                        {typeof m.latencyMs === "number" ? (
                          <span
                            className="rounded-full border border-border/50 bg-muted px-1.5 py-0.5 text-muted-foreground"
                            aria-label={`Latency: ${m.latencyMs} ms`}
                          >
                            {m.latencyMs} ms
                          </span>
                        ) : null}
                      </div>
                    ) : null}
                    {m.role === "assistant" && m.citations && m.citations.length > 0 ? (
                      <div className="flex flex-wrap items-center gap-1 text-[10px]">
                        <span className="text-muted-foreground">cites:</span>
                        {m.citations.map((c, ci) => (
                          <span key={ci} className="relative">
                            <button
                              type="button"
                              onMouseEnter={() => setHoverCite({ msg: i, ref: ci })}
                              onMouseLeave={() => setHoverCite(null)}
                              onFocus={() => setHoverCite({ msg: i, ref: ci })}
                              onBlur={() => setHoverCite(null)}
                              className="rounded-full border border-blue-500/40 bg-blue-500/10 px-1.5 py-0.5 font-mono text-blue-700 hover:bg-blue-500/20 dark:text-blue-300"
                              title={c.source}
                            >
                              [{ci + 1}] {c.label ?? c.source}
                            </button>
                            {hoverCite && hoverCite.msg === i && hoverCite.ref === ci ? (
                              <span className="absolute left-0 top-full z-10 mt-1 w-64 rounded-md border bg-popover p-2 text-[11px] text-popover-foreground shadow-md">
                                <span className="block font-mono text-muted-foreground">
                                  {c.source}
                                </span>
                                {c.label ? (
                                  <span className="mt-1 block">{c.label}</span>
                                ) : (
                                  <span className="mt-1 block text-muted-foreground">
                                    Registry entry — open the catalog to inspect.
                                  </span>
                                )}
                              </span>
                            ) : null}
                          </span>
                        ))}
                      </div>
                    ) : null}
                    {m.role === "assistant" && m.recordsUsed && m.recordsUsed.length > 0 ? (
                      <div className="text-xs">
                        <button
                          type="button"
                          onClick={() => setOpenGrounding(openGrounding === i ? null : i)}
                          className="text-muted-foreground underline-offset-2 hover:underline"
                        >
                          {openGrounding === i ? "Hide" : "View"} grounding
                          {m.mode ? ` (${m.mode})` : ""} · {m.recordsUsed.length} record
                          {m.recordsUsed.length === 1 ? "" : "s"}
                        </button>
                        {openGrounding === i ? (
                          <ul className="mt-1 list-disc space-y-0.5 pl-5 text-muted-foreground">
                            {m.recordsUsed.map((r) => (
                              <li key={r}>
                                <code className="rounded bg-muted px-1">{r}</code>
                              </li>
                            ))}
                          </ul>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
            className="flex items-center gap-2"
          >
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Ask the assistant…"
              className="flex-1 rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              disabled={sending}
              aria-label="Message"
            />
            <button
              type="submit"
              disabled={sending || !draft.trim()}
              className="rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground disabled:opacity-50"
            >
              {sending ? "Sending…" : "Send"}
            </button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function replaceLastAssistant(
  messages: ChatMessage[],
  fn: (prior: ChatMessage) => ChatMessage,
): ChatMessage[] {
  const idx = messages.length - 1;
  const last = idx >= 0 ? messages[idx] : undefined;
  if (!last || last.role !== "assistant") return messages;
  const next = messages.slice();
  next[idx] = fn(last);
  return next;
}

interface SseEvent {
  event: string;
  data: string;
}

function parseSseEvent(chunk: string): SseEvent | null {
  let event = "";
  const dataLines: string[] = [];
  for (const line of chunk.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
  }
  if (!event && dataLines.length === 0) return null;
  return { event, data: dataLines.join("\n") };
}
