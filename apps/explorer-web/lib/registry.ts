import "server-only";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { loadRegistry, type Registry } from "@domain-explorer/metadata";

let cached: Registry | null = null;

function findDataRoot(): string {
  let dir = resolve(process.cwd());
  for (let i = 0; i < 8; i++) {
    if (existsSync(resolve(dir, "data", "taxonomy"))) {
      return resolve(dir, "data");
    }
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  throw new Error("Could not locate data/taxonomy/ from cwd: " + process.cwd());
}

export function registry(): Registry {
  if (!cached) cached = loadRegistry(findDataRoot());
  return cached;
}

export const VERTICALS = [
  { slug: "BFSI", label: "Banking & Financial Services" },
  { slug: "Insurance", label: "Insurance" },
  { slug: "Retail", label: "Retail" },
  { slug: "RCG", label: "Retail & Consumer Goods" },
  { slug: "CPG", label: "Consumer Packaged Goods" },
  { slug: "TTH", label: "Travel, Transportation & Hospitality" },
  { slug: "Manufacturing", label: "Manufacturing" },
  { slug: "LifeSciences", label: "Life Sciences" },
  { slug: "Healthcare", label: "Healthcare" },
  { slug: "Telecom", label: "Telecom" },
  { slug: "Media", label: "Media" },
  { slug: "Energy", label: "Energy" },
  { slug: "Utilities", label: "Utilities" },
  { slug: "PublicSector", label: "Public Sector" },
  { slug: "HiTech", label: "Hi-Tech" },
  { slug: "ProfessionalServices", label: "Professional Services" },
  { slug: "CrossCutting", label: "Cross-Cutting / Horizontal" },
] as const;
