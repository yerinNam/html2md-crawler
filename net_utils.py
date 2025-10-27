# crawler/net_utils.py
import random
from urllib.parse import urlparse
from typing import Dict, List, Optional

def choose_user_agent(user_agents: List[str]) -> str:
    return random.choice(user_agents)

def group_by_origin(urls: List[str]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for u in urls:
        try:
            p = urlparse(u)
            origin = f"{p.scheme}://{p.netloc}"
        except:
            origin = "misc"
        out.setdefault(origin, []).append(u)
    return out

def looks_like_pdf_url(u: Optional[str]) -> bool:
    if not u: return False
    u = u.lower().split("?", 1)[0]
    return u.endswith(".pdf")

def is_pdf_by_headers(resp) -> bool:
    try:
        h = resp.headers or {}
        ct = (h.get("content-type") or "").lower()
        cd = (h.get("content-disposition") or "").lower()
        if "application/pdf" in ct: return True
        if "attachment" in cd and ".pdf" in cd: return True
    except:
        pass
    return False
