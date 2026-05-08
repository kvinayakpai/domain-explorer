// Step 2: clone the source tree.
// We deliberately avoid `cp -r` so this works the same on Windows. fs-extra's
// `copy` does the same thing and we control the ignore filter ourselves.

import path from "node:path";
import fs from "node:fs";
import fse from "fs-extra";

/**
 * Directories / file patterns we never copy. Keeps the clone fast and avoids
 * dragging huge artefacts into the customer-facing repo.
 *
 * Note: `synthetic-data/output` is per-vertical generated data — the customer
 * will regenerate it. `domain-explorer.duckdb` is large (~80MB) and rebuilt by
 * `pnpm dbt:build`. node_modules and .next are obvious.
 */
const IGNORE_DIRS = new Set([
  "node_modules",
  ".git",
  ".next",
  ".turbo",
  ".pnpm-store",
  "dist",
  "build",
  "coverage",
  ".vercel",
  ".vscode",
]);

const IGNORE_FILE_RE = [
  /\.duckdb$/i,
  /\.duckdb-wal$/i,
  /\.duckdb-shm$/i,
  /\.log$/i,
  /\.DS_Store$/i,
];

const IGNORE_PATH_FRAGMENTS = [
  // Don't copy the CLI's own outputs back into the clone — would be infinite.
  // We allow `packages/cli` itself (so the clone retains the accelerator)
  // but skip generated outputs if any.
  path.join("synthetic-data", "output") + path.sep,
];

function shouldIgnore(srcRoot, src) {
  const rel = path.relative(srcRoot, src);
  // Path components.
  const parts = rel.split(path.sep);
  for (const p of parts) {
    if (IGNORE_DIRS.has(p)) return true;
  }
  for (const re of IGNORE_FILE_RE) {
    if (re.test(path.basename(src))) return true;
  }
  for (const frag of IGNORE_PATH_FRAGMENTS) {
    if ((rel + path.sep).startsWith(frag)) return true;
  }
  return false;
}

/**
 * @param {object} ctx
 * @param {(text:string)=>void} [sub]   spinner heartbeat callback
 */
export async function clone(ctx, sub = () => {}) {
  const { sourceRepo, outputDir, dryRun } = ctx;

  if (dryRun) {
    // Even in dry-run we still walk so we can report the file count truthfully.
    const fileCount = countFiles(sourceRepo);
    return { fileCount, dryRun: true };
  }

  // If the output dir exists and isn't empty, refuse to clobber.
  if (fs.existsSync(outputDir) && fs.readdirSync(outputDir).length > 0) {
    throw new Error(
      `Output directory is not empty: ${outputDir}. Pass --output-dir to choose a fresh path.`,
    );
  }
  await fse.ensureDir(outputDir);

  let fileCount = 0;
  let lastSubAt = 0;
  await fse.copy(sourceRepo, outputDir, {
    overwrite: true,
    errorOnExist: false,
    filter: (src) => {
      if (shouldIgnore(sourceRepo, src)) return false;
      const stat = safeStatSync(src);
      if (stat?.isFile()) {
        fileCount += 1;
        // Throttle heartbeat updates.
        const now = Date.now();
        if (now - lastSubAt > 100) {
          sub(`copied ${fileCount} files…`);
          lastSubAt = now;
        }
      }
      return true;
    },
  });

  return { fileCount, dryRun: false };
}

/** Walk a tree counting files (used for --dry-run reporting). */
function countFiles(root) {
  let count = 0;
  const stack = [root];
  while (stack.length) {
    const cur = stack.pop();
    if (shouldIgnore(root, cur)) continue;
    const stat = safeStatSync(cur);
    if (!stat) continue;
    if (stat.isDirectory()) {
      let entries = [];
      try {
        entries = fs.readdirSync(cur);
      } catch {
        continue;
      }
      for (const name of entries) stack.push(path.join(cur, name));
    } else if (stat.isFile()) {
      count += 1;
    }
  }
  return count;
}

function safeStatSync(p) {
  try {
    return fs.statSync(p);
  } catch {
    return null;
  }
}
