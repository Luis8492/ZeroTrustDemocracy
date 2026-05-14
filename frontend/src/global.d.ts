/// <reference types="svelte" />
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DATA_BASE?: string;
  readonly VITE_MUNICIPALITY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
