# crawler/page_ops.py
import contextlib, time
from playwright.async_api import Page

TARGET_SELECTORS = [
    "main", "article", ".entry-content", ".post-content",
    ".wp-block-post-content", ".elementor", ".elementor-widget-container",
    "#content", "#main"
]

async def wait_rendering(page: Page):
    with contextlib.suppress(Exception):
        await page.wait_for_load_state("networkidle", timeout=8000)

    try:
        await page.evaluate("""
            const sleep = ms => new Promise(r=>setTimeout(r,ms));
            let total = 0;
            const step = () => window.scrollBy(0, Math.floor(window.innerHeight*0.8));
            for (let i=0;i<4;i++){ step(); await sleep(250); total+=250; }
            window.scrollTo(0,0);
        """)
    except Exception:
        pass

    try:
        await page.evaluate("""
            return new Promise(res=>{
                if (window.MathJax && MathJax.typesetPromise){
                    MathJax.typesetPromise().then(()=>res()).catch(()=>res());
                } else { setTimeout(res, 600); }
            });
        """)
    except Exception:
        pass

async def normalize_iframes_keep_tags(page: Page, *, max_iframes=40, viewport_margin=40, min_area=0, do_light_scroll=True) -> str:
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
                    try { const a = document.createElement('a'); a.href = raw; el.setAttribute('src', a.href); } catch (e) {}
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

CONSENT_BUTTON_XP = [
    "//button[contains(., '동의') or contains(., '허용') or contains(., '수락')]",
    "//button[contains(., 'Accept') or contains(., 'Agree') or contains(., 'Allow')]",
    "//div[contains(@class,'onetrust')]//button[.//text()[contains(.,'Accept') or contains(.,'동의')]]",
]

async def click_consent(page: Page):
    for xp in CONSENT_BUTTON_XP:
        try:
            btn = await page.wait_for_selector(f"xpath={xp}", timeout=1200)
            if btn:
                await btn.click()
                await page.wait_for_timeout(300)
        except Exception:
            pass
