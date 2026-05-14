// Lightweight canvas confetti burst.
// Spawns particles from the screen edges and animates them inward + downward
// with gravity and rotation. No dependencies, runs ~1.6s per call.

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
  angle: number;
  spin: number;
  life: number;
  maxLife: number;
}

const COLORS = [
  '#f43f5e', '#f97316', '#eab308', '#22c55e',
  '#06b6d4', '#3b82f6', '#a855f7', '#ec4899',
];

let canvas: HTMLCanvasElement | null = null;
let ctx: CanvasRenderingContext2D | null = null;
let particles: Particle[] = [];
let rafId: number | null = null;
let lastTs = 0;

function ensureCanvas(): { canvas: HTMLCanvasElement; ctx: CanvasRenderingContext2D } | null {
  if (typeof window === 'undefined') return null;
  if (!canvas) {
    canvas = document.createElement('canvas');
    canvas.style.cssText = [
      'position:fixed',
      'inset:0',
      'width:100vw',
      'height:100vh',
      'pointer-events:none',
      'z-index:9999',
    ].join(';');
    document.body.appendChild(canvas);
    ctx = canvas.getContext('2d');
  }
  const c = ctx;
  if (!c) return null;
  if (canvas.width !== window.innerWidth || canvas.height !== window.innerHeight) {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  return { canvas, ctx: c };
}

function spawnFromEdges(count: number) {
  const w = window.innerWidth;
  const h = window.innerHeight;
  // 4 edges, distribute spawns across them with velocity pointing inward.
  for (let i = 0; i < count; i++) {
    const edge = Math.floor(Math.random() * 4);
    let x = 0, y = 0, vx = 0, vy = 0;
    const speed = 250 + Math.random() * 350; // px/s
    if (edge === 0) {
      // top edge → falling in with rightward/leftward drift
      x = Math.random() * w;
      y = -10;
      vx = (Math.random() - 0.5) * 200;
      vy = speed * 0.4;
    } else if (edge === 1) {
      // right edge → launches leftward + upward
      x = w + 10;
      y = h * (0.2 + Math.random() * 0.7);
      vx = -speed;
      vy = -speed * (0.3 + Math.random() * 0.4);
    } else if (edge === 2) {
      // bottom edge → launches upward
      x = Math.random() * w;
      y = h + 10;
      vx = (Math.random() - 0.5) * 300;
      vy = -speed * (0.7 + Math.random() * 0.4);
    } else {
      // left edge → launches rightward + upward
      x = -10;
      y = h * (0.2 + Math.random() * 0.7);
      vx = speed;
      vy = -speed * (0.3 + Math.random() * 0.4);
    }
    const maxLife = 1200 + Math.random() * 600;
    particles.push({
      x, y, vx, vy,
      size: 6 + Math.random() * 6,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      angle: Math.random() * Math.PI * 2,
      spin: (Math.random() - 0.5) * 12,
      life: 0,
      maxLife,
    });
  }
}

function step(ts: number) {
  if (!ctx || !canvas) return;
  const c = ctx;
  const cv = canvas;
  const dt = lastTs ? Math.min(50, ts - lastTs) : 16;
  lastTs = ts;
  const dtSec = dt / 1000;
  const gravity = 700; // px/s^2

  c.clearRect(0, 0, cv.width, cv.height);

  for (const p of particles) {
    p.life += dt;
    p.vy += gravity * dtSec;
    p.vx *= 0.99;
    p.x += p.vx * dtSec;
    p.y += p.vy * dtSec;
    p.angle += p.spin * dtSec;

    const fade = Math.max(0, 1 - p.life / p.maxLife);
    c.save();
    c.globalAlpha = fade;
    c.translate(p.x, p.y);
    c.rotate(p.angle);
    c.fillStyle = p.color;
    c.fillRect(-p.size / 2, -p.size / 4, p.size, p.size / 2);
    c.restore();
  }

  particles = particles.filter((p) => p.life < p.maxLife && p.y < cv.height + 50);

  if (particles.length > 0) {
    rafId = requestAnimationFrame(step);
  } else {
    rafId = null;
    lastTs = 0;
    c.clearRect(0, 0, cv.width, cv.height);
  }
}

export function celebrate(count = 90): void {
  const handle = ensureCanvas();
  if (!handle) return;
  // Respect reduced-motion preference.
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;
  spawnFromEdges(count);
  if (rafId === null) {
    lastTs = 0;
    rafId = requestAnimationFrame(step);
  }
}
