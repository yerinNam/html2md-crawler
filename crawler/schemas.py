# -*- coding: utf-8 -*-
from typing import TypedDict, Optional, List

class Timings(TypedDict, total=False):
    total_ms: int
    prewarm_ms: int
    route: str
    any_selector_found: bool
    iframe_srcs: List[str]
    local_error_page: bool
    note: str

class CaptureResult(TypedDict, total=False):
    url: str
    clean_html: str
    markdown: str
    status: Optional[int]
    timings: Timings
    error: Optional[str]
