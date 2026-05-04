import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Breadcrumb } from "@/components/ui/breadcrumb";

export default function AssistantPage() {
  return (
    <div className="space-y-6">
      <Breadcrumb items={[{ label: "Home", href: "/" }, { label: "Assistant" }]} />
      <header className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Assistant</h1>
        <p className="max-w-2xl text-muted-foreground">
          Conversational explorer for the registry. LLM wiring is intentionally not connected yet —
          this page is a UI scaffold so the chat shell can be wired to the API in a later phase.
        </p>
      </header>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Coming soon</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-muted-foreground">
          <p>
            Ask questions like &quot;what are the top KPIs for hotel revenue management&quot; or
            &quot;which subdomains use SAP IBP&quot;. For now, use the search palette
            (<kbd className="rounded bg-muted px-1.5 py-0.5 text-xs">⌘K</kbd>) to navigate.
          </p>
          <div className="flex items-center gap-2 rounded-md border bg-muted/30 p-3">
            <input
              disabled
              placeholder="Ask the assistant…"
              className="flex-1 bg-transparent text-sm outline-none"
            />
            <button
              disabled
              className="rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground opacity-50"
            >
              Send
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
