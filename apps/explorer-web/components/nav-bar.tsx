"use client";
import * as React from "react";
import Link from "next/link";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetTrigger, SheetContent } from "@/components/ui/sheet";
import { ThemeToggle } from "@/components/theme-toggle";
import { CommandPalette } from "@/components/command-palette";

interface NavLink {
  label: string;
  href: string;
}

interface PaletteItem {
  id: string;
  label: string;
  href: string;
  group: string;
}

export function NavBar({
  verticals,
  paletteItems,
}: {
  verticals: NavLink[];
  paletteItems: PaletteItem[];
}) {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur">
      <div className="container flex h-14 items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="md:hidden" aria-label="Open menu">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent>
              <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                Verticals
              </h2>
              <nav className="flex flex-col gap-1">
                {verticals.map((v) => (
                  <Link
                    key={v.href}
                    href={v.href}
                    className="rounded-md px-2 py-1.5 text-sm hover:bg-accent"
                  >
                    {v.label}
                  </Link>
                ))}
              </nav>
              <h2 className="mb-2 mt-6 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                Governance
              </h2>
              <nav className="flex flex-col gap-1">
                <Link href="/governance" className="rounded-md px-2 py-1.5 text-sm hover:bg-accent">
                  Overview
                </Link>
                <Link href="/catalog" className="rounded-md px-2 py-1.5 text-sm hover:bg-accent">
                  Catalog
                </Link>
                <Link href="/glossary" className="rounded-md px-2 py-1.5 text-sm hover:bg-accent">
                  Glossary
                </Link>
                <Link href="/lineage" className="rounded-md px-2 py-1.5 text-sm hover:bg-accent">
                  Lineage
                </Link>
                <Link href="/dq" className="rounded-md px-2 py-1.5 text-sm hover:bg-accent">
                  Data Quality
                </Link>
                <Link href="/kg" className="rounded-md px-2 py-1.5 text-sm hover:bg-accent">
                  Knowledge Graph
                </Link>
                <Link href="/demo" className="rounded-md px-2 py-1.5 text-sm hover:bg-accent">
                  Demo flows
                </Link>
                <Link href="/assistant" className="rounded-md px-2 py-1.5 text-sm hover:bg-accent">
                  Assistant
                </Link>
              </nav>
            </SheetContent>
          </Sheet>
          <Link href="/" className="text-base font-semibold tracking-tight">
            Domain Explorer
          </Link>
        </div>
        <nav className="hidden md:flex items-center gap-1 text-sm">
          <Link href="/" className="rounded-md px-3 py-1.5 hover:bg-accent">Verticals</Link>
          <Link href="/governance" className="rounded-md px-3 py-1.5 hover:bg-accent">Governance</Link>
          <Link href="/catalog" className="rounded-md px-3 py-1.5 hover:bg-accent">Catalog</Link>
          <Link href="/glossary" className="rounded-md px-3 py-1.5 hover:bg-accent">Glossary</Link>
          <Link href="/lineage" className="rounded-md px-3 py-1.5 hover:bg-accent">Lineage</Link>
          <Link href="/dq" className="rounded-md px-3 py-1.5 hover:bg-accent">DQ</Link>
          <Link href="/kg" className="rounded-md px-3 py-1.5 hover:bg-accent">KG</Link>
          <Link href="/demo" className="rounded-md px-3 py-1.5 hover:bg-accent">Demo</Link>
          <Link href="/assistant" className="rounded-md px-3 py-1.5 hover:bg-accent">Assistant</Link>
        </nav>
        <div className="flex items-center gap-2">
          <CommandPalette items={paletteItems} />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
