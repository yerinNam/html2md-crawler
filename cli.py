# crawler/cli.py
import argparse, asyncio
from pathlib import Path
from .config import default_settings, Settings
from .runner import run_batches

def parse_args():
    ap = argparse.ArgumentParser(description="Playwright batch crawler")
    ap.add_argument("--urls", type=str, help="path to url list")
    ap.add_argument("--ok-html", type=str, help="ok html jsonl path")
    ap.add_argument("--ok-md", type=str, help="ok markdown jsonl path")
    ap.add_argument("--err", type=str, help="err jsonl path")
    ap.add_argument("--proxy", type=str, help="http proxy e.g. http://user:pass@host:port")
    ap.add_argument("--headless", action="store_true", help="run headless")
    ap.add_argument("--concurrency", type=int, default=None)
    ap.add_argument("--origin-concurrency", type=int, default=None)

    ap.add_argument("--user-agent", type=str, help="explicit User-Agent string")
    ap.add_argument("--ua-random", action="store_true", help="use a random UA from config")
    return ap.parse_args()

def build_cfg(args) -> Settings:
    cfg = default_settings()
    if args.urls: cfg.urls_path = Path(args.urls)
    if args.ok_html: cfg.out_ok_html_jsonl = Path(args.ok_html)
    if args.ok_md: cfg.out_ok_md_jsonl = Path(args.ok_md)
    if args.err: cfg.out_err_jsonl = Path(args.err)
    if args.proxy: cfg.proxy = args.proxy
    if args.headless: cfg.headful = False
    if args.concurrency: cfg.concurrency = args.concurrency
    if args.origin_concurrency: cfg.origin_concurrency = args.origin_concurrency

    if args.user_agent:
        cfg.user_agent = args.user_agent
    cfg.randomize_ua = bool(args.ua_random)
    return cfg

def main():
    args = parse_args()
    cfg = build_cfg(args)
    asyncio.run(run_batches(cfg))

if __name__ == "__main__":
    main()
