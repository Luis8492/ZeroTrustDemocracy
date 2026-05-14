// Single source of truth for where the static data lives.
// Override via .env (VITE_DATA_BASE) when a fork hosts data on a different path.
// Default is the relative `/data` path served from `public/data/` in dev and
// from the deployment output in production.

export const DATA_BASE: string = import.meta.env.VITE_DATA_BASE ?? '/data';
export const MUNICIPALITY: string = import.meta.env.VITE_MUNICIPALITY ?? 'setagaya';
