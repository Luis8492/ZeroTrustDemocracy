/// <reference types="svelte" />
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
  readonly VITE_MUNICIPALITY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
