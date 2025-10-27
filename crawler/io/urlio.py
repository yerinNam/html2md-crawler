# -*- coding: utf-8 -*-
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Dict, Iterable
from .paths import ensure_parent
from itertools import islice

def read_urls(path: Path) -> List[str]:
    if not path.exists(): return []
    return [ln.strip() for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip()]

def group_by_origin(urls: List[str]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for u in urls:
        try:
            p = urlparse(u); origin = f"{p.scheme}://{p.netloc}"
        except Exception:
            origin = "misc"
        out.setdefault(origin, []).append(u)
    return out

def chunked(iterable: Iterable, n: int):
    it = iter(iterable)
    while True:
        chunk = list(islice(it, n))
        if not chunk: return
        yield chunk
