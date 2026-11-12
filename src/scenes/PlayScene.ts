import Phaser from 'phaser'
import {
  FACE_KEYS,
  HIT_SCORE,
  HOLE_MASK,
  HOLES,
  MAX_UP_MS,
  MIN_UP_MS,
  PERSON,
  isPoseMode,
  ROW_LAYOUT,
  ROUND_SECONDS,
  SPAWN_GAP_END_MS,
  SPAWN_GAP_START_MS,
} from '../config'

type Mole = {
  holeIndex: number
  root: Phaser.GameObjects.Container
  body: Phaser.GameObjects.Image
  face: Phaser.GameObjects.Image
  hat: Phaser.GameObjects.Image
  hitbox: Phaser.GameObjects.Zone
  maskGfx: Phaser.GameObjects.Graphics
  alive: boolean
  upTween?: Phaser.Tweens.Tween
}

/**
 * Architecture: each mole is a Phaser Container character stack
 *   [mole_body | face decal | party hat]
 * that rises as one unit through a hole geometry mask.
 * Motion = body emerging from the hole, not a face PNG sliding over a plate.
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

    // Dark hole wells behind moles — reads as coming up out of the dirt
    HOLES.forEach((hole, i) => {
      const maskDef = HOLE_MASK[hole.row]
      const g = this.add.graphics().setDepth(5 + i)
      g.fillStyle(0x1a0e08, 0.92)
      g.fillEllipse(hole.x, hole.y, maskDef.w * hole.scale * 0.98, maskDef.h * hole.scale * 0.95)
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

    if (isPoseMode()) {
      this.timeLeft = 999
      this.timerText.setText('POSE')
      HOLES.forEach((_, i) => this.spawnMoleAt(i, true))
      this.time.delayedCall(120, () => {
        const dump = this.moles.map((m, i) => {
          if (!m) return null
          return {
            i,
            hole: HOLES[i],
            root: { x: m.root.x, y: m.root.y, scaleY: m.root.scaleY },
            body: { w: m.body.displayWidth, h: m.body.displayHeight },
            face: { w: m.face.displayWidth, h: m.face.displayHeight },
            hat: { w: m.hat.displayWidth, h: m.hat.displayHeight },
            architecture: 'container[body+face+hat] + hole geometry mask',
          }
        })
        ;(window as unknown as { __POSE_DUMP__: unknown }).__POSE_DUMP__ = dump
        console.log('POSE_DUMP', dump)
      })
    } else {
      this.scheduleSpawn(500)
    }

    this.input.on('pointermove', (p: Phaser.Input.Pointer) => {
      if (this.mallet.alpha > 0.2) {
        this.mallet.setPosition(p.x + 40, p.y - 20)
      }
    })
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
    const bodyW = bodyH * (256 / 320)
    const facePx = layout.facePx * hole.scale
    const hatW = layout.hatW * hole.scale

    // --- Character stack (local coords; body origin = bottom centre) ---
    const body = this.add
      .image(0, 0, 'mole_body')
      .setOrigin(0.5, 1)
      .setDisplaySize(bodyW, bodyH)

    // Head centre on the body PNG (~y=70 of 320 from top) — face covers the sphere
    const headY = -bodyH * (1 - layout.headFromTop)
    const face = this.add
      .image(0, headY - facePx * 0.06, faceKey)
      .setOrigin(0.5, 0.5)
      .setDisplaySize(facePx, facePx)

    // Hat child of same container — brim nests into the face-crop crown
    const hat = this.add
      .image(2, headY - facePx * 0.52, 'party_hat')
      .setOrigin(0.5, 0.92)
      .setDisplaySize(hatW, hatW * 1.22)
      .setAngle(-8)

    // Hole mask clips the whole character as it rises out of the dirt
    const maskDef = HOLE_MASK[hole.row]
    const maskW = maskDef.w * hole.scale
    const maskH = maskDef.h * hole.scale
    // Second arg false = do not add mask graphics to the display list
    const maskGfx = this.make.graphics({ x: 0, y: 0 }, false)
    maskGfx.fillStyle(0xffffff)
    maskGfx.fillEllipse(hole.x, hole.y, maskW, maskH)
    const geomMask = maskGfx.createGeometryMask()

    const root = this.add.container(hole.x, 0, [body, face, hat]).setDepth(12 + holeIndex)
    root.setMask(geomMask)

    // Body origin at hole floor: hidden = sunk below mask; visible = risen into view
    const hiddenY = hole.y + layout.hideDown
    const visibleY = hole.y + layout.popUp
    root.y = hold ? visibleY : hiddenY
    if (!hold) {
      // Squash as if compressed underground, then spring up
      root.setScale(1.05, 0.35)
    }

    const hitbox = this.add
      .zone(hole.x, hole.y - 10, 140 * hole.scale, 110 * hole.scale)
      .setDepth(30 + holeIndex)
      .setInteractive({ useHandCursor: true })

    const mole: Mole = {
      holeIndex,
      root,
      body,
      face,
      hat,
      hitbox,
      maskGfx,
      alive: true,
    }
    this.moles[holeIndex] = mole

    if (!hold) {
      const upMs = Phaser.Math.Between(MIN_UP_MS, MAX_UP_MS)
      // Physical pop: whole body emerges through the hole
      mole.upTween = this.tweens.add({
        targets: root,
        y: visibleY,
        scaleX: 1,
        scaleY: 1,
        duration: 260,
        ease: 'Back.easeOut',
        onComplete: () => {
          // Tiny settle bounce — reads as weight
          this.tweens.add({
            targets: root,
            scaleY: 0.94,
            duration: 70,
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

    // Squash the whole character into the hole
    this.tweens.add({
      targets: mole.root,
      scaleX: 1.15,
      scaleY: 0.45,
      duration: 90,
      yoyo: true,
    })

    if (this.textures.exists('star_burst')) {
      const star = this.add
        .image(mole.root.x, mole.root.y - mole.body.displayHeight * 0.7, 'star_burst')
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

    const hole = HOLES[mole.holeIndex]
    const layout = ROW_LAYOUT[hole.row]
    this.tweens.add({
      targets: mole.root,
      y: hole.y + layout.hideDown,
      alpha: 0,
      duration: 220,
      delay: 70,
      ease: 'Quad.easeIn',
      onComplete: () => this.clearMole(mole),
    })
  }

  private escapeMole(mole: Mole) {
    mole.alive = false
    this.misses += 1
    this.toast(Phaser.Utils.Array.GetRandom(PERSON.roastMiss), '#b22222')
    this.cameras.main.shake(80, 0.004)
    const hole = HOLES[mole.holeIndex]
    const layout = ROW_LAYOUT[hole.row]
    this.tweens.add({
      targets: mole.root,
      y: hole.y + layout.hideDown,
      scaleY: 0.3,
      duration: 220,
      ease: 'Back.easeIn',
      onComplete: () => this.clearMole(mole),
    })
  }

  private clearMole(mole: Mole) {
    mole.hitbox.destroy()
    mole.maskGfx.destroy()
    mole.root.destroy(true)
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
