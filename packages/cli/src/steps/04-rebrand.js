// Step 4: rebrand strings and assets.
//
// The rule of thumb: change customer-visible text, but DO NOT touch source
// imports / module ids. So:
//   - root package.json:  name + description
//   - apps/explorer-web/package.json: name only
//   - README.md: title and lead paragraph
//   - app/page.tsx: hero band Badge text
//   - app/layout.tsx: metadata.title, metadata.description, footer line
//   - .env.example: the leading comment line
// We deliberately don't search/replace the literal "Domain Explorer" anywhere
// inside the registry source files — those names are part of the product.

import path from "node:path";
import fs from "node:fs";
import fse from "fs-extra";

/** Apply a list of edits to a file. Returns 1 if file changed, 0 otherwise. */
function rewriteFile(filePath, edits) {
  if (!fs.existsSync(filePath)) return 0;
  const before = fs.readFileSync(filePath, "utf8");
  let text = before;
  for (const e of edits) {
    if (typeof e.find === "string") {
      // String replace — once.
      const idx = text.indexOf(e.find);
      if (idx >= 0) text = text.slice(0, idx) + e.replace + text.slice(idx + e.find.length);
    } else if (e.find instanceof RegExp) {
      text = text.replace(e.find, e.replace);
    }
  }
  if (text === before) return 0;
  fs.writeFileSync(filePath, text, "utf8");
  return 1;
}

/** Rewrite a JSON file by mutating an object and re-serialising. */
function rewriteJson(filePath, mutate) {
  if (!fs.existsSync(filePath)) return 0;
  let json;
  try {
    json = JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return 0;
  }
  const before = JSON.stringify(json);
  mutate(json);
  const after = JSON.stringify(json);
  if (before === after) return 0;
  fs.writeFileSync(filePath, JSON.stringify(json, null, 2) + "\n", "utf8");
  return 1;
}

export async function rebrand(ctx) {
  const { outputDir, customer, customerLabel, tagline, logo, dryRun } = ctx;
  if (dryRun) return { changedFiles: 0 };

  let changedFiles = 0;

  // 1. Root package.json — name + description.
  changedFiles += rewriteJson(path.join(outputDir, "package.json"), (j) => {
    j.name = `${customer}-domain-explorer`;
    j.description = `${customerLabel} — domain explorer accelerator (cloned from Domain Explorer).`;
  });

  // 2. apps/explorer-web/package.json — name.
  changedFiles += rewriteJson(
    path.join(outputDir, "apps", "explorer-web", "package.json"),
    (j) => {
      j.name = `${customer}-explorer-web`;
    },
  );

  // 3. README.md — title + lead.
  changedFiles += rewriteFile(path.join(outputDir, "README.md"), [
    {
      find: "# Domain Explorer\n",
      replace: `# ${customerLabel} — Domain Explorer\n\n> Customer-specific clone for **${customerLabel}**. Generated with the Customer Accelerator.\n\n`,
    },
  ]);

  // 4. app/page.tsx — hero band badge text + (optional) tagline subtitle.
  const pageTsx = path.join(outputDir, "apps", "explorer-web", "app", "page.tsx");
  const pageEdits = [
    {
      find: "<Badge>Deep Domain Explorer</Badge>",
      replace: `<Badge>${escapeJsx(customerLabel)} — Domain Explorer</Badge>`,
    },
  ];
  if (tagline) {
    // Replace the existing hero subtitle with the customer's tagline.
    pageEdits.push({
      find: /KPIs to KGs to connectors[\s\S]*?DuckDB\./,
      replace: escapeJsx(tagline),
    });
  }
  changedFiles += rewriteFile(pageTsx, pageEdits);

  // 5. app/layout.tsx — metadata.title, description, footer line.
  const layoutTsx = path.join(outputDir, "apps", "explorer-web", "app", "layout.tsx");
  changedFiles += rewriteFile(layoutTsx, [
    {
      find: 'title: "Domain Explorer"',
      replace: `title: "${customerLabel} — Domain Explorer"`,
    },
    {
      find: 'description: "Metadata-driven explorer for industry verticals, subdomains, KPIs, and integration patterns."',
      replace: `description: "${customerLabel} — metadata-driven explorer cloned from the Domain Explorer accelerator."`,
    },
    {
      find: "Domain Explorer · MIT ·",
      replace: `${customerLabel} · Domain Explorer · MIT ·`,
    },
  ]);

  // 6. .env.example — leading comment.
  changedFiles += rewriteFile(path.join(outputDir, ".env.example"), [
    {
      find: "# Domain Explorer environment variables.",
      replace: `# ${customerLabel} — Domain Explorer environment variables (cloned).`,
    },
  ]);

  // 7. Logo: copy into apps/explorer-web/public/customer-logo.<ext>.
  if (logo) {
    const ext = path.extname(logo).toLowerCase() || ".png";
    const dest = path.join(
      outputDir,
      "apps",
      "explorer-web",
      "public",
      `customer-logo${ext}`,
    );
    await fse.ensureDir(path.dirname(dest));
    await fse.copyFile(logo, dest);
    changedFiles += 1;
  }

  // 8. Drop a small `customer.json` in the repo root so other tools (or the
  // SE on a follow-up demo) can read which customer this clone is for.
  const customerMeta = {
    customer,
    customerLabel,
    vertical: ctx.vertical?.canonical,
    cloud: ctx.cloud?.slug,
    persona: ctx.persona?.id ?? null,
    tagline: tagline || null,
    generatedAt: new Date().toISOString(),
  };
  fs.writeFileSync(
    path.join(outputDir, "customer.json"),
    JSON.stringify(customerMeta, null, 2) + "\n",
    "utf8",
  );
  changedFiles += 1;

  return { changedFiles };
}

/** Make a string safe inside JSX text content (no `<`, `>`, `{`, `}`). */
function escapeJsx(s) {
  return String(s)
    .replace(/[<>{}]/g, (m) => ({ "<": "&lt;", ">": "&gt;", "{": "&#123;", "}": "&#125;" })[m]);
}
