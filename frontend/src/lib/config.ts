// Per-deployment configuration. Override via .env (VITE_*) when a fork wants
// to point at different data, identify a different assembly, or change the
// brand displayed in the UI.
//
// - VITE_DATA_BASE         — base URL for static data (default: `/data`)
// - VITE_MUNICIPALITY      — internal module key matching municipal_modules/<name>
// - VITE_ASSEMBLY_NAME     — human-readable assembly display name (header / footer / about)
// - VITE_SITE_TAGLINE      — short description shown beneath the assembly name in About
// - VITE_PROJECT_REPO_URL  — link target for "GitHub Issues" in footer/about

export const DATA_BASE: string = import.meta.env.VITE_DATA_BASE ?? '/data';
export const MUNICIPALITY: string = import.meta.env.VITE_MUNICIPALITY ?? 'sample';
export const ASSEMBLY_NAME: string =
  import.meta.env.VITE_ASSEMBLY_NAME ?? 'サンプル議会';
export const SITE_TAGLINE: string =
  import.meta.env.VITE_SITE_TAGLINE ??
  '議会の会議録を質疑応答単位で振り返り、自分の評価を匿名で記録できる非公式ビューワー。評価データはブラウザ内にのみ保存されます。';
export const PROJECT_REPO_URL: string =
  import.meta.env.VITE_PROJECT_REPO_URL ??
  'https://github.com/Luis8492/ZeroTrustDemocracy/issues';
