// Usage: node screenshot.js <input.html> <output.png> [width] [height]
const { chromium } = require('playwright');
(async () => {
  const [,, input, output, w = '1080', h = '1350'] = process.argv;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 2 });
  await page.goto('file://' + require('path').resolve(input));
  await page.waitForTimeout(300);
  await page.screenshot({ path: output, fullPage: true });
  await browser.close();
})();
