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

export type HoleDef = { x: number; y: number; scale: number }

/** Six neat holes on the table plane (tuned to backdrop) */
export const HOLES: HoleDef[] = [
  { x: 390, y: 400, scale: 0.8 },
  { x: 640, y: 385, scale: 0.76 },
  { x: 890, y: 400, scale: 0.8 },
  { x: 420, y: 545, scale: 0.94 },
  { x: 640, y: 565, scale: 1.0 },
  { x: 860, y: 545, scale: 0.94 },
]

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
