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
    this.load.image('banner', 'assets/art/banner.png')
    this.load.image('mallet_0', 'assets/art/mallet_0.png')
    this.load.image('mallet_1', 'assets/art/mallet_1.png')
    this.load.image('mallet_2', 'assets/art/mallet_2.png')
    this.load.image('star_burst', 'assets/art/star_burst.png')
    this.load.image('confetti', 'assets/art/confetti_sheet.png')

    // Mole character art — body + hat are rig layers; faces are head decals
    const bust = `v=${Date.now()}`
    this.load.image('mole_body', `assets/art/mole_body.png?${bust}`)
    this.load.image('hole_rim', `assets/art/hole_rim.png?${bust}`)
    this.load.image('board_lid', `assets/art/board_lid.png?${bust}`)
    this.load.image('party_hat', `assets/art/party_hat_rig.png?${bust}`)

    const faceFiles: Record<string, string> = {
      face_01: 'face_01_surprised.png',
      face_02: 'face_02_smiling_cap.png',
      face_03: 'face_03_serious.png',
      face_04: 'face_04_looking_down.png',
      face_05: 'face_05_cat_face.png',
      face_06: 'face_06_smirking.png',
      face_07: 'face_07_backwards_cap.png',
      face_08: 'face_08_wet_hair.png',
    }
    FACE_KEYS.forEach((key) => {
      // Circular face decals (no baked hats — hat is on the mole rig)
      this.load.image(key, `assets/faces/${faceFiles[key]}?${bust}`)
    })
  }

  create() {
    this.scene.start('menu')
  }
}
