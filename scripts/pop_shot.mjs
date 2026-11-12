/**
 * Capture moles popping in play mode: body+face+hat rising as one unit.
 */
import { chromium } from 'playwright'
import { mkdir, copyFile } from 'node:fs/promises'
import path from 'node:path'

const ROOT = 'C:/Users/user/Documents/whack-a-name'
const OUT_DIR = path.join(ROOT, '_pop_frames')
const STORE =
  'C:/Users/user/AppData/Local/Cursor/AgentStores/cursor_agent_stores/bc-f617877b-eaec-4432-8db1-768b13c985e8/files/media/whack-a-name'

await mkdir(OUT_DIR, { recursive: true })
await mkdir(STORE, { recursive: true })

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } })
page.on('console', (msg) => {
  if (msg.type() === 'error') console.log('ERR', msg.text())
})

await page.goto(`http://127.0.0.1:5188/?_=${Date.now()}`, { waitUntil: 'networkidle' })
await page.waitForSelector('canvas')
await page.waitForTimeout(900)

// Click PLAY (Phaser canvas text — click centre-bottom where PLAY sits)
await page.mouse.click(640, 620)
await page.waitForTimeout(400)

for (let i = 0; i < 14; i++) {
  const p = path.join(OUT_DIR, `pop_${String(i).padStart(2, '0')}.png`)
  await page.screenshot({ path: p })
  await page.waitForTimeout(160)
}
await browser.close()

// Pose board
const browser2 = await chromium.launch({ headless: true })
const page2 = await browser2.newPage({ viewport: { width: 1280, height: 720 } })
await page2.goto(`http://127.0.0.1:5188/?pose=1&_=${Date.now()}`, {
  waitUntil: 'networkidle',
})
await page2.waitForSelector('canvas')
await page2.waitForTimeout(3200)
const dump = await page2.evaluate(() => window.__POSE_DUMP__)
await page2.screenshot({ path: path.join(ROOT, '_shot_pose.png') })
await page2.screenshot({ path: path.join(STORE, 'play-aligned.png') })
await page2.screenshot({ path: path.join(STORE, 'after-play-aligned.png') })
await browser2.close()

console.log('pop frames done; pose arch', dump?.[0]?.architecture)
