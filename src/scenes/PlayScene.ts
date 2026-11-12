import Phaser from 'phaser'
import {
  FACE_KEYS,
  HIT_SCORE,
  HOLES,
  MAX_UP_MS,
  MIN_UP_MS,
  PERSON,
  ROUND_SECONDS,
  SPAWN_GAP_END_MS,
  SPAWN_GAP_START_MS,
} from '../config'

type Mole = {
  holeIndex: number
  root: Phaser.GameObjects.Container
  face: Phaser.GameObjects.Image
  hat: Phaser.GameObjects.Image
  hitbox: Phaser.GameObjects.Zone
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

    this.add.image(640, 360, 'backdrop').setDisplaySize(1280, 720)

    // Idle confetti particles from sheet (or tinted dots fallback)
    if (this.textures.exists('confetti')) {
      this.add.particles(0, 0, 'confetti', {
        x: { min: 40, max: 1240 },
        y: -20,
        lifespan: 4200,
        speedY: { min: 40, max: 110 },
        speedX: { min: -20, max: 20 },
        scale: { start: 0.35, end: 0.15 },
        rotate: { min: 0, max: 360 },
        frequency: 280,
        quantity: 1,
        alpha: { start: 0.85, end: 0.1 },
      })
    }

    // Hole rims are painted into the backdrop art kit — do not overlay
    // extra frame sprites (they double-up and drift off the wood holes).

    this.add.image(640, 72, 'banner').setScale(0.72).setDepth(50)
    this.add
      .text(640, 68, PERSON.bannerTitle, {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '30px',
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

    this.scheduleSpawn(600)
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
    const holeIndex = Phaser.Utils.Array.GetRandom(free)
    const hole = HOLES[holeIndex]
    this.occupied.add(holeIndex)

    const faceKey = Phaser.Utils.Array.GetRandom([...FACE_KEYS])
    const face = this.add.image(0, 0, faceKey).setDisplaySize(110 * hole.scale, 110 * hole.scale)
    const hat = this.add
      .image(8, -58 * hole.scale, 'hat')
      .setScale(0.42 * hole.scale)
      .setAngle(Phaser.Math.Between(-12, 12))

    const root = this.add.container(hole.x, hole.y + 70, [face, hat]).setDepth(12 + holeIndex)
    // Circular mask so the face reads as rising out of the painted hole
    const maskShape = this.make.graphics({ x: 0, y: 0 })
    maskShape.fillStyle(0xffffff)
    // Tall oval so the party hat clears once fully popped
    maskShape.fillEllipse(hole.x, hole.y - 28, 120 * hole.scale, 150 * hole.scale)
    root.setMask(maskShape.createGeometryMask())

    root.setScale(1, 0.2)
    root.y = hole.y + 40

    const hitbox = this.add
      .zone(hole.x, hole.y - 10, 120 * hole.scale, 120 * hole.scale)
      .setDepth(30 + holeIndex)
      .setInteractive({ useHandCursor: true })

    const mole: Mole = { holeIndex, root, face, hat, hitbox, alive: true }
    this.moles[holeIndex] = mole

    const upMs = Phaser.Math.Between(MIN_UP_MS, MAX_UP_MS)
    mole.upTween = this.tweens.add({
      targets: root,
      y: hole.y - 18,
      scaleY: 1,
      duration: 280,
      ease: 'Back.easeOut',
      onComplete: () => {
        this.time.delayedCall(upMs, () => {
          if (!mole.alive) return
          this.escapeMole(mole)
        })
      },
    })

    hitbox.on('pointerdown', (pointer: Phaser.Input.Pointer) => {
      if (!mole.alive || this.ended) return
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
      scaleX: 1.15,
      scaleY: 0.55,
      duration: 90,
      yoyo: true,
    })

    if (this.textures.exists('star_burst')) {
      const star = this.add.image(mole.root.x, mole.root.y - 40, 'star_burst').setScale(0.4).setDepth(90)
      this.tweens.add({
        targets: star,
        alpha: 0,
        scale: 0.9,
        duration: 350,
        onComplete: () => star.destroy(),
      })
    }

    this.tweens.add({
      targets: mole.root,
      y: mole.root.y + 80,
      alpha: 0,
      duration: 220,
      delay: 80,
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
      y: mole.root.y + 90,
      scaleY: 0.2,
      duration: 200,
      ease: 'Back.easeIn',
      onComplete: () => this.clearMole(mole),
    })
  }

  private clearMole(mole: Mole) {
    mole.hitbox.destroy()
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
