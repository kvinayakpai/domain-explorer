"use client";
import * as React from "react";
import { Command } from "cmdk";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import * as DialogPrimitive from "@radix-ui/react-dialog";

interface Item {
  id: string;
  label: string;
  href: string;
  group: string;
}

export function CommandPalette({ items }: { items: Item[] }) {
  const [open, setOpen] = React.useState(false);
  const router = useRouter();

  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const grouped = React.useMemo(() => {
    const out: Record<string, Item[]> = {};
    for (const it of items) (out[it.group] ??= []).push(it);
    return out;
  }, [items]);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2 rounded-md border bg-background px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent"
      >
        <Search className="h-4 w-4" />
        <span className="hidden sm:inline">Search…</span>
        <kbd className="ml-2 hidden rounded bg-muted px-1.5 py-0.5 text-xs sm:inline">⌘K</kbd>
      </button>
      <DialogPrimitive.Root open={open} onOpenChange={setOpen}>
        <DialogPrimitive.Portal>
          <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm" />
          <DialogPrimitive.Content className="fixed left-1/2 top-24 z-50 w-[92vw] max-w-lg -translate-x-1/2 rounded-lg border bg-background p-2 shadow-lg">
            <Command label="Command palette" className="overflow-hidden">
              <Command.Input
                autoFocus
                placeholder="Search subdomains, KPIs, sources…"
                className="w-full rounded-md bg-transparent px-3 py-2 text-sm outline-none"
              />
              <Command.List className="max-h-[60vh] overflow-y-auto pt-2">
                <Command.Empty className="px-3 py-4 text-sm text-muted-foreground">
                  No results.
                </Command.Empty>
                {Object.entries(grouped).map(([group, list]) => (
                  <Command.Group key={group} heading={group} className="px-1 text-xs text-muted-foreground">
                    {list.map((it) => (
                      <Command.Item
                        key={it.id}
                        value={`${it.group} ${it.label}`}
                        onSelect={() => {
                          setOpen(false);
                          router.push(it.href);
                        }}
                        className="cursor-pointer rounded-md px-3 py-2 text-sm aria-selected:bg-accent"
                      >
                        {it.label}
                      </Command.Item>
                    ))}
                  </Command.Group>
                ))}
              </Command.List>
            </Command>
          </DialogPrimitive.Content>
        </DialogPrimitive.Portal>
      </DialogPrimitive.Root>
    </>
  );
}
