// Lightweight canvas confetti burst.
// Combines edge launchers + a center starburst for a celebratory feel.
// No dependencies. Each call runs for ~2s.

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
  shape: 'rect' | 'circle';
  angle: number;
  spin: number;
  life: number;
  maxLife: number;
}

const COLORS = [
  '#f43f5e', '#f97316', '#fbbf24', '#facc15',
  '#22c55e', '#10b981', '#06b6d4', '#3b82f6',
  '#6366f1', '#a855f7', '#ec4899', '#fb7185',
];

let canvas: HTMLCanvasElement | null = null;
let ctx: CanvasRenderingContext2D | null = null;
let particles: Particle[] = [];
let rafId: number | null = null;
let lastTs = 0;

function ensureCanvas(): boolean {
  if (typeof window === 'undefined') return false;
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
  if (!ctx) return false;
  const dpr = window.devicePixelRatio || 1;
  const w = window.innerWidth;
  const h = window.innerHeight;
  if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  return true;
}

function randColor(): string {
  return COLORS[Math.floor(Math.random() * COLORS.length)];
}

function spawnEdgeBurst(count: number) {
  const w = window.innerWidth;
  const h = window.innerHeight;
  for (let i = 0; i < count; i++) {
    const edge = Math.floor(Math.random() * 4);
    let x = 0, y = 0, vx = 0, vy = 0;
    const speed = 350 + Math.random() * 450;
    if (edge === 0) {
      x = Math.random() * w;
      y = -10;
      vx = (Math.random() - 0.5) * 250;
      vy = speed * 0.5;
    } else if (edge === 1) {
      x = w + 10;
      y = h * (0.15 + Math.random() * 0.7);
      vx = -speed;
      vy = -speed * (0.3 + Math.random() * 0.5);
    } else if (edge === 2) {
      x = Math.random() * w;
      y = h + 10;
      vx = (Math.random() - 0.5) * 350;
      vy = -speed * (0.8 + Math.random() * 0.5);
    } else {
      x = -10;
      y = h * (0.15 + Math.random() * 0.7);
      vx = speed;
      vy = -speed * (0.3 + Math.random() * 0.5);
    }
    particles.push({
      x, y, vx, vy,
      size: 10 + Math.random() * 10,
      color: randColor(),
      shape: Math.random() < 0.65 ? 'rect' : 'circle',
      angle: Math.random() * Math.PI * 2,
      spin: (Math.random() - 0.5) * 14,
      life: 0,
      maxLife: 1800 + Math.random() * 700,
    });
  }
}

function spawnCenterBurst(count: number) {
  const cx = window.innerWidth / 2;
  const cy = window.innerHeight * 0.45;
  for (let i = 0; i < count; i++) {
    const a = Math.random() * Math.PI * 2;
    const speed = 200 + Math.random() * 400;
    particles.push({
      x: cx,
      y: cy,
      vx: Math.cos(a) * speed,
      vy: Math.sin(a) * speed - 100,
      size: 8 + Math.random() * 8,
      color: randColor(),
      shape: Math.random() < 0.5 ? 'rect' : 'circle',
      angle: Math.random() * Math.PI * 2,
      spin: (Math.random() - 0.5) * 16,
      life: 0,
      maxLife: 1500 + Math.random() * 600,
    });
  }
}

function step(ts: number) {
  if (!ctx || !canvas) return;
  const c = ctx;
  const w = window.innerWidth;
  const h = window.innerHeight;
  const dt = lastTs ? Math.min(50, ts - lastTs) : 16;
  lastTs = ts;
  const dtSec = dt / 1000;
  const gravity = 720;

  c.clearRect(0, 0, w, h);

  for (const p of particles) {
    p.life += dt;
    p.vy += gravity * dtSec;
    p.vx *= 0.992;
    p.x += p.vx * dtSec;
    p.y += p.vy * dtSec;
    p.angle += p.spin * dtSec;

    const fade = Math.max(0, 1 - p.life / p.maxLife);
    c.save();
    c.globalAlpha = fade;
    c.translate(p.x, p.y);
    c.rotate(p.angle);
    c.fillStyle = p.color;
    if (p.shape === 'rect') {
      c.fillRect(-p.size / 2, -p.size / 3, p.size, (p.size * 2) / 3);
    } else {
      c.beginPath();
      c.arc(0, 0, p.size / 2, 0, Math.PI * 2);
      c.fill();
    }
    c.restore();
  }

  particles = particles.filter((p) => p.life < p.maxLife && p.y < h + 80);

  if (particles.length > 0) {
    rafId = requestAnimationFrame(step);
  } else {
    rafId = null;
    lastTs = 0;
    c.clearRect(0, 0, w, h);
  }
}

export function celebrate(): void {
  if (!ensureCanvas()) return;
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;
  spawnEdgeBurst(120);
  spawnCenterBurst(60);
  if (rafId === null) {
    lastTs = 0;
    rafId = requestAnimationFrame(step);
  }
}
