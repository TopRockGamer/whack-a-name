import { chromium } from 'playwright'
import { writeFile } from 'node:fs/promises'

const OUT = 'C:/Users/user/Documents/whack-a-name/_shot_pose.png'
const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } })
page.on('console', (msg) => console.log('BROWSER', msg.type(), msg.text()))
page.on('pageerror', (err) => console.log('PAGEERROR', err.message))

// Cache-bust the page itself
await page.goto(`http://127.0.0.1:5188/?pose=1&_=${Date.now()}`, {
  waitUntil: 'networkidle',
})
await page.waitForSelector('canvas')
await page.waitForTimeout(3500)
const dump = await page.evaluate(() => window.__POSE_DUMP__)
await writeFile(
  'C:/Users/user/Documents/whack-a-name/_pose_dump.json',
  JSON.stringify(dump, null, 2),
)
await page.screenshot({ path: OUT })
await browser.close()
console.log('wrote', OUT, 'arch', dump?.[0]?.architecture, 'keys', dump?.[0] && Object.keys(dump[0]))
