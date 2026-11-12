import Phaser from 'phaser'
import {
  FACE_KEYS,
  HIT_SCORE,
  HOLE_MASK,
  HOLE_RIM,
  HOLES,
  MAX_UP_MS,
  MIN_UP_MS,
  PERSON,
  isPoseMode,
  MOLE_BODY_ASPECT,
  ROW_LAYOUT,
  ROUND_SECONDS,
  SPAWN_GAP_END_MS,
  SPAWN_GAP_START_MS,
  isPopProofMode,
  isBodyOnlyMode,
} from '../config'

type Mole = {
  holeIndex: number
  holeBucket: Phaser.GameObjects.Container
  root: Phaser.GameObjects.Container
  body: Phaser.GameObjects.Image
  face: Phaser.GameObjects.Image
  hat: Phaser.GameObjects.Image
  hitbox: Phaser.GameObjects.Zone
  maskGfx: Phaser.GameObjects.Graphics
  holeX: number
  holeY: number
  hiddenY: number
  visibleY: number
  alive: boolean
  upTween?: Phaser.Tweens.Tween
}

/**
 * Whack-a-mole character architecture:
 *   1) Dark well (depth)
 *   2) Container [plump mole body | face decal | hat] rising through geometry mask
 *   3) Wooden rim drawn ABOVE the mole so the body emerges FROM under the rim
 * Motion = squash/stretch pop of the whole character — not a face PNG slide.
 */
export class PlayScene extends Phaser.Scene {
  private score = 0
  private hits = 0
  private misses = 0
  private timeLeft = ROUND_SECONDS
  private scoreText!: Phaser.GameObjects.Text
  private timerText!: Phaser.GameObjects.Text
  private toastText!: Phaser.GameObjects.Text
  private moles: (Mole | null)[] = []
  private occupied = new Set<number>()
  private spawnEvent?: Phaser.Time.TimerEvent
  private mallet!: Phaser.GameObjects.Image
  private malletFrame = 0
  private ended = false

  constructor() {
    super('play')
  }

  create() {
    this.score = 0
    this.hits = 0
    this.misses = 0
    this.timeLeft = ROUND_SECONDS
    this.ended = false
    this.moles = HOLES.map(() => null)
    this.occupied.clear()

    this.add.image(640, 360, 'backdrop').setDisplaySize(1280, 720).setDepth(0)

    // Recessed wells: dark pit + inner walls so moles rise OUT of a hole
    HOLES.forEach((hole, i) => {
      const m = HOLE_MASK[hole.row]
      const w = m.w * hole.scale
      const h = m.h * hole.scale
      const g = this.add.graphics().setDepth(4 + i)
      // Outer lip shadow on the board
      g.fillStyle(0x000000, 0.35)
      g.fillEllipse(hole.x, hole.y + 3, w * 1.12, h * 1.08)
      // Deep black well floor
      g.fillStyle(0x050302, 1)
      g.fillEllipse(hole.x, hole.y, w * 1.0, h * 1.0)
      // Inner wall ring (slightly lighter — cylinder depth)
      g.lineStyle(Math.max(4, w * 0.06), 0x1a0e08, 0.95)
      g.strokeEllipse(hole.x, hole.y - 1, w * 0.92, h * 0.9)
      g.lineStyle(Math.max(3, w * 0.04), 0x2c1810, 0.7)
      g.strokeEllipse(hole.x, hole.y + 2, w * 0.78, h * 0.72)
      // Soft floor glow / dirt
      g.fillStyle(0x3a2418, 0.55)
      g.fillEllipse(hole.x, hole.y + h * 0.12, w * 0.48, h * 0.32)
    })

    const banner = this.add.image(640, 105, 'banner').setDepth(50)
    banner.setDisplaySize(650, Math.round(650 * (banner.height / Math.max(banner.width, 1))))
    this.add
      .text(640, 100, PERSON.bannerTitle, {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '28px',
        color: '#1a120c',
        fontStyle: 'bold',
      })
      .setOrigin(0.5)
      .setDepth(51)

    this.scoreText = this.add
      .text(40, 30, 'Score 0', {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '28px',
        color: '#f5e6c8',
        stroke: '#1a120c',
        strokeThickness: 4,
      })
      .setDepth(60)

    this.timerText = this.add
      .text(1240, 30, `${this.timeLeft}s`, {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '28px',
        color: '#f5e6c8',
        stroke: '#1a120c',
        strokeThickness: 4,
      })
      .setOrigin(1, 0)
      .setDepth(60)

    this.toastText = this.add
      .text(640, 150, '', {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '26px',
        color: '#d4a017',
        stroke: '#1a120c',
        strokeThickness: 4,
      })
      .setOrigin(0.5)
      .setDepth(70)
      .setAlpha(0)

    this.mallet = this.add
      .image(200, 200, 'mallet_0')
      .setScale(0.55)
      .setDepth(100)
      .setAlpha(0)

    // Wood board LID with punched wells — ABOVE moles, BELOW per-hole rims.
    if (this.textures.exists('board_lid')) {
      this.add.image(640, 360, 'board_lid').setDisplaySize(1280, 720).setDepth(34)
    }
    // Rims are added per-hole INSIDE the holeBucket (after the mole) so they
    // always paint over the character — global depth sorting vs containers is unreliable.

    this.time.addEvent({
      delay: 1000,
      loop: true,
      callback: () => {
        if (this.ended) return
        this.timeLeft -= 1
        this.timerText.setText(`${Math.max(0, this.timeLeft)}s`)
        if (this.timeLeft <= 0) this.endRound()
      },
    })

    if (isPoseMode() || isBodyOnlyMode()) {
      this.timeLeft = 999
      this.timerText.setText(isBodyOnlyMode() ? 'BODY' : 'POSE')
      HOLES.forEach((_, i) => this.spawnMoleAt(i, true))
      this.time.delayedCall(140, () => {
        if (isBodyOnlyMode()) {
          this.moles.forEach((m) => {
            if (!m) return
            m.face.setVisible(false)
            m.hat.setVisible(false)
          })
        }
        const dump = this.moles.map((m, i) => {
          if (!m) return null
          return {
            i,
            holeDef: HOLES[i],
            rootLocal: { x: m.root.x, y: m.root.y },
            hole: { x: m.holeX, y: m.holeY },
            body: {
              w: m.body.displayWidth,
              h: m.body.displayHeight,
              tex: m.body.texture.key,
              visible: m.body.visible,
            },
            face: { w: m.face.displayWidth, h: m.face.displayHeight, visible: m.face.visible },
            hat: { w: m.hat.displayWidth, h: m.hat.displayHeight, visible: m.hat.visible },
            architecture: 'holeBucket+mask → container[body+face+hat] + rim-above + board_lid',
          }
        })
        ;(window as unknown as { __POSE_DUMP__: unknown }).__POSE_DUMP__ = dump
        console.log('POSE_DUMP', dump)
      })
    } else if (isPopProofMode()) {
      // Front-left hole: stepped rise so proofs show body emerging from the well
      this.timeLeft = 999
      this.timerText.setText('POP')
      this.time.delayedCall(200, () => this.runPopProof(3))
    } else {
      this.scheduleSpawn(500)
    }

    this.input.on('pointermove', (p: Phaser.Input.Pointer) => {
      if (this.mallet.alpha > 0.2) this.mallet.setPosition(p.x + 40, p.y - 20)
    })
  }

  private runPopProof(holeIndex: number) {
    this.spawnMoleAt(holeIndex, true)
    const mole = this.moles[holeIndex]
    if (!mole) return
    const steps = [0, 0.22, 0.45, 0.7, 1.0]
    const frames: { t: number; y: number }[] = []
    mole.root.y = mole.hiddenY
    const advance = (i: number) => {
      if (i >= steps.length) {
        ;(window as unknown as { __POP_PROOF__: unknown }).__POP_PROOF__ = {
          frames,
          architecture: 'masked character body+face+hat rising from well',
        }
        return
      }
      const t = steps[i]
      const y = Phaser.Math.Linear(mole.hiddenY, mole.visibleY, t)
      // Soft squash early in the rise (children only — mask stays airtight)
      const squash = t < 0.35 ? 0.45 + t * 1.2 : 1
      ;[mole.body, mole.face, mole.hat].forEach((p) => {
        p.setScale(1 + (1 - squash) * 0.08, squash)
      })
      mole.root.y = y
      frames.push({ t, y })
      this.time.delayedCall(380, () => advance(i + 1))
    }
    this.time.delayedCall(120, () => advance(0))
  }

  private scheduleSpawn(delay: number) {
    this.spawnEvent?.remove(false)
    this.spawnEvent = this.time.delayedCall(delay, () => {
      if (this.ended) return
      this.spawnMole()
      const progress = 1 - this.timeLeft / ROUND_SECONDS
      const gap = Phaser.Math.Linear(SPAWN_GAP_START_MS, SPAWN_GAP_END_MS, progress)
      this.scheduleSpawn(gap)
    })
  }

  private spawnMole() {
    const free = HOLES.map((_, i) => i).filter((i) => !this.occupied.has(i))
    if (!free.length) return
    this.spawnMoleAt(Phaser.Utils.Array.GetRandom(free), false)
  }

  private spawnMoleAt(holeIndex: number, hold: boolean) {
    if (this.occupied.has(holeIndex)) return
    const hole = HOLES[holeIndex]
    const layout = ROW_LAYOUT[hole.row]
    this.occupied.add(holeIndex)

    const faceKey = FACE_KEYS[holeIndex % FACE_KEYS.length]
    const bodyH = layout.bodyH * hole.scale
    // TopRock-approved mole_body.png (512×624 plump fur + blank dome + collar)
    const bodyW = bodyH * MOLE_BODY_ASPECT
    const facePx = layout.facePx * hole.scale
    const hatW = layout.hatW * hole.scale

    const maskDef = HOLE_MASK[hole.row]
    const maskW = maskDef.w * hole.scale
    const maskH = maskDef.h * hole.scale
    // Fit width inside the well; keep enough height so collar + torso read clearly
    const fittedW = Math.min(bodyW, maskW * 0.98)
    const fittedH = fittedW / MOLE_BODY_ASPECT

    const body = this.add
      .image(0, 0, 'mole_body')
      .setOrigin(0.5, 1)
      .setDisplaySize(fittedW, fittedH)

    // Face decal ON the blank dome only (headFromTop from import metrics)
    const headY = -fittedH * (1 - layout.headFromTop)
    const face = this.add
      .image(0, headY, faceKey)
      .setOrigin(0.5, 0.5)
      .setDisplaySize(facePx, facePx)

    // Hat sits on the fur crown just above the face decal
    const hat = this.add
      .image(1, headY - facePx * 0.42, 'party_hat')
      .setOrigin(0.5, 0.95)
      .setDisplaySize(hatW, hatW * 1.15)
      .setAngle(-5)

    // Clipping = board_lid punch. Rim is a CHILD of this bucket drawn AFTER the
    // mole so the character always goes under the lip (no depth-sort fights).
    const maskGfx = this.add.graphics().setVisible(false)
    const holeBucket = this.add.container(hole.x, hole.y).setDepth(20 + holeIndex)
    const root = this.add.container(0, 0, [body, face, hat])
    const rimSize = HOLE_RIM[hole.row].size * hole.scale
    const rim = this.add.image(0, 0, 'hole_rim').setDisplaySize(rimSize, rimSize).setAlpha(0.96)
    holeBucket.add([root, rim])

    // Local Y relative to hole centre. Raise the stack so the blank dome sits in
    // the UPPER well and the plump torso/arms fill the opening (not head-only).
    const visibleY =
      -layout.headAboveHole * hole.scale + fittedH * (1 - layout.headFromTop)
    const hiddenY = fittedH * 0.95 + maskH * 0.6
    root.y = hold ? visibleY : hiddenY
    // IMPORTANT: do NOT scale holeBucket/root — geometry masks leak when scaled.
    // Squash is applied to body/face/hat children only.

    const hitbox = this.add
      .zone(hole.x, hole.y - 6, maskW * 0.95, maskH * 0.9)
      .setDepth(45 + holeIndex)
      .setInteractive({ useHandCursor: true })

    const mole: Mole = {
      holeIndex,
      holeBucket,
      root,
      body,
      face,
      hat,
      hitbox,
      maskGfx,
      holeX: hole.x,
      holeY: hole.y,
      hiddenY,
      visibleY,
      alive: true,
    }
    this.moles[holeIndex] = mole

    if (!hold) {
      const upMs = Phaser.Math.Between(MIN_UP_MS, MAX_UP_MS)
      const parts = [body, face, hat]
      parts.forEach((p) => p.setScale(1.05, 0.35))
      // Rise through the well (Y only on container — keeps mask airtight)
      mole.upTween = this.tweens.add({
        targets: root,
        y: visibleY,
        duration: 300,
        ease: 'Back.easeOut',
      })
      this.tweens.add({
        targets: parts,
        scaleX: 1,
        scaleY: 1,
        duration: 300,
        ease: 'Back.easeOut',
        onComplete: () => {
          this.tweens.add({
            targets: parts,
            scaleY: 0.94,
            scaleX: 1.04,
            duration: 80,
            yoyo: true,
            ease: 'Sine.easeInOut',
          })
          this.time.delayedCall(upMs, () => {
            if (!mole.alive) return
            this.escapeMole(mole)
          })
        },
      })
    }

    hitbox.on('pointerdown', (pointer: Phaser.Input.Pointer) => {
      if (!mole.alive || this.ended || hold) return
      this.bonkMole(mole, pointer)
    })
  }

  private bonkMole(mole: Mole, pointer: Phaser.Input.Pointer) {
    mole.alive = false
    mole.upTween?.stop()
    this.hits += 1
    this.score += HIT_SCORE
    this.scoreText.setText(`Score ${this.score}`)
    this.toast(Phaser.Utils.Array.GetRandom(PERSON.roastHit), '#2a9d8f')
    this.swingMallet(pointer.x, pointer.y)

    const parts = [mole.body, mole.face, mole.hat]
    this.tweens.add({
      targets: parts,
      scaleX: 1.15,
      scaleY: 0.45,
      duration: 80,
      yoyo: true,
    })

    if (this.textures.exists('star_burst')) {
      const star = this.add
        .image(mole.holeX, mole.holeY - mole.body.displayHeight * 0.55, 'star_burst')
        .setScale(0.35)
        .setDepth(90)
      this.tweens.add({
        targets: star,
        alpha: 0,
        scale: 0.85,
        duration: 350,
        onComplete: () => star.destroy(),
      })
    }

    this.tweens.add({
      targets: mole.root,
      y: mole.hiddenY,
      alpha: 0,
      duration: 220,
      delay: 60,
      ease: 'Back.easeIn',
      onComplete: () => this.clearMole(mole),
    })
    this.tweens.add({
      targets: parts,
      scaleY: 0.3,
      duration: 220,
      delay: 60,
      ease: 'Quad.easeIn',
    })
  }

  private escapeMole(mole: Mole) {
    mole.alive = false
    this.misses += 1
    this.toast(Phaser.Utils.Array.GetRandom(PERSON.roastMiss), '#b22222')
    this.cameras.main.shake(80, 0.004)
    const parts = [mole.body, mole.face, mole.hat]
    this.tweens.add({
      targets: mole.root,
      y: mole.hiddenY,
      duration: 260,
      ease: 'Back.easeIn',
      onComplete: () => this.clearMole(mole),
    })
    this.tweens.add({
      targets: parts,
      scaleY: 0.35,
      scaleX: 1.08,
      duration: 260,
      ease: 'Quad.easeIn',
    })
  }

  private clearMole(mole: Mole) {
    mole.hitbox.destroy()
    mole.maskGfx.destroy()
    mole.holeBucket.destroy(true)
    this.moles[mole.holeIndex] = null
    this.occupied.delete(mole.holeIndex)
  }

  private swingMallet(x: number, y: number) {
    this.malletFrame = (this.malletFrame + 1) % 3
    const key = `mallet_${this.malletFrame}` as 'mallet_0' | 'mallet_1' | 'mallet_2'
    if (this.textures.exists(key)) this.mallet.setTexture(key)
    this.mallet.setPosition(x + 50, y - 30).setAlpha(1).setAngle(-25)
    this.tweens.add({
      targets: this.mallet,
      angle: 35,
      duration: 90,
      yoyo: true,
      onComplete: () => {
        this.tweens.add({ targets: this.mallet, alpha: 0, duration: 180 })
      },
    })
  }

  private toast(msg: string, color: string) {
    this.toastText.setText(msg).setColor(color).setAlpha(1)
    this.tweens.killTweensOf(this.toastText)
    this.tweens.add({
      targets: this.toastText,
      alpha: 0,
      duration: 700,
      delay: 450,
    })
  }

  private endRound() {
    if (this.ended) return
    this.ended = true
    this.spawnEvent?.remove(false)
    this.moles.forEach((m) => {
      if (m) this.clearMole(m)
    })
    this.scene.start('end', { score: this.score, hits: this.hits, misses: this.misses })
  }
}
