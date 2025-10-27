# -*- coding: utf-8 -*-
import asyncio, contextlib
from playwright.async_api import BrowserContext, Page

class PagePool:
    def __init__(self, context: BrowserContext, size: int):
        self.context = context
        self.size = size
        self.pool = asyncio.Queue()

    async def init(self):
        for _ in range(self.size):
            p = await self.context.new_page()
            p.set_default_navigation_timeout(30_000)
            p.set_default_timeout(10_000)
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
