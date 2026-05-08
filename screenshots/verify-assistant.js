// verify-assistant.js — boot E2E sanity check of the LiteLLM-wired chat.
// Sends 8 questions across verticals, captures the response, the provider badge,
// and the round-trip time. Records to verify-assistant.json and prints a summary.

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

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  const results = [];

  for (const item of QUESTIONS) {
    const t0 = Date.now();
    try {
      await page.goto(`${BASE}/assistant`, { waitUntil: 'domcontentloaded', timeout: 30000 });
      // The assistant chat uses an <input aria-label="Message">
      const input = page.locator('input[aria-label="Message"]').first();
      await input.waitFor({ timeout: 30000 });
      await input.fill(item.q);
      const submit = page.locator('button[type="submit"]').first();
      await submit.click({ timeout: 5000 }).catch(async () => {
        await page.keyboard.press('Enter');
      });
      // Wait for any assistant message to appear (heuristic: text grows)
      await page.waitForTimeout(8000);
      const bodyText = await page.locator('body').innerText();
      const ms = Date.now() - t0;
      // Capture provider badge if any element labels it
      const badges = await page.locator('span, div').allInnerTexts();
      const badge = badges.find((t) => /Claude|GPT|Gemini|Demo Mode|Cached|Mock/i.test(t.slice(0, 40))) || '';
      results.push({
        vertical: item.vertical,
        question: item.q,
        ms,
        badge,
        responseSnippet: bodyText.slice(-600).replace(/\s+/g, ' ').trim(),
      });
      console.log(`  [${item.vertical}] ${item.q.slice(0, 60)}... -> ${ms}ms (badge: ${badge || 'none'})`);
    } catch (err) {
      const ms = Date.now() - t0;
      results.push({ vertical: item.vertical, question: item.q, ms, error: err.message });
      console.log(`  [${item.vertical}] ERROR: ${err.message}`);
    }
  }

  await browser.close();

  const summary = {
    when: new Date().toISOString(),
    base: BASE,
    count: results.length,
    failures: results.filter((r) => r.error).length,
    avgMs: Math.round(results.reduce((s, r) => s + r.ms, 0) / results.length),
    results,
  };
  fs.writeFileSync(OUT, JSON.stringify(summary, null, 2));
  console.log(`\n[verify-assistant] wrote ${OUT}`);
  console.log(`  ${summary.count - summary.failures}/${summary.count} succeeded; avg ${summary.avgMs}ms`);
})();
