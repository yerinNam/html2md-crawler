# -*- coding: utf-8 -*-
def looks_like_pdf_url(u: str | None) -> bool:
    if not u:
        return False
    u = u.lower().split("?", 1)[0]
    return u.endswith(".pdf")

def is_pdf_by_headers(resp) -> bool:
    try:
        h = resp.headers or {}
        ct = (h.get("content-type") or "").lower()
        cd = (h.get("content-disposition") or "").lower()
        if "application/pdf" in ct:
            return True
        if "attachment" in cd and ".pdf" in cd:
            return True
    except Exception:
        pass
    return False
