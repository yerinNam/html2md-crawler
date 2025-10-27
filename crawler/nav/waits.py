# -*- coding: utf-8 -*-
import contextlib
from playwright.async_api import Page

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

async def deep_scroll_until_stable(page: Page, max_secs=4):
    import time
    t0 = time.perf_counter()
    last_h = 0
    stable_count = 0
    while (time.perf_counter()-t0) < max_secs:
        try:
            h = await page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight || 0")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(550)
            if h == last_h:
                stable_count += 1
            else:
                stable_count = 0
            last_h = h
            if stable_count >= 3:
                break
        except Exception:
            break
    with contextlib.suppress(Exception):
        await page.evaluate("window.scrollTo(0,0)")

async def wait_for_web_components(page: Page, tags=("attwc-globalnav-header", "att-gnav-header-bootstrap")):
    try:
        await page.wait_for_selector(tags[0], timeout=8000)
    except Exception:
        pass
    try:
        await page.evaluate("""async (tags) => {
          const defs = (window.customElements && tags)
            ? tags.map(t => customElements.whenDefined(t).catch(()=>{}))
            : [];
          await Promise.all(defs);
          await new Promise(r => requestAnimationFrame(()=>requestAnimationFrame(r)));
        }""", list(tags))
    except Exception:
        pass

async def open_common_menus(page: Page):
    selectors = [
        "#z1_profile_button",
        "[aria-haspopup='true'][aria-controls]",
        "button[aria-haspopup='menu']",
        "a[aria-haspopup='menu']",
        "button[aria-expanded='false']",
        "[data-toggle='dropdown']",
    ]
    async def _hover_click(sel: str):
        try:
            el = await page.query_selector(sel)
            if not el:
                return False
            await el.scroll_into_view_if_needed()
            with contextlib.suppress(Exception):
                await el.hover(); await page.wait_for_timeout(150)
            with contextlib.suppress(Exception):
                await el.click(); await page.wait_for_timeout(150)
            with contextlib.suppress(Exception):
                await el.focus(); await page.keyboard.press("Enter"); await page.wait_for_timeout(120)
            return True
        except Exception:
            return False

    for s in selectors:
        hit = await _hover_click(s)
        if hit:
            break
    try:
        await page.evaluate("""
            const w = document.querySelector('#z1_profile_menu_wrapper, [id*="profile_menu_wrapper"]');
            if (w) {
                w.setAttribute('aria-hidden','false');
                w.style.display = 'block';
                w.style.opacity = '1';
                w.style.visibility = 'visible';
            }
        """)
    except Exception:
        pass
    try:
        await page.wait_for_selector("a[href*='/signin'], a[href*='/account'], a[href*='/register']", timeout=800)
    except Exception:
        pass
