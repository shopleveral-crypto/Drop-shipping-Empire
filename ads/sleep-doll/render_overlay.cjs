// Renders overlay.html frame-by-frame into transparent PNGs.
// Usage: node render_overlay.cjs <timeline.json> <hookKey> <fontDir> <outDir>
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const [timelinePath, hookKey, fontDir, outDir] = process.argv.slice(2);
  const tl = JSON.parse(fs.readFileSync(timelinePath, 'utf8'));
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: tl.width, height: tl.height }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(__dirname, 'overlay.html'));
  const font = (f) => 'file://' + path.resolve(fontDir, f);
  await page.addStyleTag({
    content: `@font-face{font-family:'Rubik';src:url('${font('Rubik.ttf')}');font-weight:300 900;}
              @font-face{font-family:'Heebo';src:url('${font('Heebo.ttf')}');font-weight:100 900;}`,
  });
  await page.evaluate(([t, k]) => window.setTimeline(t, k), [tl, hookKey]);
  await page.evaluate(async () => {
    await Promise.all([
      document.fonts.load("800 78px Rubik", "אבג"),
      document.fonts.load("900 78px Rubik", "אבג"),
      document.fonts.load("700 48px Heebo", "אבג"),
    ]);
    await document.fonts.ready;
  });

  const frames = Math.round(tl.duration * tl.fps);
  for (let i = 0; i < frames; i++) {
    await page.evaluate((t) => window.renderAt(t), i / tl.fps);
    await page.screenshot({ path: path.join(outDir, `f_${String(i).padStart(4, '0')}.png`), omitBackground: true });
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
