# -*- coding: utf-8 -*-
from playwright.async_api import BrowserContext

async def setup_speed_routes(context: BrowserContext, blocked_substrings):
    async def handler(route, request):
        rtype = (request.resource_type or "").lower()
        url   = request.url.lower()

        if rtype in ("image", "media", "font"):
            return await route.abort()

        if any(b in url for b in blocked_substrings):
            return await route.abort()

        return await route.continue_()
    await context.route("**/*", handler)
