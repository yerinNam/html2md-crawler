# -*- coding: utf-8 -*-
import shutil
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, BrowserContext, Browser
from ..config import Settings
from .profiles import guess_default_chrome_profile_win
from ..constants import BLOCK_DOMAIN_SUBSTR
from .routing import setup_speed_routes

class ContextManager:
    def __init__(self, settings: Settings):
        self.s = settings
        self.play = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def __aenter__(self):
        self.play = await async_playwright().start()

        if self.s.use_profile_copy:
            src: Path = self.s.src_profile or guess_default_chrome_profile_win()
            if not src.exists():
                raise FileNotFoundError(f"Chrome profile not found: {src}")
            if self.s.tmp_profile_dir.exists():
                shutil.rmtree(self.s.tmp_profile_dir)
            shutil.copytree(src, self.s.tmp_profile_dir)

            self.context = await self.play.chromium.launch_persistent_context(
                user_data_dir=str(self.s.tmp_profile_dir),
                channel="chrome",
                headless=not self.s.headful,
                args=["--window-size=1366,900", "--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
                proxy=self.s.proxy,
                locale=self.s.locale,
                timezone_id=self.s.timezone,
                viewport={"width":1366, "height":900},
                device_scale_factor=1.25,
                is_mobile=False,
                has_touch=False,
            )
        else:
            self.browser = await self.play.chromium.launch(
                channel="chrome",
                headless=not self.s.headful,
                args=["--window-size=1366,900"],
                proxy=self.s.proxy
            )
            self.context = await self.browser.new_context(
                viewport={"width":1366, "height":900},
                device_scale_factor=1.25,
                is_mobile=False,
                has_touch=False,
                locale=self.s.locale,
                timezone_id=self.s.timezone,
            )

        await self.context.set_extra_http_headers({
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        await setup_speed_routes(self.context, BLOCK_DOMAIN_SUBSTR)
        return self.context

    async def __aexit__(self, exc_type, exc, tb):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.play:
            await self.play.stop()
