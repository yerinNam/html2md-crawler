# crawler/md_utils.py

import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from bs4.element import Tag
from typing import cast
from html_to_markdown import convert_to_markdown 
from pathlib import Path

SCRIPT_PATTERN = r'<script.*?</script>'
STYLE_PATTERN = r'<[ ]*style.*?\/[ ]*style[ ]*>' 
META_PATTERN = r'<[ ]*meta.*?>'
COMMENT_PATTERN = r'<[ ]*!--.*?--[ ]*>'  
LINK_PATTERN = r'<[ ]*link.*?>' 
BASE64_IMG_PATTERN = r'<img[^>]+src="data:image/[^;]+;base64,[^"]+"[^>]*>'
SVG_PATTERN = r'(<svg[^>]*>)(.*?)(<\/svg>)'

_SCRIPT_PAIR_RE = re.compile(r'(?is)<script\b[^>]*?>.*?</script\s*>')
_SCRIPT_ORPHAN_RE = re.compile(r'(?is)<script\b[^>]*?/?>')

def _strip_scripts(html: str) -> str:
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
    html = re.sub(STYLE_PATTERN, '', html, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))
    html = re.sub(COMMENT_PATTERN, '', html, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))
    html = re.sub(LINK_PATTERN, '', html, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))
    html = _strip_scripts(html)

    def _filter_meta(match):
        tag = match.group(0)
        if re.search(r'property=["\']article:published_time["\']', tag, flags=re.IGNORECASE):
            return tag
        return ''  

    html = re.sub(META_PATTERN, _filter_meta, html, flags=re.IGNORECASE)

    if clean_svg:
        html = replace_svg(html)

    if clean_base64:
        html = replace_base64_images(html)

    return html


LAZY_SRC_KEYS = ("data-org-src", "data-src", "data-original", "data-lazy-src", "data-url", "data-image")
LAZY_SRCSET_KEYS = ("data-srcset", "data-lazy-srcset")

def prepare_html_for_markdown(html_content: str, base_url: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    for img in soup.find_all("img"):
        src = (img.get("src") or "").strip()
        if (not src or src.startswith("data:")):
            for key in LAZY_SRC_KEYS:
                val = (img.get(key) or "").strip()
                if val:
                    src = val
                    img["src"] = src
                    break

        if not img.get("srcset"):
            for key in LAZY_SRCSET_KEYS:
                val = (img.get(key) or "").strip()
                if val:
                    img["srcset"] = val
                    break

        if src and not src.startswith(("http://", "https://", "data:")):
            img["src"] = urljoin(base_url, src)

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

        attrs_to_remove = [
            "width", "height", "title", "class", "style", "loading", "decoding",
            "data-org-width", "data-org-height", "dmcf-mid", "dmcf-mtype",
            *LAZY_SRC_KEYS, *LAZY_SRCSET_KEYS
        ]
        for attr in attrs_to_remove:
            if attr in img.attrs:
                del img[attr]

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
    content = (text or "").strip()

    if not href:
        return content

    if content:
        clean_content = re.sub(r'\s+', ' ', content).strip() 
        return f"[{clean_content}]({href})"
    
    img = tag.find("img")
    if img and img.get("src"):
        alt = (img.get("alt") or "").strip()
        src = (img.get("src") or "").strip()
        inner = f"![{alt}]({src})" if alt else f"![Image]({src})"
        return f"[{inner}]({href})"

    label = tag.get_text(strip=True) or href
    return f"[{label}]({href})"


def custom_li_converter(*, tag: Tag, text: str, convert_as_inline: bool = False, **kwargs) -> str:
    bullets = kwargs.get("bullets", ("*",)) 
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
                        line = " ".join(line.split())
                        if line:
                            result_parts.append(f"\n{list_indent_str}{line}\n")
            return "".join(result_parts)

    return f"\n\n{bullet} {' '.join((text or '').split())}\n"



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