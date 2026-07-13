"""readme-to-demo: turn a raw README into a demo-oriented project brief."""

from __future__ import annotations

__version__ = "0.2.0"

from .extractor import (
    Analysis,
    ChecklistItem,
    analyze,
    extract_checklist,
    extract_demo_brief,
    render_brief,
    render_checklist,
)
from .models import Asset, CodeBlock, ParsedReadme, Section
from .parser import parse
from .sources import SourceError, describe_source, read_source

__all__ = [
    "__version__",
    "Analysis",
    "ChecklistItem",
    "analyze",
    "extract_checklist",
    "extract_demo_brief",
    "render_brief",
    "render_checklist",
    "parse",
    "ParsedReadme",
    "Section",
    "CodeBlock",
    "Asset",
    "read_source",
    "describe_source",
    "SourceError",
]
