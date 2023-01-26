/* index.js */

const puppeteer = require('puppeteer');

async function main(){
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('https://colaf.net');
  await page.screenshot({path: 'screenshot.png'});

  await browser.close();
}
main();