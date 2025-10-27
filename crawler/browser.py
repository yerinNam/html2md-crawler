# crawler/browser.py
import shutil, contextlib, random, asyncio
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Optional, Dict
from .config import Settings
from .net_utils import choose_user_agent

class PagePool:
    def __init__(self, context: BrowserContext, size: int):
        self.context = context
        self.size = size
        self.pool = asyncio.Queue()

    async def init(self):
        for _ in range(self.size):
            p = await self.context.new_page()
            p.set_default_navigation_timeout(30000)
            p.set_default_timeout(10000)
            await self.pool.put(p)

    async def acquire(self) -> Page:
        return await self.pool.get()

    async def release(self, page: Page):
        await self.pool.put(page)

    async def close(self):
        while not self.pool.empty():
            p = await self.pool.get()
            with contextlib.suppress(Exception):
                await p.close()

async def launch_context(pw, cfg: Settings) -> tuple[Optional[Browser], BrowserContext]:
    browser: Optional[Browser] = None

    if cfg.user_agent:
        ua = cfg.user_agent
    elif cfg.randomize_ua:
        ua = choose_user_agent(cfg.user_agents or [])
    else:
        ua = (cfg.user_agents or ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"])[0]

    if cfg.use_profile_copy:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=str(cfg.tmp_profile_dir),
            channel="chrome",
            headless=not cfg.headful,
            args=["--window-size=1366,900","--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
            proxy={"server": cfg.proxy} if cfg.proxy else None,
            locale=cfg.locale,
            timezone_id=cfg.timezone,
            viewport={"width": 1366, "height": 900},
            device_scale_factor=1.25,
            is_mobile=False,
            has_touch=False,
            user_agent=ua,                
        )
    else:
        browser = await pw.chromium.launch(
            channel="chrome",
            headless=not cfg.headful,
            args=["--window-size=1366,900"],
            proxy={"server": cfg.proxy} if cfg.proxy else None,
        )
        context = await browser.new_context(
            storage_state=None,
            viewport={"width": 1366, "height": 900},
            device_scale_factor=1.25,
            is_mobile=False,
            has_touch=False,
            locale=cfg.locale,
            timezone_id=cfg.timezone,
            user_agent=ua,               
        )

    await context.set_extra_http_headers({
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    })
    return browser, context

def guess_default_chrome_profile_win() -> Path:
    import os
    home = Path.home()
    base = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
    return base / "Google" / "Chrome" / "User Data" / "Default"
