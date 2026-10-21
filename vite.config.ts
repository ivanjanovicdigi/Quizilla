import { defineConfig, loadEnv } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { VitePWA } from 'vite-plugin-pwa';
import pkg from './package.json' with { type: 'json' };

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  // GitHub Pages serves the app from /<repo>/ – set BASE_PATH=/Quizilla/ in CI.
  const base = env.BASE_PATH || '/';
  // Optional: point the dev server at a local PostgREST (used for local testing).
  const localApi = env.LOCAL_API;

  return {
    base,
    define: { __APP_VERSION__: JSON.stringify(pkg.version) },
    plugins: [
      svelte(),
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.svg', 'apple-touch-icon.png'],
        manifest: {
          name: 'Quizilla',
          short_name: 'Quizilla',
          description: 'Precvičuj si vedomosti – krátke kvízy s odomykaním úrovní.',
          lang: 'sk',
          theme_color: '#16a34a',
          background_color: '#0f172a',
          display: 'standalone',
          orientation: 'portrait',
          start_url: base,
          scope: base,
          icons: [
            { src: 'icon-192.png', sizes: '192x192', type: 'image/png' },
            { src: 'icon-512.png', sizes: '512x512', type: 'image/png' },
            { src: 'icon-512-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
          ]
        },
        workbox: {
          globPatterns: ['**/*.{js,css,html,svg,png,woff2}'],
          navigateFallbackDenylist: [/\/rest\//]
        }
      })
    ],
    server: {
      host: true,
      proxy: localApi
        ? { '/rest/v1': { target: localApi, changeOrigin: true, rewrite: (p) => p.replace(/^\/rest\/v1/, '') } }
        : undefined
    },
    build: { target: 'es2020' }
  };
});
