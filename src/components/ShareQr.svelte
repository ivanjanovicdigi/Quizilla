<script lang="ts">
  import { t } from '../lib/i18n.svelte';

  // "Share Quizilla" card: big QR code of the public app link (public/qr-quizilla.svg).
  // The QR always points to the live app, also when running locally. Always shown.
  const APP_URL = 'https://ivanjanovicdigi.github.io/Quizilla/';
  const src = `${import.meta.env.BASE_URL}qr-quizilla.svg`;
</script>

<section class="card share">
  <h3>{t('share.title')}</h3>
  <!-- white tile so the code stays scannable in dark mode -->
  <img class="qr" {src} alt={t('share.alt')} width="240" height="240" />
  <p class="small muted">{t('share.info')}</p>
  <a class="small link" href={APP_URL} target="_blank" rel="noopener">{APP_URL.replace('https://', '')}</a>
</section>

<style>
  .share { display: flex; flex-direction: column; align-items: center; gap: 10px; text-align: center; }
  .share h3, .share p { margin: 0; }
  .qr {
    display: block; width: min(240px, 100%); height: auto; aspect-ratio: 1;
    background: #fff; border-radius: 14px; padding: 10px; box-sizing: border-box;
  }
  .link { overflow-wrap: anywhere; color: var(--accent-strong); }
</style>
