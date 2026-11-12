export const GAME_WIDTH = 1280
export const GAME_HEIGHT = 720
export const ROUND_SECONDS = 50
export const MAX_UP_MS = 1400
export const MIN_UP_MS = 700
export const SPAWN_GAP_START_MS = 900
export const SPAWN_GAP_END_MS = 420
export const HIT_SCORE = 100
export const MISS_PENALTY = 0

/** Personalisation — edit per order */
export const PERSON = {
  name: 'TopRock',
  bannerTitle: 'Whack-a-TopRock',
  endMessage:
    'Happy Birthday, TopRock! May your playlist stay un-ruined and your party hats stay ridiculous.',
  roastMiss: [
    'Missed! He ruined another track.',
    'Too slow — playlist in danger.',
    'Oof. He smirked.',
  ],
  roastHit: ['Bonk!', 'Nice one!', 'Hat flew!', 'Got him!'],
}

export type HoleDef = {
  x: number
  y: number
  scale: number
  /** back row = smaller moles, shallower pop */
  row: 'back' | 'front'
}

/**
 * Hole centres measured from painted voids in backdrop.png.
 * Back row first, then front.
 */
export const HOLES: HoleDef[] = [
  { x: 521, y: 410, scale: 0.78, row: 'back' },
  { x: 822, y: 410, scale: 0.76, row: 'back' },
  { x: 1125, y: 410, scale: 0.78, row: 'back' },
  { x: 475, y: 493, scale: 0.95, row: 'front' },
  { x: 821, y: 493, scale: 1.0, row: 'front' },
  { x: 1161, y: 493, scale: 0.95, row: 'front' },
]

/**
 * Mole character layout — one Phaser container per hole:
 *   body (2.5D cylinder) + face decal + hat
 * The whole stack rises through a hole geometry mask.
 *
 * bodyH: displayed height of mole_body.png (origin bottom-centre).
 * facePx: circular face decal on the head.
 * hatW: party hat width on the crown.
 * headFromTop: fraction down the body PNG where the head centre sits (~78/320).
 * popUp: how far above the hole centre the body origin sits when fully up
 *   (negative = origin above hole centre so head clears the rim).
 * hideDown: how far below hole centre when fully hidden.
 */
/**
 * popUp / hideDown are offsets ADDED to hole.y for the body origin (bottom).
 * Larger popUp = character sits lower so the HEAD lands inside the hole mask
 * (face+hat were previously clipped above the ellipse).
 *
 * Target when up: head ≈ hole.y − 8 (near top-centre of the void).
 *   popUp ≈ bodyH * (1 - headFromTop) - 8
 */
export const ROW_LAYOUT = {
  back: {
    bodyH: 160,
    facePx: 102,
    hatW: 62,
    headFromTop: 0.22,
    popUp: 112,
    hideDown: 250,
    visibleY: 112,
    hiddenY: 250,
  },
  front: {
    bodyH: 200,
    facePx: 128,
    hatW: 78,
    headFromTop: 0.22,
    popUp: 142,
    hideDown: 310,
    visibleY: 142,
    hiddenY: 310,
  },
} as const

/** Hole-mask ellipse — clips the rising mole body as it emerges */
export const HOLE_MASK = {
  back: { w: 132, h: 108 },
  front: { w: 168, h: 156 },
} as const

/** @deprecated hats are a rig layer on the mole, not a separate float */
export const HAT_LAYOUT = {
  note: 'hat is a child of the mole container — see PlayScene.spawnMoleAt',
} as const

/** ?pose=1 — hold every mole up for screenshot QA */
export function isPoseMode(): boolean {
  if (typeof window === 'undefined') return false
  return new URLSearchParams(window.location.search).has('pose')
}

/** @deprecated prefer isPoseMode() */
export const POSE_MODE = false

export const FACE_KEYS = [
  'face_01',
  'face_02',
  'face_03',
  'face_04',
  'face_05',
  'face_06',
  'face_07',
  'face_08',
] as const
