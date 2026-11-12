import Phaser from 'phaser'
import { PERSON } from '../config'

export class EndScene extends Phaser.Scene {
  constructor() {
    super('end')
  }

  create(data: { score: number; hits: number; misses: number }) {
    this.add.image(640, 360, 'backdrop').setDisplaySize(1280, 720).setTint(0x888888)

    const panel = this.add.rectangle(640, 360, 720, 420, 0xf5e6c8, 0.96).setStrokeStyle(4, 0xb22222)
    this.add
      .text(640, 220, 'Party saved!', {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '48px',
        color: '#b22222',
        fontStyle: 'bold',
      })
      .setOrigin(0.5)

    this.add
      .text(640, 290, `Score ${data.score}`, {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '36px',
        color: '#1a120c',
      })
      .setOrigin(0.5)

    this.add
      .text(640, 340, `${data.hits} bonks · ${data.misses} escapes`, {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '22px',
        color: '#6b3f24',
      })
      .setOrigin(0.5)

    this.add
      .text(640, 410, PERSON.endMessage, {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '20px',
        color: '#1a120c',
        align: 'center',
        wordWrap: { width: 560 },
      })
      .setOrigin(0.5)

    const again = this.add
      .text(640, 510, 'PLAY AGAIN', {
        fontFamily: 'Trebuchet MS, Segoe UI, sans-serif',
        fontSize: '28px',
        color: '#f5e6c8',
        backgroundColor: '#b22222',
        padding: { x: 24, y: 10 },
      })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true })

    again.on('pointerdown', () => this.scene.start('play'))
    void panel
  }
}
