<script lang="ts">
  // App icon artwork (public/icon-192.png / icon-512.png – gold Q + kaiju, transparent rounded corners).
  let { size = 40 }: { size?: number } = $props();
  const base = import.meta.env.BASE_URL;
</script>

<img
  class="logo"
  src="{base}icon-192.png"
  srcset="{base}icon-192.png 192w, {base}icon-512.png 512w"
  sizes="{size}px"
  alt=""
  width={size}
  height={size} />

<style>
  .logo { display: inline-block; flex: none; object-fit: contain; vertical-align: middle; }
</style>
