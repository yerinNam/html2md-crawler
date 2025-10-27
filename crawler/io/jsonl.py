# -*- coding: utf-8 -*-
import json
from pathlib import Path
from .paths import ensure_parent

def append_jsonl(path: Path, obj: dict):
    ensure_parent(path)
    with path.open("a", encoding="utf-8", newline="\n") as fw:
        fw.write(json.dumps(obj, ensure_ascii=False) + "\n")

def load_done_urls(*paths: Path) -> set[str]:
    done = set()
    for p in paths:
        if not p or not p.exists(): continue
        with p.open(encoding="utf-8") as f:
            for ln in f:
                try:
                    obj = json.loads(ln)
                    if "url" in obj: done.add(obj["url"])
                except: pass
    return done
