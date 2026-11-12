/**
 * Capture mole rise proofs: stepped popproof + live play strip + pose board.
 */
import { chromium } from 'playwright'
import { mkdir, copyFile, readdir } from 'node:fs/promises'
import path from 'node:path'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const { createCanvas, loadImage } = (() => {
  try {
    return require('canvas')
  } catch {
    return { createCanvas: null, loadImage: null }
  }
})()

const ROOT = 'C:/Users/user/Documents/whack-a-name'
const OUT_DIR = path.join(ROOT, '_pop_frames')
const STORE =
  'C:/Users/user/AppData/Local/Cursor/AgentStores/cursor_agent_stores/bc-f617877b-eaec-4432-8db1-768b13c985e8/files/media/whack-a-name'

await mkdir(OUT_DIR, { recursive: true })
await mkdir(STORE, { recursive: true })

const bust = Date.now()

// --- 1) Stepped popproof (clearest body-from-hole sequence) ---
{
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } })
  await page.goto(`http://127.0.0.1:5188/?popproof=1&_=${bust}`, {
    waitUntil: 'networkidle',
  })
  await page.waitForSelector('canvas')
  // Capture at each step (~380ms) — 5 steps + settle
  for (let i = 0; i < 6; i++) {
    await page.waitForTimeout(400)
    const p = path.join(OUT_DIR, `proof_${String(i).padStart(2, '0')}.png`)
    await page.screenshot({ path: p })
  }
  await page.waitForTimeout(200)
  const meta = await page.evaluate(() => window.__POP_PROOF__)
  console.log('popproof', meta)
  await browser.close()
}

// --- 2) Live play burst ---
{
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } })
  await page.goto(`http://127.0.0.1:5188/?_=${bust + 1}`, { waitUntil: 'networkidle' })
  await page.waitForSelector('canvas')
  await page.waitForTimeout(700)
  await page.mouse.click(640, 620)
  await page.waitForTimeout(350)
  for (let i = 0; i < 12; i++) {
    const p = path.join(OUT_DIR, `live_${String(i).padStart(2, '0')}.png`)
    await page.screenshot({ path: p })
    await page.waitForTimeout(140)
  }
  await browser.close()
}

// --- 3) Pose board ---
{
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } })
  await page.goto(`http://127.0.0.1:5188/?pose=1&_=${bust + 2}`, {
    waitUntil: 'networkidle',
  })
  await page.waitForSelector('canvas')
  await page.waitForTimeout(2800)
  await page.screenshot({ path: path.join(ROOT, '_shot_pose.png') })
  await page.screenshot({ path: path.join(STORE, 'play-aligned.png') })
  await page.screenshot({ path: path.join(STORE, 'after-play-aligned.png') })
  // Front hole close-up crop via full shot (proof viewers zoom)
  await page.screenshot({ path: path.join(ROOT, '_proof_front.png') })
  await page.screenshot({ path: path.join(STORE, 'after-closeup.png') })
  await browser.close()
}

// --- 4) Build pop strip from proof_ frames (Pillow via python if no canvas) ---
const proofFrames = (await readdir(OUT_DIR))
  .filter((f) => f.startsWith('proof_') && f.endsWith('.png'))
  .sort()

if (createCanvas && loadImage && proofFrames.length) {
  const imgs = []
  for (const f of proofFrames.slice(0, 5)) {
    imgs.push(await loadImage(path.join(OUT_DIR, f)))
  }
  const w = imgs[0].width
  const h = imgs[0].height
  const canvas = createCanvas(w * imgs.length, h)
  const ctx = canvas.getContext('2d')
  imgs.forEach((im, i) => ctx.drawImage(im, i * w, 0))
  const { writeFileSync } = await import('node:fs')
  writeFileSync(path.join(ROOT, '_pop_strip.png'), canvas.toBuffer('image/png'))
  writeFileSync(path.join(STORE, 'pop-strip.png'), canvas.toBuffer('image/png'))
  console.log('strip via canvas', imgs.length)
} else {
  // Python pillow strip
  const { spawnSync } = await import('node:child_process')
  const py = `
from pathlib import Path
from PIL import Image
root = Path(r"${ROOT}")
store = Path(r"${STORE}")
frames = sorted((root / "_pop_frames").glob("proof_*.png"))[:5]
imgs = [Image.open(p).convert("RGB") for p in frames]
w, h = imgs[0].size
strip = Image.new("RGB", (w * len(imgs), h))
for i, im in enumerate(imgs):
    strip.paste(im, (i * w, 0))
strip.save(root / "_pop_strip.png")
strip.save(store / "pop-strip.png")
for i, im in enumerate(imgs):
    im.save(store / f"pop-frame-{i}.png")
# body asset proof
body = Image.open(root / "public/assets/art/mole_body.png").convert("RGBA")
bg = Image.new("RGB", body.size, (28, 18, 14))
bg.paste(body, (0, 0), body)
bg.save(store / "mole-body.png")
bg.save(root / "_mole_body_preview.png")
print("strip", len(imgs), "->", store / "pop-strip.png")
`
  const r = spawnSync('python', ['-c', py], { encoding: 'utf-8' })
  console.log(r.stdout || '', r.stderr || '')
}

// Copy key live frames too
for (const name of ['proof_02.png', 'proof_03.png', 'proof_04.png']) {
  const src = path.join(OUT_DIR, name)
  try {
    await copyFile(src, path.join(STORE, name.replace('proof_', 'pop-mid-')))
  } catch {}
}

console.log('done proofs ->', STORE)
