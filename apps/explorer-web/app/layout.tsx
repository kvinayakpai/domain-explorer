import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { NavBar } from "@/components/nav-bar";
import { registry, VERTICALS } from "@/lib/registry";
import { ANCHOR_KEYS, anchorLineages, anchorSlugs } from "@/lib/lineage-data";

export const metadata: Metadata = {
  title: "Domain Explorer",
  description: "Metadata-driven explorer for industry verticals, subdomains, KPIs, and integration patterns.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const reg = registry();
  const verticalsWithContent = new Set(reg.subdomains.map((s) => s.vertical));
  const verticals = VERTICALS.filter((v) => verticalsWithContent.has(v.slug as never)).map(
    (v) => ({ label: v.label, href: `/v/${v.slug}` }),
  );
  // Master IDs come first; we then add subdomain KPI ids that aren't in master.
  const masterIds = new Set(reg.kpiMaster.map((k) => k.id));
  const kpiPaletteSeed: { id: string; name: string }[] = [
    ...reg.kpiMaster.map((k) => ({ id: k.id, name: k.name })),
  ];
  for (const s of reg.subdomains) {
    for (const k of s.kpis) {
      if (!masterIds.has(k.id)) {
        kpiPaletteSeed.push({ id: k.id, name: k.name });
        masterIds.add(k.id);
      }
    }
  }
  const paletteItems = [
    { id: "nav-models", label: "Data models", href: "/models", group: "Models" },
    { id: "nav-kpi-library", label: "KPI library", href: "/kpi-library", group: "KPIs" },
    { id: "nav-governance", label: "Governance", href: "/governance", group: "Governance" },
    { id: "nav-catalog", label: "Catalog", href: "/catalog", group: "Governance" },
    { id: "nav-glossary", label: "Glossary", href: "/glossary", group: "Governance" },
    { id: "nav-lineage", label: "Lineage (all anchors)", href: "/lineage", group: "Governance" },
    { id: "nav-dq", label: "Data Quality", href: "/dq", group: "Governance" },
    { id: "nav-kg", label: "Knowledge Graph", href: "/kg", group: "Governance" },
    { id: "nav-demo", label: "Demo flows", href: "/demo", group: "Demo" },
    ...ANCHOR_KEYS.map((key) => ({
      id: `lineage-${key}`,
      label: `Lineage: ${anchorLineages[key].title}`,
      href: `/lineage/${anchorSlugs[key]}`,
      group: "Lineage",
    })),
    ...reg.subdomains.flatMap((s) => [
      {
        id: `sd-${s.id}`,
        label: s.name,
        href: `/d/${s.id}`,
        group: "Subdomains",
      },
      {
        id: `model-${s.id}`,
        label: `Model: ${s.name} (3NF)`,
        href: `/models/${s.id}/3nf`,
        group: "Models",
      },
    ]),
    ...kpiPaletteSeed.map((k) => ({
      id: `k-${k.id}`,
      label: k.name,
      href: `/kpi/${k.id}`,
      group: "KPIs",
    })),
    ...reg.sourceSystems.map((s) => ({
      id: `s-${s.id}`,
      label: `${s.vendor} — ${s.product}`,
      href: `/source/${s.id}`,
      group: "Source systems",
    })),
    ...reg.glossary.map((t) => ({
      id: `g-${t.name}`,
      label: t.name,
      href: `/glossary#letter-${(/[A-Z]/i.test(t.name[0] ?? "") ? t.name[0]!.toUpperCase() : "#")}`,
      group: "Glossary",
    })),
  ];
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <NavBar verticals={verticals} paletteItems={paletteItems} />
          <main className="container py-8">{children}</main>
          <footer className="container py-8 text-xs text-muted-foreground">
            <p>
              Domain Explorer · MIT · {VERTICALS.length} verticals · {reg.subdomains.length}{" "}
              subdomains seeded · {reg.glossary.length} glossary terms · {reg.kpiMaster.length}{" "}
              curated KPIs
            </p>
          </footer>
        </ThemeProvider>
      </body>
    </html>
  );
}
