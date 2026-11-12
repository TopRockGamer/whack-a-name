import Phaser from 'phaser'
import { PERSON, isPoseMode, isPopProofMode, isBodyOnlyMode } from '../config'

export class MenuScene extends Phaser.Scene {
  constructor() {
    super('menu')
  }

  create() {
    if (isPoseMode() || isPopProofMode() || isBodyOnlyMode()) {
      this.scene.start('play')
      return
    }

    this.add.image(640, 360, 'backdrop').setDisplaySize(1280, 720)

    const banner = this.add.image(640, 105, 'banner')
    banner.setDisplaySize(650, Math.round(650 * (banner.height / Math.max(banner.width, 1))))
    this.add
      .text(banner.x, banner.y - 2, PERSON.bannerTitle, {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '34px',
        color: '#1a120c',
        fontStyle: 'bold',
      })
      .setOrigin(0.5)

    this.add
      .text(640, 175, 'Tap the faces before they ruin the playlist.', {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '22px',
        color: '#f5e6c8',
      })
      .setOrigin(0.5)

    const btn = this.add
      .text(640, 620, 'PLAY', {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '40px',
        color: '#1a120c',
        backgroundColor: '#d4a017',
        padding: { x: 36, y: 14 },
      })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true })

    btn.on('pointerover', () => btn.setStyle({ backgroundColor: '#f0c040' }))
    btn.on('pointerout', () => btn.setStyle({ backgroundColor: '#d4a017' }))
    btn.on('pointerdown', () => this.scene.start('play'))

    this.input.keyboard?.once('keydown-SPACE', () => this.scene.start('play'))
    this.input.keyboard?.once('keydown-ENTER', () => this.scene.start('play'))
  }
}
