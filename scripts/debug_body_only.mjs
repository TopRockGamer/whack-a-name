/** Pose with faces/hats hidden — prove mole_body is on screen. */
import { chromium } from 'playwright'

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } })
await page.goto(`http://127.0.0.1:5188/?pose=1&_=${Date.now()}`, {
  waitUntil: 'networkidle',
})
await page.waitForSelector('canvas')
await page.waitForTimeout(2500)
const info = await page.evaluate(() => {
  const dump = window.__POSE_DUMP__
  // Hide faces/hats via Phaser texture visibility if we can reach the scene
  const game = window.game || Object.values(window).find((v) => v?.scene?.scenes)
  const scenes = game?.scene?.scenes || []
  const play = scenes.find((s) => s?.sys?.settings?.key === 'play')
  const moles = play?.moles || []
  let hidden = 0
  for (const m of moles) {
    if (!m) continue
    if (m.face) {
      m.face.setVisible(false)
      hidden++
    }
    if (m.hat) {
      m.hat.setVisible(false)
      hidden++
    }
    if (m.body) m.body.clearTint?.()
  }
  return {
    dump: dump?.[3],
    moles: moles.length,
    hidden,
    hasBodyTex: !!play?.textures?.exists?.('mole_body'),
    bodySrc: play?.textures?.get?.('mole_body')?.key,
  }
})
console.log(JSON.stringify(info, null, 2))
await page.waitForTimeout(200)
await page.screenshot({
  path: 'C:/Users/user/Documents/whack-a-name/_debug_body_only.png',
})
await browser.close()
