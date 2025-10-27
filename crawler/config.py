# -*- coding: utf-8 -*-
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

@dataclass
class Settings:
    urls_path: Path
    out_ok_html: Path
    out_ok_md: Path
    out_err: Path

    headful: bool = True
    proxy: Optional[dict] = None  # playwright proxy dict or None
    concurrency: int = 4
    origin_concurrency: int = 1
    jitter_range: Tuple[float, float] = (0.30, 1.10)

    use_profile_copy: bool = True
    src_profile: Optional[Path] = None
    tmp_profile_dir: Path = Path("./tmp_chrome_profile")

    locale: str = "ko-KR"
    timezone: str = "Asia/Seoul"

    prewarm_enable: bool = True
    prewarm_batch_size: int = 50
    prewarm_nav_timeout_ms: int = 12_000
    prewarm_wait_ms_headful: int = 300
    prewarm_wait_ms_headless: int = 150

def load_default_settings() -> Settings:
    return Settings(
        urls_path=Path(r"D:\compare_random.txt"),
        out_ok_html=Path(r"D:\ye\test\ok_html_err.jsonl"),
        out_ok_md=Path(r"D:\ye\test\ok_markdown_err.jsonl"),
        out_err=Path(r"D:\ye\test\err_err.jsonl"),
    )
