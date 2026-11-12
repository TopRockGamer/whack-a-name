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
  face: Phaser.GameObjects.Image
  hitbox: Phaser.GameObjects.Zone
  maskGfx: Phaser.GameObjects.Graphics
  alive: boolean
  upTween?: Phaser.Tweens.Tween
}

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

    // ChatGPT: backdrop first, fixed full-bleed
    this.add.image(640, 360, 'backdrop').setDisplaySize(1280, 720).setDepth(0)

    // Banner — ChatGPT: ~(640,105), ~650px wide, clean crop
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
      // Hold every hole populated for placement screenshots
      this.timeLeft = 999
      this.timerText.setText('POSE')
      HOLES.forEach((_, i) => this.spawnMoleAt(i, true))
      // Expose live transforms for Playwright QA
      this.time.delayedCall(100, () => {
        const dump = this.moles.map((m, i) => {
          if (!m) return null
          return {
            i,
            hole: HOLES[i],
            root: { x: m.root.x, y: m.root.y, scaleY: m.root.scaleY },
            face: { w: m.face.displayWidth, h: m.face.displayHeight },
            bakedHat: true,
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
    const facePx = layout.facePx
    // Hats are baked onto face PNGs (scripts/bake_hats_on_faces.py)
    const face = this.add.image(0, 0, faceKey).setDisplaySize(facePx, facePx)

    // Clip to painted hole void (baked hat is inside the face circle)
    const maskDef = HOLE_MASK[hole.row]
    const maskW = maskDef.w * hole.scale
    const maskH = maskDef.h * hole.scale
    const maskGfx = this.make.graphics({ x: 0, y: 0 })
    maskGfx.fillStyle(0xffffff)
    maskGfx.fillEllipse(hole.x, hole.y - 4, maskW, maskH)
    face.setMask(maskGfx.createGeometryMask())

    const startY = hold ? hole.y + layout.visibleY : hole.y + layout.hiddenY
    const root = this.add.container(hole.x, startY, [face]).setDepth(12 + holeIndex)
    if (!hold) root.setScale(1, 0.25)

    const hitbox = this.add
      .zone(hole.x, hole.y - 8, 130 * hole.scale, 100 * hole.scale)
      .setDepth(30 + holeIndex)
      .setInteractive({ useHandCursor: true })

    const mole: Mole = { holeIndex, root, face, hitbox, maskGfx, alive: true }
    this.moles[holeIndex] = mole

    if (!hold) {
      const upMs = Phaser.Math.Between(MIN_UP_MS, MAX_UP_MS)
      mole.upTween = this.tweens.add({
        targets: root,
        y: hole.y + layout.visibleY,
        scaleY: 1,
        duration: 180,
        ease: 'Back.easeOut',
        onComplete: () => {
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

    this.tweens.add({
      targets: mole.root,
      scaleX: 1.12,
      scaleY: 0.55,
      duration: 90,
      yoyo: true,
    })

    if (this.textures.exists('star_burst')) {
      const star = this.add.image(mole.root.x, mole.root.y - 36, 'star_burst').setScale(0.35).setDepth(90)
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
      y: mole.root.y + 70,
      alpha: 0,
      duration: 200,
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
    this.tweens.add({
      targets: mole.root,
      y: mole.root.y + 80,
      scaleY: 0.2,
      duration: 180,
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
