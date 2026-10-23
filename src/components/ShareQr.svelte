<script lang="ts">
  import { t } from '../lib/i18n.svelte';

  // "Share Quizilla" card: QR code of the public app link (public/qr-quizilla.svg).
  // The QR always points to the live app, also when running locally.
  const APP_URL = 'https://ivanjanovicdigi.github.io/Quizilla/';
  const src = `${import.meta.env.BASE_URL}qr-quizilla.svg`;
</script>

<section class="card share">
  <!-- white tile so the code stays scannable in dark mode -->
  <img class="qr" {src} alt={t('share.alt')} width="132" height="132" />
  <div class="text">
    <h3>{t('share.title')}</h3>
    <p class="small muted">{t('share.info')}</p>
    <a class="small link" href={APP_URL} target="_blank" rel="noopener">{APP_URL.replace('https://', '')}</a>
  </div>
</section>

<style>
  .share { display: flex; align-items: center; gap: 16px; }
  .qr {
    flex: none; display: block; width: 132px; height: 132px;
    background: #fff; border-radius: 12px; padding: 6px; box-sizing: border-box;
  }
  .text { min-width: 0; display: flex; flex-direction: column; gap: 6px; }
  .text h3, .text p { margin: 0; }
  .link { overflow-wrap: anywhere; color: var(--accent-strong); }
  @media (max-width: 340px) {
    .share { flex-direction: column; text-align: center; }
  }
</style>
