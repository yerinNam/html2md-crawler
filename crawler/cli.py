# -*- coding: utf-8 -*-
import argparse
from pathlib import Path
from .config import Settings, load_default_settings

def parse_args():
    ap = argparse.ArgumentParser(description="Playwright batch crawler")
    ap.add_argument("--urls", type=str)
    ap.add_argument("--ok-html", type=str)
    ap.add_argument("--ok-md", type=str)
    ap.add_argument("--err", type=str)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--concurrency", type=int, default=None)
    ap.add_argument("--origin-concurrency", type=int, default=None)
    ap.add_argument("--proxy", type=str, help="http://user:pass@host:port")
    return ap.parse_args()

def build_settings_from_args() -> Settings:
    s = load_default_settings()
    args = parse_args()
    if args.urls: s.urls_path = Path(args.urls)
    if args.ok_html: s.out_ok_html = Path(args.ok_html)
    if args.ok_md: s.out_ok_md = Path(args.ok_md)
    if args.err: s.out_err = Path(args.err)
    if args.headless: s.headful = False
    if args.concurrency is not None: s.concurrency = args.concurrency
    if args.origin_concurrency is not None: s.origin_concurrency = args.origin_concurrency
    if args.proxy:
        s.proxy = {"server": args.proxy}
    return s
