// Single source of truth for the assembly identifier and API base URL.
// Override via .env files (VITE_API_BASE, VITE_MUNICIPALITY) when forking.

export const API_BASE: string = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
export const MUNICIPALITY: string = import.meta.env.VITE_MUNICIPALITY ?? 'setagaya';
