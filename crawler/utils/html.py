# @title ## Specify a URL as input{"run":"auto","vertical-output":true}

import re
import requests
from IPython.display import display, Markdown

# (REMOVE <SCRIPT> to </script> and variations)
SCRIPT_PATTERN = r'<script.*?</script>'
#SCRIPT_PATTERN = r'<[ ]*script.*?\/[ ]*script[ ]*>'  # mach any char zero or more times
# text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))

# (REMOVE HTML <STYLE> to </style> and variations)
STYLE_PATTERN = r'<[ ]*style.*?\/[ ]*style[ ]*>'  # mach any char zero or more times
# text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))

# (REMOVE HTML <META> to </meta> and variations)
META_PATTERN = r'<[ ]*meta.*?>'  # mach any char zero or more times
# text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))

# (REMOVE HTML COMMENTS <!-- to --> and variations)
COMMENT_PATTERN = r'<[ ]*!--.*?--[ ]*>'  # mach any char zero or more times
# text = re.sub(pattern, '', text, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))

# (REMOVE HTML LINK <LINK> to </link> and variations)
LINK_PATTERN = r'<[ ]*link.*?>'  # mach any char zero or more times

# (REPLACE base64 images)
BASE64_IMG_PATTERN = r'<img[^>]+src="data:image/[^;]+;base64,[^"]+"[^>]*>'

# (REPLACE <svg> to </svg> and variations)
SVG_PATTERN = r'(<svg[^>]*>)(.*?)(<\/svg>)'

# <script>...</script> 쌍 먼저 제거
_SCRIPT_PAIR_RE = re.compile(r'(?is)<script\b[^>]*?>.*?</script\s*>')
# 남은 고아(open-only)/self-closing <script ...> 제거
_SCRIPT_ORPHAN_RE = re.compile(r'(?is)<script\b[^>]*?/?>')

def _strip_scripts(html: str) -> str:
    """스크립트 블록을 쌍 → 고아 순서로 반복 제거"""
    prev = None
    while prev != html:
        prev = html
        html = _SCRIPT_PAIR_RE.sub('', html)
    html = _SCRIPT_ORPHAN_RE.sub('', html)
    return html

def replace_svg(html: str, new_content: str = "this is a placeholder") -> str:
    return re.sub(
        SVG_PATTERN,
        lambda match: f"{match.group(1)}{new_content}{match.group(3)}",
        html,
        flags=re.DOTALL,
    )


def replace_base64_images(html: str, new_image_src: str = "#") -> str:
    return re.sub(BASE64_IMG_PATTERN, f'<img src="{new_image_src}"/>', html)


def has_base64_images(text: str) -> bool:
    base64_content_pattern = r'data:image/[^;]+;base64,[^"]+'
    return bool(re.search(base64_content_pattern, text, flags=re.DOTALL))


def has_svg_components(text: str) -> bool:
    return bool(re.search(SVG_PATTERN, text, flags=re.DOTALL))

def clean_html(html: str, clean_svg: bool = False, clean_base64: bool = False):
    # <script>, <style>, <!-- -->, <link> 제거
    #html = re.sub(SCRIPT_PATTERN, '', html, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))
    html = re.sub(STYLE_PATTERN, '', html, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))
    html = re.sub(COMMENT_PATTERN, '', html, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))
    html = re.sub(LINK_PATTERN, '', html, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))
    html = _strip_scripts(html)

    # <meta> 태그 처리: published_time만 남기고 삭제
    def _filter_meta(match):
        tag = match.group(0)
        if re.search(r'property=["\']article:published_time["\']', tag, flags=re.IGNORECASE):
            return tag  # 그대로 둠
        return ''  

    html = re.sub(META_PATTERN, _filter_meta, html, flags=re.IGNORECASE)

    if clean_svg:
        html = replace_svg(html)

    if clean_base64:
        html = replace_base64_images(html)

    return html



from bs4 import BeautifulSoup
from urllib.parse import urljoin
from bs4.element import Tag
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin


LAZY_SRC_KEYS = ("data-org-src", "data-src", "data-original", "data-lazy-src", "data-url", "data-image")
LAZY_SRCSET_KEYS = ("data-srcset", "data-lazy-srcset")

def prepare_html_for_markdown(html_content: str, base_url: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    # --- 2) <img> 처리 (lazy, src/srcset, 속성 정리, 절대경로화) ---
    for img in soup.find_all("img"):
        # (a) lazy 속성 우선순위로 src 승격 (data-org-src가 있으면 가장 우선)
        src = (img.get("src") or "").strip()
        if (not src or src.startswith("data:")):
            for key in LAZY_SRC_KEYS:
                val = (img.get(key) or "").strip()
                if val:
                    src = val
                    img["src"] = src
                    break

        # (b) srcset도 lazy 버전이 있으면 옮기기
        if not img.get("srcset"):
            for key in LAZY_SRCSET_KEYS:
                val = (img.get(key) or "").strip()
                if val:
                    img["srcset"] = val
                    break

        # (c) src 절대경로화
        if src and not src.startswith(("http://", "https://", "data:")):
            img["src"] = urljoin(base_url, src)

        # (d) srcset 내 URL 절대경로화
        if img.get("srcset"):
            parts = []
            for cand in img["srcset"].split(","):
                cand = cand.strip()
                if not cand:
                    continue
                tokens = cand.split()
                if tokens:
                    u = tokens[0]
                    rest = " ".join(tokens[1:])
                    if not u.startswith(("http://", "https://", "data:")):
                        u = urljoin(base_url, u)
                    parts.append(u + ((" " + rest) if rest else ""))
            if parts:
                img["srcset"] = ", ".join(parts)

        # (e) 마크다운 변환에 불필요한 속성 제거
        attrs_to_remove = [
            "width", "height", "title", "class", "style", "loading", "decoding",
            "data-org-width", "data-org-height", "dmcf-mid", "dmcf-mtype",
            *LAZY_SRC_KEYS, *LAZY_SRCSET_KEYS
        ]
        for attr in attrs_to_remove:
            if attr in img.attrs:
                del img[attr]

    # --- 3) <a> 처리 (href 보정/절대경로화) ---
    for a in soup.find_all("a"):
        href = (a.get("href") or "").strip()
        if not href:
            a["href"] = base_url
            continue
        if not href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            a["href"] = urljoin(base_url, href)

    return str(soup)

def make_img_converter():

    counter = {"n": 0}
    def _converter(*, tag: Tag, **kwargs) -> str:
        counter["n"] += 1
        alt = (tag.get("alt") or "").strip()
        src = (tag.get("src") or "").strip()
        if not src:
            return ""
        if alt:
            return f"![Image {counter['n']}: {alt}]({src})"
        else:
            return f"![Image {counter['n']}]({src})"
    return _converter

def custom_a_converter(*, tag: Tag, text: str, **kwargs) -> str:
    href = (tag.get("href") or "").strip()
    content = (text or "").strip()  # ← 자식 태그(예: <img>)가 이미 변환된 마크다운

    # href가 없으면 링크로 만들지 않고 내용만 반환
    if not href:
        return content

    if content:
        clean_content = re.sub(r'\s+', ' ', content).strip() 
        return f"[{clean_content}]({href})"
    
    # content가 비어있다면, 직접 <img> 태그를 찾아서 만들어 주기
    img = tag.find("img")
    if img and img.get("src"):
        alt = (img.get("alt") or "").strip()
        src = (img.get("src") or "").strip()
        inner = f"![{alt}]({src})" if alt else f"![Image]({src})"
        return f"[{inner}]({href})"

    # 이미지도 없고 텍스트만 있는 순수 앵커일 때
    label = tag.get_text(strip=True) or href
    return f"[{label}]({href})"


from bs4 import BeautifulSoup, Tag
from typing import cast

def custom_li_converter(*, tag: Tag, text: str, convert_as_inline: bool = False, **kwargs) -> str:
    ## 기존 함수인데 가지고 온 bullet과 list_indent_str
    bullets = kwargs.get("bullets", ("*",))  # ← 튜플이어야 함! ("*",)도 OK
    list_indent_type = kwargs.get("list_indent_type", "spaces")
    list_indent_width = kwargs.get("list_indent_width", 4)
    list_indent_str = kwargs.get(
        "list_indent_str",
        "\t" if list_indent_type == "tabs" else " " * list_indent_width
    )


    checkbox = tag.find("input", {"type": "checkbox"})
    if checkbox and isinstance(checkbox, Tag):
        checked = checkbox.get("checked") is not None
        checkbox_symbol = "[x]" if checked else "[ ]"
        return f"- {checkbox_symbol} {(text or '').strip()}\n"

    parent = tag.parent
    if parent is not None and parent.name == "ol":
        start = (
            int(cast("str", parent.get("start")))
            if isinstance(parent.get("start"), str) and str(parent.get("start")).isnumeric()
            else 1
        )
        bullet = f"{start + parent.index(tag)}."
    else:
        depth = -1
        t = tag
        while t:
            if getattr(t, "name", None) == "ul":
                depth += 1
            if not getattr(t, "parent", None):
                break
            t = t.parent
        bullet = bullets[depth % len(bullets)] if bullets else "-"

    has_block_children = "\n\n" in (text or "")

    if has_block_children:
        paragraphs = (text or "").strip().split("\n\n")
        
        if paragraphs:
            result_parts = [f"{bullet} {paragraphs[0].strip()}\n"]

            for para in paragraphs[1:]:
                if para.strip():
                    for line in para.strip().split("\n"):
                        line = " ".join(line.split()) ## 바뀐 부분 => 정규화 추가함
                        if line:
                            result_parts.append(f"\n{list_indent_str}{line}\n")
            return "".join(result_parts)

    return f"\n\n{bullet} {' '.join((text or '').split())}\n"


from html_to_markdown import convert_to_markdown 
from pathlib import Path
from urllib.parse import urlparse

CONSENT_BUTTON_XP = [
    "//button[contains(., '동의')]",
    "//button[contains(., '허용')]",
    "//button[contains(., 'Accept')]",
    "//button[contains(., 'Agree')]",
]

def html_to_markdown_with_prep(html: str, url: str) -> str:
    html_fixed = prepare_html_for_markdown(html, url)
    md = convert_to_markdown(
        html_fixed,
        strip=['svg'],
        heading_style="atx",
        whitespace_mode='strict',
        remove_navigation=False,
        remove_forms=False,
        preprocess_html=True,
        preprocessing_preset="standard",
        escape_misc=False,
        custom_converters={
            "img": make_img_converter(),
            "a": custom_a_converter,
            "li": custom_li_converter,
        },
    )
    md = md.replace('this is a placeholder', '')
    return md


def read_urls(txt_path: str | Path) -> list[str]:
    urls = []
    for line in Path(txt_path).read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        pu = urlparse(s)
        if pu.scheme in ("http", "https") and pu.netloc:
            urls.append(s)
        else:
            print(f"⚠️  무시: 올바르지 않은 URL 형식 -> {s!r}")
    return urls

async def click_consent(page):
    for xp in CONSENT_BUTTON_XP:
        try:
            btn = await page.wait_for_selector(f"xpath={xp}", timeout=2000)
            if btn:
                await btn.click()
                await page.wait_for_timeout(500)
        except Exception:
            pass