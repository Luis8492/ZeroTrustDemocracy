// Lightweight canvas confetti burst.
// Fires "party popper" fountains from the bottom-left and bottom-right
// corners — particles shoot upward at varied angles and fall back along
// the sides, keeping the screen center mostly clear.
// No dependencies. Each call runs for ~1.8s.

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

function spawnCornerPoppers(perCorner: number) {
  const w = window.innerWidth;
  const h = window.innerHeight;
  const origins: Array<{ x: number; y: number; sign: 1 | -1 }> = [
    { x: 20, y: h - 20, sign: 1 },       // 左下: 右斜め上方向
    { x: w - 20, y: h - 20, sign: -1 },  // 右下: 左斜め上方向
  ];
  for (const o of origins) {
    for (let i = 0; i < perCorner; i++) {
      // 真上 〜 内向き約70° の扇形 (画面端まで含む)
      const angle = -Math.PI / 2 + o.sign * Math.random() * (Math.PI * 0.42);
      const speed = 520 + Math.random() * 600;
      particles.push({
        x: o.x,
        y: o.y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        size: 6 + Math.random() * 7,
        color: randColor(),
        shape: Math.random() < 0.7 ? 'rect' : 'circle',
        angle: Math.random() * Math.PI * 2,
        spin: (Math.random() - 0.5) * 14,
        life: 0,
        maxLife: 1500 + Math.random() * 700,
      });
    }
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
  // 意図的に prefers-reduced-motion を無視している:
  // この演出はユーザー操作起点のゲーミフィケーション要素であり、
  // OS のアニメーション縮小設定があっても発火させる。
  if (!ensureCanvas()) return;
  spawnCornerPoppers(60); // 左下60 + 右下60 = 120粒
  if (rafId === null) {
    lastTs = 0;
    rafId = requestAnimationFrame(step);
  }
}
