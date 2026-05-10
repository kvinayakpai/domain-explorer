// verify-assistant.js — boot E2E sanity check of the LiteLLM-wired chat.
// v3: type the question (so React onChange fires per keystroke and the submit
// button becomes enabled), wait for button to be enabled, click; on click
// failure use form.requestSubmit() instead of bare keyboard Enter; on timeout
// capture a screenshot + forensic page state before bailing.

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PORT = process.env.SHOOT_PORT || process.env.PORT || 3030;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = path.join(__dirname, 'verify-assistant.json');
const FAIL_DIR = __dirname; // screenshots/

const QUESTIONS = [
  { vertical: 'BFSI', q: 'What KPIs does the Head of Payments care about?' },
  { vertical: 'BFSI', q: 'Walk me from STP rate down to the source-system field.' },
  { vertical: 'Insurance', q: 'How would I detect claim leakage in our data?' },
  { vertical: 'Healthcare', q: 'Which FHIR resources feed our care quality KPIs?' },
  { vertical: 'LifeSciences', q: "What's the data path from an adverse event to the regulatory submission?" },
  { vertical: 'Retail', q: 'Why is my markdown rate spiking in store cluster 3?' },
  { vertical: 'Manufacturing', q: 'Which data sources do I need to compute OEE end-to-end?' },
  { vertical: 'CrossCutting', q: "What's the difference between 3NF and Data Vault?" },
];

const CHROME_MARKERS = [
  'Try asking',
  'Pick a persona and ask anything',
  'MIT · 16 verticals',
  'Multi-provider · KG-grounded',
];

async function captureForensics(page) {
  try {
    return await page.evaluate(() => ({
      inputValue: document.querySelector('input[aria-label="Message"]')?.value ?? null,
      buttonDisabled: document.querySelector('button[type="submit"]')?.disabled ?? null,
      formExists: !!document.querySelector('form'),
      userBubbleCount: document.querySelectorAll('[data-testid="user-message"]').length,
      asstBubbleCount: document.querySelectorAll('[data-testid="assistant-message"]').length,
      lastAsstText: (() => {
        const ns = document.querySelectorAll('[data-testid="assistant-message"]');
        const last = ns[ns.length - 1];
        return last ? (last.textContent || '').slice(0, 200) : null;
      })(),
    }));
  } catch (e) {
    return { forensicError: String(e && e.message ? e.message : e) };
  }
}

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  const results = [];

  for (const item of QUESTIONS) {
    const t0 = Date.now();
    let pass = false;
    let failReason = '';
    let answer = '';
    let badge = '';
    let forensic = null;
    let screenshotPath = null;

    try {
      // Fresh page load per iteration so each conversation starts empty.
      await page.goto(`${BASE}/assistant`, { waitUntil: 'domcontentloaded', timeout: 30000 });

      const input = page.locator('input[aria-label="Message"]').first();
      await input.waitFor({ timeout: 30000 });

      const priorAssistant = await page.locator('[data-testid="assistant-message"]').count();

      // Type the question so React onChange fires per keystroke. fill() sets
      // the value via the native setter and may not synchronously update
      // React state, leaving the disabled-on-empty submit button disabled.
      await input.click(); // ensure focus
      await input.pressSequentially(item.q, { delay: 20 });

      // Wait for the submit button to actually be enabled before clicking.
      // disabled={sending || !draft.trim()}
      const submitEnabled = page.locator('button[type="submit"]:not([disabled])').first();
      try {
        await submitEnabled.waitFor({ timeout: 10000 });
      } catch (e) {
        // If still disabled, fall through to requestSubmit below.
      }

      const submit = page.locator('button[type="submit"]').first();
      let submitted = false;
      try {
        await submit.click({ timeout: 5000 });
        submitted = true;
      } catch (clickErr) {
        // Fall back to form.requestSubmit() — bypasses the disabled-button
        // gate but still triggers the form's onSubmit handler.
        try {
          await page.evaluate(() => {
            const form = document.querySelector('form');
            if (form) form.requestSubmit();
          });
          submitted = true;
        } catch (rsErr) {
          failReason = `click+requestSubmit failed: ${clickErr.message} / ${rsErr.message}`;
        }
      }

      if (submitted) {
        // Wait up to 60s for a NEW assistant bubble whose text is non-empty,
        // not "thinking…", and >= 40 chars.
        await page.waitForFunction(
          ({ prior }) => {
            const nodes = Array.from(
              document.querySelectorAll('[data-testid="assistant-message"]'),
            );
            if (nodes.length <= prior) return false;
            const last = nodes[nodes.length - 1];
            const txt = (last.textContent || '').trim();
            if (!txt) return false;
            if (txt === 'thinking…') return false;
            if (txt.length < 40) return false;
            return true;
          },
          { prior: priorAssistant },
          { timeout: 60000, polling: 250 },
        );

        const lastBubble = page.locator('[data-testid="assistant-message"]').last();
        answer = (await lastBubble.innerText()).trim();

        const lastRow = page.locator('[data-testid="assistant-message-row"]').last();
        const badgeLoc = lastRow.locator('span[aria-label^="Provider:"]').first();
        if ((await badgeLoc.count()) > 0) {
          badge = (await badgeLoc.innerText()).trim();
        }

        if (!answer) {
          failReason = 'empty assistant text';
        } else if (answer.length < 40) {
          failReason = `assistant text too short (${answer.length} chars)`;
        } else if (CHROME_MARKERS.some((m) => answer.includes(m))) {
          failReason = `assistant text contains page chrome: ${
            CHROME_MARKERS.find((m) => answer.includes(m))
          }`;
        } else {
          pass = true;
        }
      }
    } catch (err) {
      failReason = err.message;
    }

    if (!pass) {
      // Forensic capture
      forensic = await captureForensics(page);
      const safeName = item.vertical.replace(/[^A-Za-z0-9_-]/g, '_');
      screenshotPath = path.join(FAIL_DIR, `verify-fail-${safeName}.png`);
      try {
        await page.screenshot({ path: screenshotPath, fullPage: true });
      } catch {
        screenshotPath = null;
      }
    }

    const ms = Date.now() - t0;
    const result = {
      vertical: item.vertical,
      question: item.q,
      ms,
      badge,
      pass,
      answerLength: answer.length,
      answerSnippet: answer.slice(0, 200),
      ...(pass
        ? {}
        : { error: failReason, forensic, screenshot: screenshotPath }),
    };
    results.push(result);
    const tag = pass ? 'PASS' : 'FAIL';
    console.log(
      `  [${tag}] [${item.vertical}] ${item.q.slice(0, 60)}... -> ${ms}ms (badge: ${badge || 'none'}, len: ${answer.length})${
        pass ? '' : ` :: ${failReason}`
      }`,
    );
    if (!pass && forensic) {
      console.log(`         forensic: ${JSON.stringify(forensic)}`);
    }
  }

  await browser.close();

  const passCount = results.filter((r) => r.pass).length;
  const summary = {
    when: new Date().toISOString(),
    base: BASE,
    count: results.length,
    passes: passCount,
    failures: results.length - passCount,
    avgMs: Math.round(results.reduce((s, r) => s + r.ms, 0) / results.length),
    results,
  };
  fs.writeFileSync(OUT, JSON.stringify(summary, null, 2));
  console.log(`\n[verify-assistant] wrote ${OUT}`);
  console.log(`  ${summary.passes}/${summary.count} passed; avg ${summary.avgMs}ms`);
  process.exit(summary.failures === 0 ? 0 : 1);
})();
