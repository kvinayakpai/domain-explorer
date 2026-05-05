import { registry } from "@/lib/registry";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { GlossaryList } from "@/components/glossary-list";

export const dynamic = "force-static";

export const metadata = {
  title: "Glossary · Domain Explorer",
  description: "A-Z glossary of business, KPI, and regulatory terms cross-linked to subdomains.",
};

export default function GlossaryPage() {
  const reg = registry();
  return (
    <div className="space-y-6">
      <Breadcrumb
        items={[
          { label: "Verticals", href: "/" },
          { label: "Governance", href: "/governance" },
          { label: "Glossary" },
        ]}
      />
      <header className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Glossary</h1>
        <p className="max-w-3xl text-muted-foreground">
          Canonical definitions for the business, KPI, and regulatory vocabulary used across
          the registry. Each term links to the subdomains and KPIs where it shows up most.
        </p>
      </header>
      <GlossaryList items={reg.glossary} />
    </div>
  );
}
