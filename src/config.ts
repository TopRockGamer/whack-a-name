export const GAME_WIDTH = 1280
export const GAME_HEIGHT = 720
export const ROUND_SECONDS = 50
export const MAX_UP_MS = 1400
export const MIN_UP_MS = 700
export const SPAWN_GAP_START_MS = 900
export const SPAWN_GAP_END_MS = 420
export const HIT_SCORE = 100
export const MISS_PENALTY = 0

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
  row: 'back' | 'front'
}

export const HOLES: HoleDef[] = [
  { x: 521, y: 410, scale: 0.78, row: 'back' },
  { x: 822, y: 410, scale: 0.76, row: 'back' },
  { x: 1125, y: 410, scale: 0.78, row: 'back' },
  { x: 475, y: 493, scale: 0.95, row: 'front' },
  { x: 821, y: 493, scale: 1.0, row: 'front' },
  { x: 1161, y: 493, scale: 0.95, row: 'front' },
]

/**
 * TopRock-approved mole_body.png (512×624): plump fur + blank dome + carnival collar.
 * headFromTop = head centre Y / sprite H (from import_approved_mole.py).
 * facePx ≈ 0.335 * bodyH so the decal sits ON the dome, not replacing the body.
 */
export const MOLE_BODY_ASPECT = 512 / 624

export const ROW_LAYOUT = {
  back: {
    bodyH: 220,
    facePx: 54,
    hatW: 42,
    // Dome centre is high on the approved sprite (blank head sphere)
    headFromTop: 0.175,
    headAboveHole: 6,
    popUp: 72,
    hideDown: 210,
  },
  front: {
    bodyH: 280,
    facePx: 68,
    hatW: 50,
    headFromTop: 0.175,
    headAboveHole: 8,
    popUp: 90,
    hideDown: 260,
  },
} as const

/** Larger wells so the approved furry torso + collar can be seen */
export const HOLE_MASK = {
  back: { w: 150, h: 132 },
  front: { w: 190, h: 176 },
} as const

/** Rim lip ABOVE mole (child of hole bucket) */
export const HOLE_RIM = {
  back: { size: 196 },
  front: { size: 248 },
} as const

export function isPoseMode(): boolean {
  if (typeof window === 'undefined') return false
  return new URLSearchParams(window.location.search).has('pose')
}

/** Slow single-hole rise for pop-strip proofs */
export function isPopProofMode(): boolean {
  if (typeof window === 'undefined') return false
  return new URLSearchParams(window.location.search).has('popproof')
}

/** Hide face/hat — show only mole_body for art QA */
export function isBodyOnlyMode(): boolean {
  if (typeof window === 'undefined') return false
  return new URLSearchParams(window.location.search).has('bodyonly')
}

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
