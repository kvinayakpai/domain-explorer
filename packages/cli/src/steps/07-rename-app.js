// Step 7: rename the Next.js app's package name and HTML title.
//
// The package.json rename actually happens in step 04-rebrand (so we don't
// touch the same JSON twice). What's left here is to make sure the app's
// internal references (e.g. `pnpm --filter explorer-web`) still resolve.
// We write a small `pnpm-workspace.local.json` describing the rename so any
// scripts that grep for the original name can find the new one.

import path from "node:path";
import fs from "node:fs";

export async function renameApp(ctx) {
  const { outputDir, customer, dryRun } = ctx;
  if (dryRun) return { renamedTo: null };

  const newPkgName = `${customer}-explorer-web`;
  const newAppName = `${customer}-domain-explorer`;

  // 1. The root README quick-start instructions reference `--filter explorer-web`.
  //    We update root package.json scripts to use the renamed package.
  const rootPkgPath = path.join(outputDir, "package.json");
  if (fs.existsSync(rootPkgPath)) {
    const json = JSON.parse(fs.readFileSync(rootPkgPath, "utf8"));
    if (json.scripts) {
      for (const [k, v] of Object.entries(json.scripts)) {
        if (typeof v === "string") {
          json.scripts[k] = v.replaceAll("explorer-web", newPkgName);
        }
      }
    }
    fs.writeFileSync(rootPkgPath, JSON.stringify(json, null, 2) + "\n", "utf8");
  }

  // 2. Next.js page <title> defaults come from app/layout.tsx metadata which
  //    we already rewrote in step 04. Nothing to do here.

  // 3. Drop a tiny marker so other tooling can find the new app name without
  //    parsing package.json.
  fs.writeFileSync(
    path.join(outputDir, ".accelerator-app-name"),
    newAppName + "\n",
    "utf8",
  );

  return { renamedTo: newPkgName, appName: newAppName };
}
