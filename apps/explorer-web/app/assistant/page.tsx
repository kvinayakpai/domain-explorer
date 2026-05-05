import { Breadcrumb } from "@/components/ui/breadcrumb";
import { AssistantChat } from "@/components/assistant-chat";
import { listPersonaOptions } from "@/lib/grounding";

export const dynamic = "force-dynamic";

export default function AssistantPage() {
  const personas = listPersonaOptions();
  const liveMode = Boolean(process.env.ANTHROPIC_API_KEY);
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
        {liveMode ? (
          <p className="text-xs text-muted-foreground">
            Live mode — answers come from Claude grounded on KG context.
          </p>
        ) : (
          <p className="text-xs text-muted-foreground">
            Demo mode — set <code className="rounded bg-muted px-1">ANTHROPIC_API_KEY</code> to
            enable live Claude responses. Without a key the assistant returns a deterministic
            structured answer built from the same context bundle.
          </p>
        )}
      </header>
      <AssistantChat personas={personas} />
    </div>
  );
}
