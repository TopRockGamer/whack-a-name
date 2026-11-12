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
  /** back row = smaller faces, shallower pop */
  row: 'back' | 'front'
}

/**
 * Hole centres measured from painted voids in backdrop.png
 * (ChatGPT placement review + dark-ellipse detection).
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
 * Face diameter + pop offsets per row.
 * Hats are baked into face PNGs (scripts/bake_hats_on_faces.py) so they
 * cannot float as a separate sprite.
 */
export const ROW_LAYOUT = {
  // Slightly larger so crown hair under brim reads; keep tips below wood plank.
  back: { facePx: 70, hiddenY: 36, visibleY: 7 },
  front: { facePx: 86, hiddenY: 44, visibleY: 16 },
} as const

/** @deprecated Hats are baked onto faces; kept for reference / ChatGPT notes */
export const HAT_LAYOUT = {
  originX: 0.5,
  originY: 0.7,
  widthMul: 0.62,
  angle: -8,
  offsetXMul: 0,
  crownMul: 0.2,
  note: 'baked into face PNGs — PlayScene no longer spawns a separate hat',
} as const

/** Hole-mask ellipse — match painted void; do not spill hats onto wood */
export const HOLE_MASK = {
  back: { w: 100, h: 56 },
  front: { w: 112, h: 70 },
} as const

/** ?pose=1 — hold every mole up for screenshot QA (read live, not import-time) */
export function isPoseMode(): boolean {
  if (typeof window === 'undefined') return false
  return new URLSearchParams(window.location.search).has('pose')
}

/** @deprecated prefer isPoseMode() */
export const POSE_MODE = false

export const FACE_KEYS = [
  'face_01',
  'face_08', // was face_02 (pre-existing cap fought the party-hat seat)
  'face_03',
  'face_04',
  'face_05',
  'face_06',
  'face_07',
  'face_02',
] as const
