import { writable, type Writable } from 'svelte/store';
import { countEvaluations, getTheme, setTheme as persistTheme } from './db';
import type { ThemeName } from './types';

export const theme: Writable<ThemeName> = writable<ThemeName>('plain');
export const evaluatedCount: Writable<number> = writable<number>(0);

let themeInitialized = false;

export async function initStores(): Promise<void> {
  if (!themeInitialized) {
    const saved = await getTheme();
    theme.set(saved);
    applyTheme(saved);
    theme.subscribe((value) => {
      applyTheme(value);
      void persistTheme(value);
    });
    themeInitialized = true;
  }
  await refreshEvaluatedCount();
}

export async function refreshEvaluatedCount(): Promise<void> {
  evaluatedCount.set(await countEvaluations());
}

function applyTheme(value: ThemeName): void {
  document.documentElement.setAttribute('data-theme', value);
}
