# -*- coding: utf-8 -*-
import time, contextlib
from playwright.async_api import Page, BrowserContext

CAPTCHA_SELECTORS = [
    "iframe[src*='cloudflare']",
    "div[class*='cf-challenge']",
    "div[class*='cf-turnstile']",
    "div[id*='challenge-stage']",
    "text=사람인지 확인",
    "text=Please verify you are human",
    "text=Just a moment",
    "text=Attention Required",
]

async def is_captcha_page(page: Page) -> bool:
    try:
        for s in CAPTCHA_SELECTORS:
            el = await page.query_selector(s)
            if el: return True
        title = (await page.title()) or ""
        lowt = title.lower()
        if any(k in lowt for k in ["verify", "attention required", "just a moment", "cloudflare"]):
            return True
        ctype = await page.evaluate("document.contentType || ''")
        if isinstance(ctype, str) and "cf-challenge" in ctype.lower():
            return True
    except Exception:
        pass
    return False

async def ensure_solved_for_origin(context: BrowserContext, origin: str, prompt_for_manual: bool=True, headful: bool=True, max_wait_ms: int = 120_000):
    page = await context.new_page()
    try:
        await page.goto(origin, wait_until="domcontentloaded", timeout=30_000)
        has_captcha = await is_captcha_page(page)
        if has_captcha and prompt_for_manual and headful:
            print(f"[ACTION] Solve CAPTCHA for: {origin}\n브라우저 창에서 사람인증을 완료한 뒤 콘솔에 Enter.")
            try:
                input()
            except KeyboardInterrupt:
                return False
        start = time.perf_counter()
        while True:
            await page.wait_for_timeout(800)
            solved = not (await is_captcha_page(page))
            if solved: break
            if (time.perf_counter() - start) * 1000 > max_wait_ms:
                print(f"[WARN] CAPTCHA still present on {origin} after wait. Continue anyway.")
                break
        return True
    finally:
        with contextlib.suppress(Exception):
            await page.close()
