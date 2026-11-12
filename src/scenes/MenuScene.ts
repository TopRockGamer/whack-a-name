import Phaser from 'phaser'
import { PERSON } from '../config'

export class MenuScene extends Phaser.Scene {
  constructor() {
    super('menu')
  }

  create() {
    this.add.image(640, 360, 'backdrop').setDisplaySize(1280, 720)

    const banner = this.add.image(640, 118, 'banner').setScale(0.85)
    this.add
      .text(banner.x, banner.y - 4, PERSON.bannerTitle, {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '42px',
        color: '#1a120c',
        fontStyle: 'bold',
      })
      .setOrigin(0.5)

    this.add
      .text(640, 200, 'Tap the faces before they ruin the playlist.', {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '22px',
        color: '#f5e6c8',
      })
      .setOrigin(0.5)

    const btn = this.add
      .text(640, 560, 'PLAY', {
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
