import './style.css'
import Phaser from 'phaser'
import { GAME_HEIGHT, GAME_WIDTH } from './config'
import { BootScene } from './scenes/BootScene'
import { MenuScene } from './scenes/MenuScene'
import { PlayScene } from './scenes/PlayScene'
import { EndScene } from './scenes/EndScene'

const parent = document.querySelector<HTMLDivElement>('#app')!
parent.innerHTML = '<div id="game-parent"></div>'

const game = new Phaser.Game({
  type: Phaser.AUTO,
  parent: 'game-parent',
  width: GAME_WIDTH,
  height: GAME_HEIGHT,
  backgroundColor: '#1a120c',
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  scene: [BootScene, MenuScene, PlayScene, EndScene],
})
;(window as unknown as { __PHASER_GAME__: Phaser.Game }).__PHASER_GAME__ = game
