import { Breadcrumb } from "@/components/ui/breadcrumb";
import { AssistantChat } from "@/components/assistant-chat";
import { listPersonaOptions } from "@/lib/grounding";

export const dynamic = "force-dynamic";

export default function AssistantPage() {
  const personas = listPersonaOptions();
  const liveProviders: string[] = [];
  if (process.env.ANTHROPIC_API_KEY) liveProviders.push("Claude");
  if (process.env.OPENAI_API_KEY) liveProviders.push("GPT");
  if (process.env.GOOGLE_API_KEY) liveProviders.push("Gemini");
  if (process.env.LITELLM_BASE_URL) liveProviders.push("LiteLLM");
  return (
    <div className="space-y-6">
      <Breadcrumb items={[{ label: "Home", href: "/" }, { label: "Assistant" }]} />
      <header className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Assistant</h1>
        <p className="max-w-2xl text-muted-foreground">
          Conversational explorer for the registry. Pick a persona and ask about their decisions,
          KPIs, or source systems — answers are grounded against the typed YAML registry and the
          openCypher templates under{" "}
          <code className="rounded bg-muted px-1 text-xs">kg/cypher/</code>.
        </p>
        {liveProviders.length > 0 ? (
          <p className="text-xs text-muted-foreground">
            Live mode — providers in failover order: {liveProviders.join(" → ")}. Repeat questions
            stream from the in-memory cache.
          </p>
        ) : (
          <p className="text-xs text-muted-foreground">
            Demo mode — set any of <code className="rounded bg-muted px-1">ANTHROPIC_API_KEY</code>,{" "}
            <code className="rounded bg-muted px-1">OPENAI_API_KEY</code>,{" "}
            <code className="rounded bg-muted px-1">GOOGLE_API_KEY</code>, or{" "}
            <code className="rounded bg-muted px-1">LITELLM_BASE_URL</code> to enable a live
            provider. Without one the assistant streams from{" "}
            <code className="rounded bg-muted px-1">data/canned-answers.json</code>.
          </p>
        )}
      </header>
      <AssistantChat personas={personas} />
    </div>
  );
}
