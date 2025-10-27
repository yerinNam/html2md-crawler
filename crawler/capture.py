# crawler/capture.py
import time, asyncio, contextlib
from urllib.parse import urlparse
from typing import Tuple, Optional, Dict, Any
from playwright.async_api import Page
from .page_ops import normalize_iframes_keep_tags, TARGET_SELECTORS
from .net_utils import is_pdf_by_headers, looks_like_pdf_url

async def goto_and_capture(
    page: Page,
    url: str,
    *,
    nav_timeout=8000,
    sel_timeout=6000,
    retries=2,
    jitter_range=(0.30, 1.10)
) -> Tuple[Optional[str], Dict[str, Any], Optional[int], Optional[str]]:
    timings: Dict[str, Any] = {}
    t0 = time.perf_counter()
    last_err = None

    got_download = {"hit": False}
    def _on_download(d): got_download["hit"] = True
    page.on("download", _on_download)

    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    for _ in range(retries + 1):
        try:
            # origin 방문
            with contextlib.suppress(Exception):
                await page.goto(origin, wait_until="domcontentloaded", timeout=nav_timeout)
                await asyncio.sleep(_rand(*jitter_range))

            # 타겟 이동
            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=min(nav_timeout, 12000), referer=origin)
            except Exception:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=min(nav_timeout, 12000), referer=origin)

            status = resp.status if resp else None
            if status and status >= 500:
                raise RuntimeError(f"http_{status}")

            with contextlib.suppress(Exception):
                await page.wait_for_selector("a[href]", timeout=3000)

            # 다운로드/PDF 차단
            if got_download["hit"]:
                timings["total_ms"] = _ms(t0); return None, timings, status, "blocked_download_attachment"
            if resp and is_pdf_by_headers(resp):
                timings["total_ms"] = _ms(t0); return None, timings, resp.status, "blocked_pdf_content_type"
            with contextlib.suppress(Exception):
                ctype = await page.evaluate("document.contentType || ''")
                if isinstance(ctype, str) and ctype.lower().startswith("application/pdf"):
                    timings["total_ms"] = _ms(t0); return None, timings, status, "blocked_pdf_document"

            # 주요 셀렉터 대기
            sel_or = " || ".join([f"document.querySelector('{s}')" for s in TARGET_SELECTORS])
            try:
                await page.wait_for_function(f"() => {sel_or}", timeout=sel_timeout)
                timings["any_selector_found"] = True
            except:
                timings["any_selector_found"] = False

            # 스크롤 약간
            with contextlib.suppress(Exception):
                await page.evaluate("""
                    const sleep = ms => new Promise(r=>setTimeout(r,ms));
                    for (let i=0;i<2;i++){ window.scrollBy(0, Math.floor(window.innerHeight*0.9)); await sleep(200); }
                    window.scrollTo(0,0);
                """)

            # iframe 보존 HTML 수집
            html = await normalize_iframes_keep_tags(page, max_iframes=40, do_light_scroll=False)
            with contextlib.suppress(Exception):
                iframe_srcs = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('iframe[src]')).map(el => {
                        try { const a = document.createElement('a'); a.href = el.getAttribute('src'); return a.href; } catch(e){ return null; }
                    }).filter(Boolean)
                """)
                timings["iframe_srcs"] = iframe_srcs

            timings["total_ms"] = _ms(t0)
            return html, timings, status, None

        except Exception as e:
            last_err = f"navigate_failed: {e}"
            with contextlib.suppress(Exception):
                html = await page.content()
                if html and html.strip():
                    timings["total_ms"] = _ms(t0)
                    timings["local_error_page"] = True
                    timings["note"] = "nav_error_but_got_content"
                    return html, timings, None, None
            await page.wait_for_timeout(500)
            continue

    try:
        alt = url + ("&" if "?" in url else "?") + "tmpl=component&print=1"
        resp = await page.goto(alt, wait_until="domcontentloaded", timeout=nav_timeout, referer=origin)
        with contextlib.suppress(Exception):
            await page.emulate_media(media="print")
        with contextlib.suppress(Exception):
            await page.wait_for_selector("#print, .print, .print-area, .component-content, article, main, #content", timeout=4000)
        if got_download["hit"] or (resp and is_pdf_by_headers(resp)) or looks_like_pdf_url(alt):
            timings["total_ms"] = _ms(t0); return None, timings, (resp.status if resp else None), "blocked_pdf_fallback"

        html = await normalize_iframes_keep_tags(page, max_iframes=40, do_light_scroll=False)
        timings["total_ms"] = _ms(t0); timings["route"] = "fallback_print_view"
        return html, timings, (resp.status if resp else None), None

    except Exception as e:
        timings["total_ms"] = _ms(t0)
        return None, timings, None, (last_err or f"fallback_failed: {e}")

def _ms(t0: float) -> int:
    import time
    return int((time.perf_counter() - t0) * 1000)

def _rand(a: float, b: float) -> float:
    import random
    return random.uniform(a, b)
