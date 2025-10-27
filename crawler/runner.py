# crawler/runner.py
import asyncio, contextlib, random
from typing import Dict, Set, List, Optional
from urllib.parse import urlparse

from playwright.async_api import async_playwright
from .config import Settings
from .io_utils import append_jsonl, read_urls, load_done_urls, chunked
from .net_utils import group_by_origin
from .browser import launch_context, PagePool
from .captcha import ensure_solved_for_origin
from .capture import goto_and_capture
from .md_utils import clean_html, html_to_markdown_with_prep  

async def run_once_with_pool(page_pool: PagePool, url: str, idx: int, total: int, cfg: Settings):
    page = await page_pool.acquire()
    try:
        html, timings, status, err = await goto_and_capture(page, url)

        if html and not err:
            html_clean = clean_html(html)
            try:
                md = html_to_markdown_with_prep(html_clean, url)
            except Exception as e:
                md = ""
                print(f"[WARN] Markdown 변환 실패: {e}")

            append_jsonl(cfg.out_ok_html_jsonl, {"url": url, "clean_html": html_clean})
            append_jsonl(cfg.out_ok_md_jsonl,   {"url": url, "markdown": md, "timings": timings})
            badge = "✅"
        else:
            clean = ""
            md = ""
            if html:
                clean = clean_html(html)
                try:
                    md = html_to_markdown_with_prep(clean, url)
                except Exception as e:
                    md = ""
                    print(f"[WARN] (ERR) Markdown 변환 실패: {e}")
            append_jsonl(cfg.out_err_jsonl, {
                "url": url, "clean_html": clean, "markdown": md,
                "status": status, "timings": timings, "error": err or "unknown_error",
            })
            badge = "☠️"

        ms = (timings or {}).get("total_ms")
        print(f"{badge} {idx}/{total} | {url}" + (f" | {ms} ms" if ms else ""))

    except Exception as e:
        append_jsonl(cfg.out_err_jsonl, {
            "url": url, "clean_html": "", "markdown": "",
            "status": None, "timings": {}, "error": f"run_once_exception | {type(e).__name__}: {e}",
        })
        print(f"☠️ {idx}/{total} | {url} | run_once_exception: {type(e).__name__}: {e}")
    finally:
        with contextlib.suppress(Exception):
            await page_pool.release(page)

async def run_batches(cfg: Settings):
    urls_all = read_urls(cfg.urls_path)
    done = load_done_urls(cfg.out_ok_html_jsonl, cfg.out_ok_md_jsonl, cfg.out_err_jsonl)
    urls_all = [u for u in urls_all if u not in done]
    if not urls_all:
        print("모든 URL이 이미 처리됨"); return

    async with async_playwright() as pw:
        browser, context = await launch_context(pw, cfg)

        buckets = group_by_origin(urls_all)
        origins_all = sorted([o for o in buckets.keys() if o not in ("misc", "")])
        misc_urls = buckets.get("misc", [])

        origin_semaphores: Dict[str, asyncio.Semaphore] = {
            o: asyncio.Semaphore(cfg.origin_concurrency) for o in origins_all
        }

        for batch_idx, origin_batch in enumerate(chunked(origins_all, cfg.prewarm_batch_size), 1):
            print(f"[INFO] === Batch {batch_idx}: {len(origin_batch)} origins ===")

            if cfg.headful:
                for origin in origin_batch:
                    try:
                        await ensure_solved_for_origin(context, origin, prompt_for_manual=True, headful=cfg.headful)
                    except Exception as e:
                        print(f"[WARN] ensure_solved_for_origin failed for {origin}: {e}")

            if cfg.prewarm_enable:
                await asyncio.gather(*(prewarm_origin(context, o, cfg) for o in origin_batch))

            urls_batch = []
            for o in origin_batch:
                for u in buckets[o]:
                    if u not in done:
                        urls_batch.append(u)

            print(f"[INFO] Batch {batch_idx}: crawl {len(urls_batch)} urls")
            sem_global = asyncio.Semaphore(cfg.concurrency)
            page_pool = PagePool(context, size=cfg.concurrency)
            await page_pool.init()

            async def runner(i, u, total):
                parsed = urlparse(u)
                origin = f"{parsed.scheme}://{parsed.netloc}"
                sem_origin = origin_semaphores.get(origin, asyncio.Semaphore(1))
                async with sem_global, sem_origin:
                    await asyncio.sleep(random.uniform(*cfg.jitter_range))
                    await run_once_with_pool(page_pool, u, i, total, cfg)
                    done.add(u)

            tasks = [runner(i, u, len(urls_batch)) for i, u in enumerate(urls_batch, 1)]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=False)

            await page_pool.close()

        if misc_urls:
            remain = [u for u in misc_urls if u not in done]
            print(f"[INFO] === misc crawl {len(remain)} urls ===")
            sem_global = asyncio.Semaphore(cfg.concurrency)
            sem_misc = asyncio.Semaphore(cfg.origin_concurrency)
            page_pool = PagePool(context, size=cfg.concurrency)
            await page_pool.init()

            async def runner_misc(i, u, total):
                async with sem_global, sem_misc:
                    await asyncio.sleep(random.uniform(*cfg.jitter_range))
                    await run_once_with_pool(page_pool, u, i, total, cfg)

            tasks = [runner_misc(i, u, len(remain)) for i, u in enumerate(remain, 1)]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=False)
            await page_pool.close()

        await context.close()
        if browser:
            await browser.close()

async def prewarm_origin(context, origin: str, cfg: Settings):
    page = await context.new_page()
    page.set_default_navigation_timeout(cfg.prewarm_nav_timeout_ms)
    page.set_default_timeout(8000)
    try:
        await page.goto(origin, wait_until="domcontentloaded", timeout=cfg.prewarm_nav_timeout_ms)
        await page.wait_for_timeout(cfg.prewarm_wait_ms_headful if cfg.headful else cfg.prewarm_wait_ms_headless)
    except Exception:
        pass
    finally:
        with contextlib.suppress(Exception):
            await page.close()
