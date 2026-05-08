// Animated spinner wrapper around `ora`. Each step:
//   - shows a spinning bullet while running,
//   - records elapsed seconds,
//   - flips to a green check on success or a red cross on failure,
//   - if a step exceeds 5 seconds, prints sub-spinner heartbeat text so the
//     viewer never thinks the CLI hung.
//
// Steps return any object they like; `runStep` passes it through unchanged so
// callers can read step-specific results (e.g. file count).

import chalk from "chalk";

const SLOW_THRESHOLD_MS = 5_000;

/**
 * @param {object} args
 * @param {string} args.label
 * @param {boolean} [args.quiet]
 * @param {string}  [args.longRunningHint]
 * @param {(sub:(text:string)=>void)=>Promise<any>} args.fn
 */
export async function runStep({ label, quiet = false, longRunningHint, fn }) {
  // Lazy import so unit tests can run without TTY (`ora` reaches into the tty).
  const { default: ora } = await import("ora");

  const start = Date.now();
  // In quiet mode we use a no-op spinner that still tracks state. ora handles
  // non-TTY cleanly but we want to fully suppress output for --quiet.
  const spinner = quiet
    ? { start: () => spinner, succeed: () => spinner, fail: () => spinner, text: "" }
    : ora({ text: label, color: "cyan", spinner: "dots" }).start();

  // Heartbeat: every second past the threshold, update the spinner text with
  // a count so the demo audience sees motion.
  let heartbeat = null;
  if (!quiet && longRunningHint) {
    heartbeat = setInterval(() => {
      const sec = ((Date.now() - start) / 1000).toFixed(1);
      if (Date.now() - start >= SLOW_THRESHOLD_MS) {
        spinner.text = `${label}  ${chalk.dim(`(${sec}s — ${longRunningHint})`)}`;
      } else {
        spinner.text = `${label}  ${chalk.dim(`(${sec}s)`)}`;
      }
    }, 250);
  }

  try {
    const sub = (text) => {
      if (!quiet) spinner.text = `${label} — ${chalk.dim(text)}`;
    };
    const result = await fn(sub);
    const elapsedMs = Date.now() - start;
    const elapsedStr = chalk.dim(`(${(elapsedMs / 1000).toFixed(1)}s)`);
    if (!quiet) {
      spinner.succeed(`${chalk.green("✓")} ${label}  ${elapsedStr}`);
    }
    if (heartbeat) clearInterval(heartbeat);
    return { ...(result ?? {}), elapsedMs };
  } catch (err) {
    if (heartbeat) clearInterval(heartbeat);
    if (!quiet) {
      spinner.fail(`${chalk.red("✗")} ${label}  ${chalk.red(err?.message ?? String(err))}`);
    }
    throw err;
  }
}

/** Format a millisecond duration as `Ns` for the summary. */
export function formatDuration(ms) {
  const s = ms / 1000;
  if (s < 60) return `${s.toFixed(1)}s`;
  const m = Math.floor(s / 60);
  const r = (s - m * 60).toFixed(0);
  return `${m}m ${r}s`;
}
