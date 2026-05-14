import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  server: {
    host: '0.0.0.0',
    port: 8001,
  },
  build: {
    target: 'es2022',
    outDir: 'dist',
  },
});
