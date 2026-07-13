"""Structured, provenance-carrying view of a parsed README.

Every element keeps the 1-based source line it came from so the demo brief can
cite *where* each install/usage command and asset was found — the first step
toward treating a README as something you compile rather than eyeball.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Section:
    """A heading and the raw markdown body beneath it."""

    title: str
    level: int  # 1-6 for ATX/setext headings; 0 for the implicit intro
    body: str
    line: int  # 1-based line of the heading


@dataclass(frozen=True)
class CodeBlock:
    """A fenced or indented code block."""

    content: str
    lang: str  # lowercased info string ("" when untagged)
    line: int  # 1-based line of the opening fence


@dataclass(frozen=True)
class Asset:
    """An image reference (markdown, reference-style, or raw HTML ``<img>``)."""

    src: str
    line: int  # 1-based
    is_badge: bool
    kind: str  # "markdown" | "html"


@dataclass(frozen=True)
class ParsedReadme:
    """Everything the extractor needs, derived from a real markdown AST."""

    title: str
    first_paragraph: str
    sections: list[Section] = field(default_factory=list)
    code_blocks: list[CodeBlock] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)
    line_count: int = 0
