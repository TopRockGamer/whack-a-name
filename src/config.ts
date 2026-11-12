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
 * Plump creature: blank fur head + shoulders/chest.
 * facePx covers the head dome; headFromTop ≈ 118/340 on mole_body.png
 */
export const ROW_LAYOUT = {
  back: {
    bodyH: 175,
    facePx: 72,
    hatW: 52,
    headFromTop: 0.32,
    popUp: 72,
    hideDown: 210,
  },
  front: {
    bodyH: 230,
    facePx: 86,
    hatW: 62,
    headFromTop: 0.32,
    popUp: 90,
    hideDown: 260,
  },
} as const

/** Tight hole mask — body clipped by rim, never spills onto wood */
export const HOLE_MASK = {
  back: { w: 108, h: 92 },
  front: { w: 136, h: 128 },
} as const

/** Rim lip ABOVE moles — slightly larger than mask for well depth */
export const HOLE_RIM = {
  back: { size: 148 },
  front: { size: 186 },
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
