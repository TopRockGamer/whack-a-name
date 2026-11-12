import { chromium } from 'playwright'
import { writeFile } from 'node:fs/promises'

const URL = 'http://localhost:5188/?pose=1'
const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } })
await page.goto(URL, { waitUntil: 'networkidle' })
await page.waitForSelector('canvas')
await page.waitForTimeout(2000)
const dump = await page.evaluate(() => window.__POSE_DUMP__)
console.log(JSON.stringify(dump, null, 2))
await writeFile('C:/Users/user/Documents/whack-a-name/_pose_dump.json', JSON.stringify(dump, null, 2))
await page.screenshot({ path: 'C:/Users/user/Documents/whack-a-name/_fix_pose.png' })
await browser.close()
