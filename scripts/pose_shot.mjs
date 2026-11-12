import { chromium } from 'playwright'
import { mkdir } from 'node:fs/promises'
import path from 'node:path'

const ROOT = 'C:/Users/user/Documents/whack-a-name'
const STORE =
  'C:/Users/user/AppData/Local/Cursor/AgentStores/cursor_agent_stores/bc-f617877b-eaec-4432-8db1-768b13c985e8/files/media/whack-a-name'
const URL = 'http://localhost:5188/?pose=1'

await mkdir(STORE, { recursive: true })

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } })
page.setDefaultTimeout(20000)
await page.goto(URL, { waitUntil: 'networkidle' })
// Wait for Phaser canvas + moles
await page.waitForSelector('canvas')
await page.waitForTimeout(2500)
const out1 = path.join(ROOT, '_fix_pose.png')
const out2 = path.join(STORE, '_fix_pose.png')
const out3 = path.join(STORE, 'play-aligned.png')
const out4 = path.join(STORE, 'play.png')
await page.screenshot({ path: out1 })
await page.screenshot({ path: out2 })
await page.screenshot({ path: out3 })
await page.screenshot({ path: out4 })
const title = await page.title()
const hasPose = await page.evaluate(() => location.href)
console.log({ title, hasPose, out1 })
await browser.close()
