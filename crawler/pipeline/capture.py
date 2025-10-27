# -*- coding: utf-8 -*-
import time, random, contextlib, re
from urllib.parse import urlparse
from playwright.async_api import Page
from ..schemas import Timings
from ..constants import TARGET_SELECTORS
from ..extract.pdf import looks_like_pdf_url, is_pdf_by_headers
from ..nav.waits import wait_rendering, deep_scroll_until_stable, wait_for_web_components, open_common_menus
from ..nav.consent import click_consent
from ..nav.captcha import is_captcha_page
from ..extract.iframe import normalize_iframes_keep_tags
from ..config import Settings

class CapturePipeline:
    def __init__(self, settings: Settings):
        self.s = settings

    async def goto_and_capture(self, page: Page, url: str, retries: int = 2):
        timings: Timings = {}
        t0 = time.perf_counter()

        got_download = {"hit": False}
        page.on("download", lambda d: got_download.update(hit=True))

        parsed = urlparse(url); origin = f"{parsed.scheme}://{parsed.netloc}"
        last_err = None

        for attempt in range(retries + 1):
            try:
                if looks_like_pdf_url(url):
                    timings["total_ms"] = int((time.perf_counter()-t0)*1000)
                    return None, timings, None, "blocked_pdf_url"

                with contextlib.suppress(Exception):
                    await page.goto(origin, wait_until="domcontentloaded", timeout=12_000)
                await page.wait_for_timeout(int(random.uniform(*self.s.jitter_range)*1000))

                resp = await page.goto(url, wait_until="domcontentloaded", timeout=12_000, referer=origin)
                status = resp.status if resp else None
                if status and status >= 500:
                    raise RuntimeError(f"http_{status}")

                with contextlib.suppress(Exception):
                    await page.wait_for_selector("a[href]", timeout=5000)

                if got_download["hit"]:
                    timings["total_ms"] = int((time.perf_counter()-t0)*1000)
                    return None, timings, status, "blocked_download_attachment"
                if resp and is_pdf_by_headers(resp):
                    timings["total_ms"] = int((time.perf_counter()-t0)*1000)
                    return None, timings, status, "blocked_pdf_content_type"

                html = await normalize_iframes_keep_tags(page, max_iframes=40, do_light_scroll=False)
                text_only = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\\1>", "", html)
                text_only = re.sub(r"(?is)<[^>]+>", "", text_only).strip()
                if len(text_only) < 50:
                    with contextlib.suppress(Exception):
                        await page.reload(wait_until="domcontentloaded", timeout=12_000)

                with contextlib.suppress(Exception):
                    ctype = await page.evaluate("document.contentType || ''")
                    if isinstance(ctype, str) and ctype.lower().startswith("application/pdf"):
                        timings["total_ms"] = int((time.perf_counter()-t0)*1000)
                        return None, timings, status, "blocked_pdf_document"

                sel_or = " || ".join([f"document.querySelector('{s}')" for s in TARGET_SELECTORS])
                with contextlib.suppress(Exception):
                    ok = await page.wait_for_function(f"() => {sel_or}", timeout=8000)
                    timings["any_selector_found"] = bool(ok)

                with contextlib.suppress(Exception):
                    await page.evaluate("""
                      const sleep = ms => new Promise(r=>setTimeout(r,ms));
                      for (let i=0;i<2;i++){ window.scrollBy(0, Math.floor(window.innerHeight*0.9)); await sleep(200); }
                      window.scrollTo(0,0);
                    """)
                await deep_scroll_until_stable(page, max_secs=2)
                await wait_rendering(page)
                await wait_for_web_components(page)
                await click_consent(page)
                await open_common_menus(page)

                html = await normalize_iframes_keep_tags(page, max_iframes=40, do_light_scroll=False)
                timings["total_ms"] = int((time.perf_counter()-t0)*1000)
                return html, timings, status, None

            except Exception as e:
                last_err = f"navigate_failed: {e}"
                with contextlib.suppress(Exception):
                    html = await page.content()
                    if html and html.strip():
                        timings["total_ms"] = int((time.perf_counter()-t0)*1000)
                        timings["local_error_page"] = True
                        timings["note"] = "nav_error_but_got_content"
                        return html, timings, None, None

        try:
            alt = url + ("&" if "?" in url else "?") + "tmpl=component&print=1"
            resp = await page.goto(alt, wait_until="domcontentloaded", timeout=12_000, referer=origin)
            with contextlib.suppress(Exception):
                await page.emulate_media(media="print")
            await wait_rendering(page)
            await deep_scroll_until_stable(page, max_secs=4)
            html = await normalize_iframes_keep_tags(page, max_iframes=40, do_light_scroll=False)
            timings["total_ms"] = int((time.perf_counter()-t0)*1000)
            timings["route"] = "fallback_print_view"
            return html, timings, (resp.status if resp else None), None
        except Exception as e:
            timings["total_ms"] = int((time.perf_counter()-t0)*1000)
            return None, timings, None, (last_err or f"fallback_failed: {e}")
