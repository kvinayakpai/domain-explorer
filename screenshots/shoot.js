const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROUTES = [
  ['index', '/'],
  ['v_bfsi', '/v/BFSI'],
  ['d_payments', '/d/payments'],
  ['d_mes_quality', '/d/mes_quality'],
  ['kpi_pay_stp_rate', '/kpi/pay.kpi.stp_rate'],
  ['source_stripe', '/source/src.stripe_payments'],
  ['assistant', '/assistant'],
];

const OUT = process.argv[2] || '/sessions/clever-affectionate-tesla/mnt/domain-explorer/screenshots';
const BASE = 'http://127.0.0.1:3000';

async function shoot(profile, viewport, deviceScaleFactor) {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport, deviceScaleFactor, isMobile: profile === 'mobile' });
  const page = await ctx.newPage();
  for (const [name, route] of ROUTES) {
    const dest = path.join(OUT, profile, `${name}.png`);
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    try {
      await page.goto(BASE + route, { waitUntil: 'networkidle', timeout: 15000 });
    } catch (e) {
      console.error(`nav ${profile} ${route}:`, e.message);
    }
    await page.waitForTimeout(400);
    await page.screenshot({ path: dest, fullPage: true });
    console.log(`  ${profile}/${name}.png  (${route})`);
  }
  await browser.close();
}

(async () => {
  await shoot('desktop', { width: 1280, height: 900 }, 1);
  await shoot('mobile', { width: 390, height: 844 }, 2);
})().catch(e => { console.error(e); process.exit(1); });
