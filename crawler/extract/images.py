# -*- coding: utf-8 -*-
from typing import List

async def harvest_images(page, base_url: str) -> List[str]:
    js = r"""
    (base) => {
      const toAbs = (u) => {
        try { const a = document.createElement('a'); a.href = u; return a.href; } catch(e){ return null; }
      };
      const urls = new Set();
      for (const img of Array.from(document.querySelectorAll('img'))) {
        const cand = [
          img.getAttribute('src'),
          img.getAttribute('data-src'),
          img.getAttribute('data-original'),
          img.getAttribute('data-lazy'),
          img.getAttribute('data-url')
        ].filter(Boolean);
        for (const c of cand) { const u = toAbs(c); if (u) urls.add(u); }
        const srcset = img.getAttribute('srcset') || img.getAttribute('data-srcset');
        if (srcset) {
          for (const part of srcset.split(',')) {
            const u = toAbs(part.trim().split(' ')[0]);
            if (u) urls.add(u);
          }
        }
      }
      for (const s of Array.from(document.querySelectorAll('source'))) {
        const ss = s.getAttribute('srcset');
        if (ss) {
          for (const part of ss.split(',')) {
            const u = toAbs(part.trim().split(' ')[0]);
            if (u) urls.add(u);
          }
        }
        const su = s.getAttribute('src');
        if (su) { const u = toAbs(su); if (u) urls.add(u); }
      }
      for (const m of Array.from(document.querySelectorAll('meta[property="og:image"], meta[name="og:image"], meta[name="twitter:image"], meta[property="twitter:image"]'))) {
        const c = m.getAttribute('content');
        if (c) { const u = toAbs(c); if (u) urls.add(u); }
      }
      for (const el of Array.from(document.querySelectorAll('*'))) {
        const cs = getComputedStyle(el);
        const bg = cs && cs.getPropertyValue('background-image');
        if (bg && bg.includes('url(')) {
          const matches = [...bg.matchAll(/url\((['"]?)(.*?)\1\)/g)];
          for (const m of matches) {
            const u = toAbs(m[2]); if (u) urls.add(u);
          }
        }
      }
      for (const ln of Array.from(document.querySelectorAll('link[rel="image_src"], link[rel="thumbnail"]'))) {
        const href = ln.getAttribute('href');
        if (href) { const u = toAbs(href); if (u) urls.add(u); }
      }
      return Array.from(urls);
    }
    """
    try:
        imgs = await page.evaluate(js, base_url)
        exts = (".jpg",".jpeg",".png",".webp",".gif",".bmp",".svg",".avif")
        imgs = [u for u in imgs if any(u.split("?",1)[0].lower().endswith(e) for e in exts)]
        seen, out = set(), []
        for u in imgs:
            if u in seen: continue
            seen.add(u); out.append(u)
        return out
    except Exception:
        return []
