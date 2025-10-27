# -*- coding: utf-8 -*-
import asyncio, random
from urllib.parse import urlparse
from typing import Dict, List
from playwright.async_api import BrowserContext
from ..browser.page_pool import PagePool
from ..io.jsonl import append_jsonl, load_done_urls
from ..io.urlio import read_urls, group_by_origin, chunked
from ..utils.html import clean_html, html_to_markdown_with_prep
from ..config import Settings
from .capture import CapturePipeline
from ..nav.prewarm import prewarm_origin
from ..nav.captcha import ensure_solved_for_origin

async def run_batches(context: BrowserContext, settings: Settings):
    urls_all = read_urls(settings.urls_path)
    done = load_done_urls(settings.out_ok_html, settings.out_ok_md, settings.out_err)
    urls_all = [u for u in urls_all if u not in done]
    if not urls_all:
        print("모든 URL이 이미 처리됨")
        return

    buckets = group_by_origin(urls_all)
    origins_all = sorted([o for o in buckets.keys() if o not in ("misc","")])
    misc_urls = buckets.get("misc", [])

    origin_semaphores: Dict[str, asyncio.Semaphore] = {
        o: asyncio.Semaphore(settings.origin_concurrency) for o in origins_all
    }

    cap = CapturePipeline(settings)

    async def run_one(page_pool: PagePool, u: str, idx: int, total: int):
        page = await page_pool.acquire()
        try:
            html, timings, status, err = await cap.goto_and_capture(page, u)
            if html and not err:
                html_clean = clean_html(html)
                try:
                    md = html_to_markdown_with_prep(html_clean, u)
                except Exception as e:
                    md = ""
                    print(f"[WARN] Markdown 변환 실패: {e}")
                append_jsonl(settings.out_ok_html, {"url": u, "clean_html": html_clean})
                append_jsonl(settings.out_ok_md,   {"url": u, "markdown": md, "timings": timings})
                badge = "✅"
            else:
                clean, md = "", ""
                if html:
                    clean = clean_html(html)
                    try:
                        md = html_to_markdown_with_prep(clean, u)
                    except Exception as e:
                        print(f"[WARN] (ERR) Markdown 변환 실패: {e}")
                append_jsonl(settings.out_err, {
                    "url": u, "clean_html": clean, "markdown": md,
                    "status": status, "timings": timings, "error": err or "unknown_error"
                })
                badge = "☠️"
            ms = (timings or {}).get("total_ms")
            print(f"{badge} {idx}/{total} | {u}" + (f" | {ms} ms" if ms else ""))
        finally:
            await page_pool.release(page)

    for batch_idx, origin_batch in enumerate(chunked(origins_all, settings.prewarm_batch_size), 1):
        print(f"[INFO] === Batch {batch_idx}: {len(origin_batch)} origins ===")

        if settings.headful:
            for origin in origin_batch:
                try:
                    await ensure_solved_for_origin(context, origin, prompt_for_manual=True, headful=settings.headful)
                except Exception as e:
                    print(f"[WARN] ensure_solved_for_origin failed for {origin}: {e}")

        if settings.prewarm_enable:
            await asyncio.gather(*(prewarm_origin(context, o, settings.prewarm_wait_ms_headful, settings.prewarm_wait_ms_headless, settings.headful, settings.prewarm_nav_timeout_ms) for o in origin_batch))

        urls_batch: List[str] = []
        for o in origin_batch:
            for u in buckets[o]:
                if u not in done:
                    urls_batch.append(u)
        print(f"[INFO] Batch {batch_idx}: crawl {len(urls_batch)} urls")

        sem_global = asyncio.Semaphore(settings.concurrency)
        page_pool = PagePool(context, size=settings.concurrency)
        await page_pool.init()

        async def runner(i, u, total):
            parsed = urlparse(u)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            sem_origin = origin_semaphores.get(origin, asyncio.Semaphore(1))
            async with sem_global, sem_origin:
                await asyncio.sleep(random.uniform(*settings.jitter_range))
                await run_one(page_pool, u, i, total)
                done.add(u)

        tasks = [runner(i, u, len(urls_batch)) for i, u in enumerate(urls_batch, 1)]
        if tasks:
            await asyncio.gather(*tasks)
        await page_pool.close()

    if misc_urls:
        misc_urls = [u for u in misc_urls if u not in done]
        print(f"[INFO] === misc crawl {len(misc_urls)} urls ===")
        sem_global = asyncio.Semaphore(settings.concurrency)
        sem_misc = asyncio.Semaphore(settings.origin_concurrency)

        page_pool = PagePool(context, size=settings.concurrency)
        await page_pool.init()

        async def runner(i, u, total):
            async with sem_global, sem_misc:
                await asyncio.sleep(random.uniform(*settings.jitter_range))
                await run_one(page_pool, u, i, total)
                done.add(u)

        tasks = [runner(i, u, len(misc_urls)) for i, u in enumerate(misc_urls, 1)]
        if tasks:
            await asyncio.gather(*tasks)
        await page_pool.close()
