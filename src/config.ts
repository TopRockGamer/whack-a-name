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
 * visibleY ≈ 0 keeps the face centred on the painted void so the mask
 * shows forehead near the top of the hole (where the hat should sit).
 */
export const ROW_LAYOUT = {
  back: { facePx: 98, hiddenY: 48, visibleY: 0 },
  front: { facePx: 116, hiddenY: 58, visibleY: 0 },
} as const

/**
 * Hat local transform (ChatGPT Desktop + pose QA).
 * Local Y = -facePx * crownMul so back/front rows scale together.
 */
export const HAT_LAYOUT = {
  originX: 0.5,
  originY: 0.82,
  /** hatScale = (facePx * widthMul) / 174 */
  widthMul: 0.55,
  angle: -8,
  offsetXMul: 0,
  /** Brim on hairline ≈ 0.36–0.40 of face radius above center */
  crownMul: 0.38,
} as const

/** Hole-mask ellipse — keep inside painted voids */
export const HOLE_MASK = {
  back: { w: 88, h: 60 },
  front: { w: 102, h: 70 },
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
  'face_02',
  'face_03',
  'face_04',
  'face_05',
  'face_06',
  'face_07',
  'face_08',
] as const
