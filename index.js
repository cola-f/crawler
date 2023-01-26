/* index.js */
const puppeteer = require('puppeteer');

async function main(){
  const browser = await puppeteer.launch({
    //executablPath: 'C:\',
    defaultViewport: {
      width: 1920, 
      height: 1080
    },
    headless: false
  });
  const page = await browser.newPage();
  await page.goto('https://comic.naver.com/webtoon/detail?titleId=721433&no=197&weekday=tue');
  await page.screenshot({path: 'screenshot.png'});

  await browser.close();
}
main();
/*
await input.click();
await input.type(keyword)
await page.keyboard.press('Enter');
await page.waitForSelector('');
*/