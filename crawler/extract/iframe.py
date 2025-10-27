# -*- coding: utf-8 -*-
from playwright.async_api import Page

async def normalize_iframes_keep_tags(page: Page, *, max_iframes: int = 40, viewport_margin: int = 40, min_area: int = 0, do_light_scroll: bool = True) -> str:
    if do_light_scroll:
        try:
            await page.evaluate("""
                const sleep = ms => new Promise(r=>setTimeout(r,ms));
                for (let i=0;i<6;i++){
                    window.scrollBy(0, Math.floor(window.innerHeight*0.9));
                    await sleep(250);
                }
                window.scrollTo(0,0);
            """)
        except Exception:
            pass

    await page.evaluate(
        """(maxIframes, minArea, viewportMargin) => {
            const vw = window.innerWidth, vh = window.innerHeight;
            const isVisible = (el) => {
                const cs = getComputedStyle(el);
                if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity || '1') === 0) return false;
                const rect = el.getBoundingClientRect();
                if (!rect || rect.width <= 0 || rect.height <= 0) return false;
                const inViewport =
                    (rect.bottom >= -viewportMargin) &&
                    (rect.top <= (vh + viewportMargin)) &&
                    (rect.right >= -viewportMargin) &&
                    (rect.left <= (vw + viewportMargin));
                if (!inViewport) return false;
                if ((rect.width * rect.height) < minArea) return false;
                return true;
            };
            let kept = 0;
            for (const el of document.querySelectorAll('iframe')) {
                if (kept >= maxIframes) break;
                if (!isVisible(el)) continue;
                const raw = el.getAttribute('src') || '';
                if (raw) {
                    try {
                        const a = document.createElement('a');
                        a.href = raw;
                        el.setAttribute('src', a.href);
                    } catch (e) {}
                }
                el.setAttribute('data-iframe-preserved', '1');
                kept++;
            }
            const summary = document.createComment(`PRESERVED IFRAMES: ${kept}/${document.querySelectorAll('iframe').length}`);
            document.documentElement.appendChild(summary);
        }""",
        max_iframes, min_area, viewport_margin
    )
    return await page.evaluate("() => document.documentElement.outerHTML")
