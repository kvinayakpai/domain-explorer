import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { NavBar } from "@/components/nav-bar";
import { registry, VERTICALS } from "@/lib/registry";

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
  const paletteItems = [
    ...reg.subdomains.map((s) => ({
      id: `sd-${s.id}`,
      label: s.name,
      href: `/d/${s.id}`,
      group: "Subdomains",
    })),
    ...reg.kpis.map((k) => ({
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
  ];
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <NavBar verticals={verticals} paletteItems={paletteItems} />
          <main className="container py-8">{children}</main>
          <footer className="container py-8 text-xs text-muted-foreground">
            <p>Domain Explorer · MIT · {VERTICALS.length} verticals · {reg.subdomains.length} subdomains seeded</p>
          </footer>
        </ThemeProvider>
      </body>
    </html>
  );
}
