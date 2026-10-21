"""Render PWA PNG icons from public/favicon.svg (run: python3 scripts/make-icons.py)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parent.parent
svg = (root / "public/favicon.svg").read_text()
targets = [("icon-192.png", 192, False), ("icon-512.png", 512, False),
           ("icon-512-maskable.png", 512, True), ("apple-touch-icon.png", 180, True)]
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, size, full in targets:
        pg = b.new_page(viewport={"width": size, "height": size})
        # maskable/apple: full-bleed square background with padded mark
        inner = svg.replace('rx="16"', 'rx="0"') if full else svg
        sized = inner.replace("<svg ", f'<svg width="{size}" height="{size}" ')
        pg.set_content(f'<html><body style="margin:0;background:transparent">{sized}</body></html>')
        pg.screenshot(path=str(root / "public" / name), omit_background=True)
        pg.close()
    b.close()
print("icons written")
