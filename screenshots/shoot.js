const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROUTES = [
  ['index', '/'],
  ['v_bfsi', '/v/BFSI'],
  ['d_payments', '/d/payments'],
  ['governance', '/governance'],
  ['glossary', '/glossary'],
  ['catalog', '/catalog'],
  ['lineage', '/lineage'],
  ['dq', '/dq'],
  ['kg', '/kg'],
  ['assistant', '/assistant'],
  ['demo', '/demo'],
  ['demo_bfsi', '/demo/BFSI'],
];

const OUT = process.argv[2] || path.join(__dirname);
const BASE = 'http://127.0.0.1:3000';

async function shoot(profile, viewport, deviceScaleFactor) {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport, deviceScaleFactor, isMobile: profile === 'mobile' });
  const page = await ctx.newPage();
  for (const [name, route] of ROUTES) {
    const dest = path.join(OUT, profile, `${name}.png`);
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    try {
      await page.goto(BASE + route, { waitUntil: 'networkidle', timeout: 20000 });
    } catch (e) {
      console.error(`nav ${profile} ${route}:`, e.message);
    }
    await page.waitForTimeout(500);
    await page.screenshot({ path: dest, fullPage: true });
    console.log(`  ${profile}/${name}.png  (${route})`);
  }
  await browser.close();
}

(async () => {
  await shoot('desktop', { width: 1280, height: 900 }, 1);
  await shoot('mobile', { width: 390, height: 844 }, 2);
})().catch(e => { console.error(e); process.exit(1); });
