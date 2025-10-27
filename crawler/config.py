# crawler/config.py
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, List

@dataclass
class Settings:
    urls_path: Path
    out_ok_html_jsonl: Path
    out_ok_md_jsonl: Path
    out_err_jsonl: Path

    headful: bool = True
    proxy: Optional[str] = None
    concurrency: int = 4
    origin_concurrency: int = 1
    jitter_range: Tuple[float, float] = (0.30, 1.10)

    use_profile_copy: bool = False
    src_profile: Optional[Path] = None
    tmp_profile_dir: Path = Path("./tmp_chrome_profile")

    user_agent: Optional[str] = None 

    locale: str = "ko-KR"
    timezone: str = "Asia/Seoul"
    user_agents: List[str] = None
    randomize_ua: bool = False 

    prewarm_enable: bool = True
    prewarm_batch_size: int = 50
    prewarm_nav_timeout_ms: int = 12000
    prewarm_wait_ms_headful: int = 300
    prewarm_wait_ms_headless: int = 150

def default_settings() -> Settings:
    return Settings(
        urls_path=Path(r"D.\compare_random.txt"),
        out_ok_html_jsonl=Path(r".\ok_html.jsonl"),
        out_ok_md_jsonl=Path(r".\ok_markdown.jsonl"),
        out_err_jsonl=Path(r".\err.jsonl"),
        user_agents=[
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
        ],
    )
