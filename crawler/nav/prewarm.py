# -*- coding: utf-8 -*-
import time, contextlib
from playwright.async_api import BrowserContext

async def prewarm_origin(context: BrowserContext, origin: str, wait_ms_headful=300, wait_ms_headless=150, headful=True, nav_timeout_ms=12_000) -> dict:
    timings = {}
    page = await context.new_page()
    page.set_default_navigation_timeout(nav_timeout_ms)
    page.set_default_timeout(8000)
    t0 = time.perf_counter()
    try:
        await page.goto(origin, wait_until="domcontentloaded", timeout=nav_timeout_ms)
        await page.wait_for_timeout(wait_ms_headful if headful else wait_ms_headless)
    except Exception:
        pass
    timings["prewarm_ms"] = int((time.perf_counter() - t0) * 1000)
    with contextlib.suppress(Exception):
        await page.close()
    return timings
