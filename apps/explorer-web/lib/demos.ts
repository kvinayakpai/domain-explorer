/**
 * Working demos that run on the same simulated data as a subdomain, read from
 * data/demos.json (the static viewer reads the same file).
 *
 * Factory to Field (factory_to_field/ in this repo) is an end-to-end build for oil and gas:
 * an ontology, a knowledge graph over simulated refinery, oil-field and pump-maker systems,
 * and agents that investigate alarms with every number cited. Its landing page, walkthrough
 * video and case viewer are served by GitHub Pages from factory-to-field/.
 */
import raw from "../../../data/demos.json";

export interface SubdomainDemo {
  title: string;
  url: string;
  blurb: string;
}

export const SUBDOMAIN_DEMOS: Record<string, SubdomainDemo> = Object.fromEntries(
  Object.entries(raw as Record<string, unknown>).filter(
    (entry): entry is [string, SubdomainDemo] => !entry[0].startsWith("_") && typeof entry[1] === "object",
  ),
);

export function demoFor(subdomainId: string): SubdomainDemo | undefined {
  return SUBDOMAIN_DEMOS[subdomainId];
}
