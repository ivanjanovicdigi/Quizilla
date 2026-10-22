import { mount } from 'svelte';
import { registerSW } from 'virtual:pwa-register';
import './styles/app.css';
import './styles/code.css';
import App from './App.svelte';

// Service worker: when a new version is deployed, it is installed in the background and the
// page reloads itself, so nobody stays on an old cached build. Installed apps that stay open
// also check for a new version every hour.
registerSW({
  immediate: true,
  onRegisteredSW(_url, reg) {
    if (reg) setInterval(() => reg.update().catch(() => {}), 60 * 60 * 1000);
  }
});

export default mount(App, { target: document.getElementById('app')! });
