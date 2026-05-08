// Step 8: initialise a fresh git repo in the clone.
//
// We try `git` directly via child_process. If git isn't on PATH we fall back
// gracefully — the clone is still usable, just without the initial commit.

import { spawn } from "node:child_process";
import path from "node:path";

function run(cmd, args, cwd) {
  return new Promise((resolve) => {
    const p = spawn(cmd, args, { cwd, stdio: "ignore", shell: process.platform === "win32" });
    p.on("error", () => resolve({ ok: false, code: null }));
    p.on("close", (code) => resolve({ ok: code === 0, code }));
  });
}

export async function initGit(ctx) {
  if (ctx.skipGit || ctx.dryRun) {
    return { ok: false, reason: "skipped" };
  }
  const cwd = ctx.outputDir;

  // git init -b main — older gits don't support -b. Fall through to plain init
  // followed by `git symbolic-ref HEAD refs/heads/main`.
  let r = await run("git", ["init", "-b", "main"], cwd);
  if (!r.ok) {
    r = await run("git", ["init"], cwd);
    if (!r.ok) return { ok: false, reason: "git-not-available" };
    await run("git", ["symbolic-ref", "HEAD", "refs/heads/main"], cwd);
  }

  // The clone might not include a .gitignore tailored for the customer; the
  // source's .gitignore is copied as-is which is fine.
  await run("git", ["add", "-A"], cwd);

  // Configure user.name/email locally so the commit doesn't fail on machines
  // without a global git identity. We don't override an existing config.
  await run("git", ["config", "user.name", "Domain Explorer Accelerator"], cwd);
  await run("git", ["config", "user.email", "accelerator@domain-explorer.local"], cwd);

  const message = `chore: bootstrap from Domain Explorer accelerator for ${ctx.customer}`;
  const commit = await run("git", ["commit", "-m", message, "--no-verify"], cwd);
  if (!commit.ok) {
    return { ok: false, reason: "commit-failed" };
  }
  return { ok: true, branch: "main", message };
}
