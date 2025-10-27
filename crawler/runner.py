# -*- coding: utf-8 -*-
import asyncio
from .config import Settings
from .browser.context import ContextManager
from .pipeline.batches import run_batches

async def run(settings: Settings):
    async with ContextManager(settings) as context:
        await run_batches(context, settings)
