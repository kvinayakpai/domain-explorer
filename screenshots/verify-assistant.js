// verify-assistant.js — boot E2E sanity check of the LiteLLM-wired chat.
// Sends 8 questions across verticals. Per iteration:
//   1. count existing assistant bubbles
//   2. submit the question
//   3. wait (up to 60s) for a NEW assistant bubble whose text is non-empty,
//      != "thinking…", and >= 40 chars
//   4. read ONLY the last assistant bubble's text + its provider badge
//   5. assert the text doesn't equal known page-chrome strings
// Records to verify-assistant.json and prints a summary.

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PORT = process.env.SHOOT_PORT || process.env.PORT || 3030;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = path.join(__dirname, 'verify-assistant.json');

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

// Substrings that prove we captured page chrome instead of the real answer.
const CHROME_MARKERS = [
  'Try asking',
  'Pick a persona and ask anything',
  'MIT · 16 verticals',
  'Multi-provider · KG-grounded',
];

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
    try {
      // Fresh page load per iteration so each conversation starts empty.
      await page.goto(`${BASE}/assistant`, { waitUntil: 'domcontentloaded', timeout: 30000 });

      const input = page.locator('input[aria-label="Message"]').first();
      await input.waitFor({ timeout: 30000 });

      // Count existing assistant bubbles BEFORE submitting (should be 0 on a
      // fresh load, but we measure the delta to be robust).
      const priorAssistant = await page.locator('[data-testid="assistant-message"]').count();

      await input.fill(item.q);
      const submit = page.locator('button[type="submit"]').first();
      await submit.click({ timeout: 5000 }).catch(async () => {
        await page.keyboard.press('Enter');
      });

      // Wait up to 60s for a NEW assistant bubble whose text is non-empty,
      // not "thinking…", and >= 40 chars. We poll the DOM via waitForFunction.
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

      // Read ONLY the last assistant bubble's text.
      const lastBubble = page.locator('[data-testid="assistant-message"]').last();
      answer = (await lastBubble.innerText()).trim();

      // Read the badge from inside the SAME row (not the page).
      const lastRow = page.locator('[data-testid="assistant-message-row"]').last();
      // Badge is a span with aria-label="Provider: ..." inside the row.
      const badgeLoc = lastRow.locator('span[aria-label^="Provider:"]').first();
      const badgeCount = await badgeLoc.count();
      if (badgeCount > 0) {
        badge = (await badgeLoc.innerText()).trim();
      }

      // Assertions
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
    } catch (err) {
      failReason = err.message;
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
      ...(pass ? {} : { error: failReason }),
    };
    results.push(result);
    const tag = pass ? 'PASS' : 'FAIL';
    console.log(
      `  [${tag}] [${item.vertical}] ${item.q.slice(0, 60)}... -> ${ms}ms (badge: ${badge || 'none'}, len: ${answer.length})${
        pass ? '' : ` :: ${failReason}`
      }`,
    );
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
