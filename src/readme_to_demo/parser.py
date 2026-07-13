"""Parse README markdown into a structured :class:`ParsedReadme` using a real
CommonMark/GFM AST (``markdown-it-py``).

Parsing through an AST rather than line-by-line regex fixes a whole class of
fragility that a demo tool must not get wrong:

* ``#`` inside a fenced code block is code, never a heading;
* setext (underline-style) headings are recognized;
* reference-style images (``![alt][id]``) resolve to their target;
* screenshots embedded as raw HTML ``<img>`` are detected;
* CRLF input is normalized.

Every returned element carries its 1-based source line for provenance.
"""

from __future__ import annotations

import re

from markdown_it import MarkdownIt

from .models import Asset, CodeBlock, ParsedReadme, Section

__all__ = ["parse"]

_MD = MarkdownIt("commonmark").enable("table")

_HTML_IMG_RE = re.compile(r"""<img[^>]*\bsrc\s*=\s*["']([^"']+)["']""", re.IGNORECASE)

# Image URLs that are status badges rather than demo screenshots. Matched against
# the image *source*, never against prose, so mentioning the word "badge" in text
# never counts as a badge.
_BADGE_SRC_RE = re.compile(
    r"""
    img\.shields\.io | badge\.fury\.io | badgen\.net | shields\.io
    | /badges?/ | badge\.svg | \.svg\?        # generic badge image conventions
    | (?:coverage|pipeline)\.svg              # GitLab canonical badge names
    | codecov\.io | coveralls\.io | app\.codacy\.com
    | travis-ci | circleci\.com/.*\.svg | github\.com/.*/badge\.svg
    """,
    re.IGNORECASE | re.VERBOSE,
)


def parse(text: str) -> ParsedReadme:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    tokens = _MD.parse(text)

    headings = _collect_headings(tokens)
    code_blocks = _collect_code_blocks(tokens)
    assets = _collect_assets(tokens)
    first_paragraph = _first_paragraph(tokens)
    sections = _build_sections(headings, lines, text)

    return ParsedReadme(
        title=_title(headings),
        first_paragraph=first_paragraph,
        sections=sections,
        code_blocks=code_blocks,
        assets=assets,
        line_count=len(lines),
    )


def _is_badge(src: str) -> bool:
    return bool(_BADGE_SRC_RE.search(src))


def _inline_text(token) -> str:
    """Plain text of an inline token: link/emphasis labels kept, images dropped.

    Deliberately does NOT fall back to ``token.content`` (the raw markdown), so an
    image/badge-only paragraph reads as empty and is skipped as a summary.
    """
    if token is None:
        return ""
    parts: list[str] = []
    for child in token.children or []:
        if child.type in ("text", "code_inline"):
            parts.append(child.content)
        elif child.type in ("softbreak", "hardbreak"):
            parts.append(" ")
    return "".join(parts).strip()


def _collect_headings(tokens) -> list[tuple[int, str, int, int]]:
    """Return ``(level, title, start_line0, body_start_line0)`` per heading."""
    headings: list[tuple[int, str, int, int]] = []
    for idx, tok in enumerate(tokens):
        if tok.type != "heading_open":
            continue
        level = int(tok.tag[1])
        inline = tokens[idx + 1] if idx + 1 < len(tokens) else None
        title = _inline_text(inline) if inline and inline.type == "inline" else ""
        start, body_start = (tok.map[0], tok.map[1]) if tok.map else (0, 1)
        headings.append((level, title, start, body_start))
    return headings


def _collect_code_blocks(tokens) -> list[CodeBlock]:
    blocks: list[CodeBlock] = []
    for tok in tokens:
        if tok.type not in ("fence", "code_block"):
            continue
        info = (tok.info or "").strip()
        lang = info.split()[0].lower() if info else ""
        line = (tok.map[0] + 1) if tok.map else 0
        content = tok.content.rstrip("\n")
        if content.strip():
            blocks.append(CodeBlock(content=content, lang=lang, line=line))
    return blocks


def _collect_assets(tokens) -> list[Asset]:
    assets: list[Asset] = []
    seen: set[str] = set()

    def add(src: str, line: int, kind: str) -> None:
        src = src.strip()
        if src and src not in seen:
            seen.add(src)
            assets.append(Asset(src=src, line=line, is_badge=_is_badge(src), kind=kind))

    for tok in tokens:
        line = (tok.map[0] + 1) if tok.map else 0
        if tok.type == "inline":
            for child in tok.children or []:
                if child.type == "image":
                    add(child.attrGet("src") or "", line, "markdown")
                elif child.type == "html_inline":
                    for match in _HTML_IMG_RE.finditer(child.content):
                        add(match.group(1), line, "html")
        elif tok.type == "html_block":
            for match in _HTML_IMG_RE.finditer(tok.content):
                add(match.group(1), line, "html")
    return assets


# An image reference whose definition is missing survives as literal text like
# "![alt][ref]" or "![alt]"; it must not be mistaken for prose.
_UNRESOLVED_IMAGE_RE = re.compile(r"!\[[^\]]*\](?:\[[^\]]*\])?")


def _first_paragraph(tokens) -> str:
    """First real prose paragraph — a badge/logo-only paragraph is not prose."""
    expecting = False
    for tok in tokens:
        if tok.type == "paragraph_open":
            expecting = True
        elif tok.type == "inline" and expecting:
            expecting = False
            text = _UNRESOLVED_IMAGE_RE.sub("", _inline_text(tok)).strip()
            if text:
                return text
    return ""


def _build_sections(
    headings: list[tuple[int, str, int, int]], lines: list[str], text: str
) -> list[Section]:
    sections: list[Section] = []

    intro = "\n".join(lines[: headings[0][2]]).strip() if headings else text.strip()
    if intro:
        sections.append(Section(title="Introduction", level=0, body=intro, line=1))

    for i, (level, title, start, body_start) in enumerate(headings):
        end = headings[i + 1][2] if i + 1 < len(headings) else len(lines)
        body = "\n".join(lines[body_start:end]).strip()
        sections.append(Section(title=title, level=level, body=body, line=start + 1))

    return sections


def _title(headings: list[tuple[int, str, int, int]]) -> str:
    for level, title, *_ in headings:
        if level == 1 and title:
            return title
    for _level, title, *_ in headings:
        if title:
            return title
    return "Untitled project"
