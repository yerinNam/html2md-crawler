# crawler/io_utils.py
import json, os
from pathlib import Path
from itertools import islice
from typing import Dict, List, Iterable, Set

def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def append_jsonl(path: Path, obj: dict):
    ensure_parent(path)
    with path.open("a", encoding="utf-8", newline="\n") as fw:
        fw.write(json.dumps(obj, ensure_ascii=False) + "\n")

def read_urls(path: Path) -> List[str]:
    if not path.exists(): return []
    return [ln.strip() for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip()]

def load_done_urls(*paths: Path) -> Set[str]:
    done = set()
    for p in paths:
        if not p or not p.exists(): continue
        with p.open(encoding="utf-8") as f:
            for ln in f:
                try:
                    o = json.loads(ln)
                    u = o.get("url")
                    if u: done.add(u)
                except: pass
    return done

def chunked(iterable: Iterable, n: int):
    it = iter(iterable)
    while True:
        chunk = list(islice(it, n))
        if not chunk: return
        yield chunk
