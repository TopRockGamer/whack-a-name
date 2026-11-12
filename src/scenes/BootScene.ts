import Phaser from 'phaser'
import { FACE_KEYS } from '../config'

export class BootScene extends Phaser.Scene {
  constructor() {
    super('boot')
  }

  preload() {
    const barBg = this.add.rectangle(640, 360, 420, 18, 0x3a2216).setOrigin(0.5)
    const bar = this.add.rectangle(640 - 210, 360, 4, 14, 0xd4a017).setOrigin(0, 0.5)
    this.load.on('progress', (v: number) => {
      bar.width = Math.max(4, 420 * v)
    })
    this.load.on('complete', () => {
      bar.destroy()
      barBg.destroy()
    })

    this.load.image('backdrop', 'assets/art/backdrop.png')
    this.load.image('hole_frame', 'assets/art/hole_frame.png')
    this.load.image('hole_void', 'assets/art/hole_void.png')
    this.load.image('hat', 'assets/art/party_hat.png')
    this.load.image('banner', 'assets/art/banner.png')
    this.load.image('mallet_0', 'assets/art/mallet_0.png')
    this.load.image('mallet_1', 'assets/art/mallet_1.png')
    this.load.image('mallet_2', 'assets/art/mallet_2.png')
    this.load.image('star_burst', 'assets/art/star_burst.png')
    this.load.image('confetti', 'assets/art/confetti_sheet.png')

    const faceFiles = [
      'face_01_surprised.png',
      'face_02_smiling_cap.png',
      'face_03_serious.png',
      'face_04_looking_down.png',
      'face_05_cat_face.png',
      'face_06_smirking.png',
      'face_07_backwards_cap.png',
      'face_08_wet_hair.png',
    ]
    FACE_KEYS.forEach((key, i) => {
      this.load.image(key, `assets/faces/${faceFiles[i]}`)
    })
  }

  create() {
    this.scene.start('menu')
  }
}
