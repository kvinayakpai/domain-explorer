"use client";
import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface PersonaOption {
  key: string;
  subdomainId: string;
  subdomainName: string;
  vertical: string;
  name: string;
  title: string;
  level: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  /** YAML records used to ground this assistant turn (optional). */
  recordsUsed?: string[];
  /** Mode tag: "live" (Claude API) or "demo" (canned fallback). */
  mode?: "live" | "demo";
}

const SUGGESTIONS = [
  "What KPIs does the Head of Payments care about?",
  "Which source systems feed P&C claim leakage?",
  "Walk me from RevPAR back to the operational dataset.",
];

export function AssistantChat({ personas }: { personas: PersonaOption[] }) {
  const [personaKey, setPersonaKey] = React.useState<string>(personas[0]?.key ?? "");
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [draft, setDraft] = React.useState<string>("");
  const [sending, setSending] = React.useState(false);
  const [openGrounding, setOpenGrounding] = React.useState<number | null>(null);
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
            <CardTitle className="text-sm">Try asking</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => send(s)}
                className="w-full rounded-md border px-2 py-1.5 text-left text-xs hover:bg-accent"
                disabled={sending}
              >
                {s}
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
              Claude-grounded · KG retrieval
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
