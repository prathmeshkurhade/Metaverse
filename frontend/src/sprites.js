/**
 * Pixel art avatar sprites -- drawn directly on canvas.
 * Each sprite is a 16x16 grid of colors. null = transparent.
 *
 * WHY code instead of images?
 * - No image loading delays
 * - No external URLs to manage
 * - Works offline
 * - Tiny file size (just arrays)
 * - Easy to add new sprites
 */

const _ = null  // transparent pixel

// Color palette
const R = '#ef4444'  // red
const B = '#3b82f6'  // blue
const G = '#22c55e'  // green
const Y = '#facc15'  // yellow
const P = '#a855f7'  // purple
const O = '#f97316'  // orange
const W = '#ffffff'  // white
const K = '#000000'  // black (outline)
const S = '#fbbf24'  // skin
const D = '#92400e'  // dark skin
const H = '#1e293b'  // hair dark
const E = '#0f172a'  // eyes

// Each sprite: { name, palette (16x16 grid), primaryColor }
export const AVATARS = [
  {
    id: 'knight',
    name: 'Knight',
    color: '#6366f1',
    pixels: [
      [_,_,_,_,_,K,K,K,K,K,K,_,_,_,_,_],
      [_,_,_,_,K,B,B,B,B,B,B,K,_,_,_,_],
      [_,_,_,K,B,B,B,B,B,B,B,B,K,_,_,_],
      [_,_,_,K,B,B,B,B,B,B,B,B,K,_,_,_],
      [_,_,K,K,K,K,K,K,K,K,K,K,K,K,_,_],
      [_,_,K,S,S,S,S,S,S,S,S,S,S,K,_,_],
      [_,_,K,S,E,E,S,S,S,E,E,S,S,K,_,_],
      [_,_,K,S,S,S,S,K,S,S,S,S,S,K,_,_],
      [_,_,_,K,S,S,S,S,S,S,S,S,K,_,_,_],
      [_,_,_,_,K,S,K,K,K,S,S,K,_,_,_,_],
      [_,_,_,K,B,B,B,B,B,B,B,B,K,_,_,_],
      [_,_,K,B,B,B,B,B,B,B,B,B,B,K,_,_],
      [_,_,K,B,B,B,B,B,B,B,B,B,B,K,_,_],
      [_,_,_,K,S,S,K,_,_,K,S,S,K,_,_,_],
      [_,_,_,K,S,S,K,_,_,K,S,S,K,_,_,_],
      [_,_,_,K,K,K,K,_,_,K,K,K,K,_,_,_],
    ],
  },
  {
    id: 'mage',
    name: 'Mage',
    color: '#a855f7',
    pixels: [
      [_,_,_,_,_,_,K,P,K,_,_,_,_,_,_,_],
      [_,_,_,_,_,K,P,P,P,K,_,_,_,_,_,_],
      [_,_,_,_,K,P,P,Y,P,P,K,_,_,_,_,_],
      [_,_,_,K,P,P,P,P,P,P,P,K,_,_,_,_],
      [_,_,K,K,K,K,K,K,K,K,K,K,K,_,_,_],
      [_,_,K,S,S,S,S,S,S,S,S,S,K,_,_,_],
      [_,_,K,S,E,E,S,S,S,E,E,S,K,_,_,_],
      [_,_,K,S,S,S,S,K,S,S,S,S,K,_,_,_],
      [_,_,_,K,S,S,S,S,S,S,S,K,_,_,_,_],
      [_,_,_,_,K,S,K,K,K,S,K,_,_,_,_,_],
      [_,_,_,K,P,P,P,P,P,P,P,K,_,_,_,_],
      [_,_,K,P,P,P,P,P,P,P,P,P,K,_,_,_],
      [_,_,K,P,P,P,P,P,P,P,P,P,K,_,_,_],
      [_,_,_,K,S,S,K,_,_,K,S,S,K,_,_,_],
      [_,_,_,K,S,S,K,_,_,K,S,S,K,_,_,_],
      [_,_,_,K,K,K,K,_,_,K,K,K,K,_,_,_],
    ],
  },
  {
    id: 'ranger',
    name: 'Ranger',
    color: '#22c55e',
    pixels: [
      [_,_,_,_,_,K,K,K,K,K,_,_,_,_,_,_],
      [_,_,_,_,K,G,G,G,G,G,K,_,_,_,_,_],
      [_,_,_,K,G,G,G,G,G,G,G,K,_,_,_,_],
      [_,_,K,K,K,K,K,K,K,K,K,K,K,_,_,_],
      [_,_,_,K,H,H,H,H,H,H,H,K,_,_,_,_],
      [_,_,K,S,S,S,S,S,S,S,S,S,K,_,_,_],
      [_,_,K,S,E,E,S,S,S,E,E,S,K,_,_,_],
      [_,_,K,S,S,S,S,K,S,S,S,S,K,_,_,_],
      [_,_,_,K,S,S,S,S,S,S,S,K,_,_,_,_],
      [_,_,_,_,K,S,K,K,K,S,K,_,_,_,_,_],
      [_,_,_,K,G,G,G,G,G,G,G,K,_,_,_,_],
      [_,_,K,G,G,G,G,G,G,G,G,G,K,_,_,_],
      [_,_,K,G,G,G,G,G,G,G,G,G,K,_,_,_],
      [_,_,_,K,S,S,K,_,_,K,S,S,K,_,_,_],
      [_,_,_,K,S,S,K,_,_,K,S,S,K,_,_,_],
      [_,_,_,K,K,K,K,_,_,K,K,K,K,_,_,_],
    ],
  },
  {
    id: 'warrior',
    name: 'Warrior',
    color: '#ef4444',
    pixels: [
      [_,_,_,_,_,_,K,K,K,_,_,_,_,_,_,_],
      [_,_,_,_,_,K,R,R,R,K,_,_,_,_,_,_],
      [_,_,_,_,K,H,H,H,H,H,K,_,_,_,_,_],
      [_,_,_,K,H,H,H,H,H,H,H,K,_,_,_,_],
      [_,_,_,K,H,H,H,H,H,H,H,K,_,_,_,_],
      [_,_,K,S,S,S,S,S,S,S,S,S,K,_,_,_],
      [_,_,K,S,E,E,S,S,S,E,E,S,K,_,_,_],
      [_,_,K,S,S,S,S,K,S,S,S,S,K,_,_,_],
      [_,_,_,K,S,S,S,S,S,S,S,K,_,_,_,_],
      [_,_,_,_,K,S,K,K,K,S,K,_,_,_,_,_],
      [_,_,_,K,R,R,R,R,R,R,R,K,_,_,_,_],
      [_,K,K,R,R,R,R,R,R,R,R,R,K,K,_,_],
      [_,K,_,K,R,R,R,R,R,R,R,K,_,K,_,_],
      [_,_,_,K,S,S,K,_,_,K,S,S,K,_,_,_],
      [_,_,_,K,S,S,K,_,_,K,S,S,K,_,_,_],
      [_,_,_,K,K,K,K,_,_,K,K,K,K,_,_,_],
    ],
  },
  {
    id: 'healer',
    name: 'Healer',
    color: '#facc15',
    pixels: [
      [_,_,_,_,_,_,_,K,_,_,_,_,_,_,_,_],
      [_,_,_,_,_,_,K,Y,K,_,_,_,_,_,_,_],
      [_,_,_,_,_,K,W,W,W,K,_,_,_,_,_,_],
      [_,_,_,_,K,W,W,W,W,W,K,_,_,_,_,_],
      [_,_,_,K,K,K,K,K,K,K,K,K,_,_,_,_],
      [_,_,K,S,S,S,S,S,S,S,S,S,K,_,_,_],
      [_,_,K,S,E,E,S,S,S,E,E,S,K,_,_,_],
      [_,_,K,S,S,S,S,K,S,S,S,S,K,_,_,_],
      [_,_,_,K,S,S,S,S,S,S,S,K,_,_,_,_],
      [_,_,_,_,K,S,S,S,S,S,K,_,_,_,_,_],
      [_,_,_,K,W,W,W,W,W,W,W,K,_,_,_,_],
      [_,_,K,W,W,W,Y,Y,Y,W,W,W,K,_,_,_],
      [_,_,K,W,W,W,W,W,W,W,W,W,K,_,_,_],
      [_,_,_,K,S,S,K,_,_,K,S,S,K,_,_,_],
      [_,_,_,K,S,S,K,_,_,K,S,S,K,_,_,_],
      [_,_,_,K,K,K,K,_,_,K,K,K,K,_,_,_],
    ],
  },
  {
    id: 'shadow',
    name: 'Shadow',
    color: '#64748b',
    pixels: [
      [_,_,_,_,_,K,K,K,K,K,_,_,_,_,_,_],
      [_,_,_,_,K,H,H,H,H,H,K,_,_,_,_,_],
      [_,_,_,K,H,H,H,H,H,H,H,K,_,_,_,_],
      [_,_,_,K,H,H,H,H,H,H,H,K,_,_,_,_],
      [_,_,K,K,K,K,K,K,K,K,K,K,K,_,_,_],
      [_,_,K,S,S,S,S,S,S,S,S,S,K,_,_,_],
      [_,_,K,S,W,E,S,S,S,W,E,S,K,_,_,_],
      [_,_,K,S,S,S,S,K,S,S,S,S,K,_,_,_],
      [_,_,_,K,S,S,S,S,S,S,S,K,_,_,_,_],
      [_,_,_,_,K,S,K,K,K,S,K,_,_,_,_,_],
      [_,_,_,K,H,H,H,H,H,H,H,K,_,_,_,_],
      [_,_,K,H,H,H,H,H,H,H,H,H,K,_,_,_],
      [_,_,K,H,H,H,H,H,H,H,H,H,K,_,_,_],
      [_,_,_,K,H,H,K,_,_,K,H,H,K,_,_,_],
      [_,_,_,K,H,H,K,_,_,K,H,H,K,_,_,_],
      [_,_,_,K,K,K,K,_,_,K,K,K,K,_,_,_],
    ],
  },
]

/**
 * Draw a sprite on canvas at the given position.
 * The sprite is scaled to fit within tileSize.
 */
export function drawSprite(ctx, sprite, x, y, tileSize) {
  const pixelSize = tileSize / 16
  const pixels = sprite.pixels

  for (let row = 0; row < 16; row++) {
    for (let col = 0; col < 16; col++) {
      const color = pixels[row][col]
      if (color) {
        ctx.fillStyle = color
        ctx.fillRect(
          x + col * pixelSize,
          y + row * pixelSize,
          pixelSize + 0.5,  // +0.5 to avoid sub-pixel gaps
          pixelSize + 0.5
        )
      }
    }
  }
}

/**
 * Draw a sprite onto a small canvas and return it as a data URL.
 * Used for previews outside the main game canvas.
 */
export function spriteToDataUrl(sprite, size = 64) {
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  drawSprite(ctx, sprite, 0, 0, size)
  return canvas.toDataURL()
}
