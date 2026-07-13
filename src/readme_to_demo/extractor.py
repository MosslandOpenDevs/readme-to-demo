"""Turn a parsed README into a structured, provenance-carrying demo brief.

Public entry points:

* :func:`analyze` — README text -> :class:`Analysis`
* :func:`render_brief` — Analysis -> demo-brief markdown
* :func:`render_checklist` — Analysis -> launch-readiness report (text or JSON)
* :func:`extract_demo_brief` / :func:`extract_checklist` — convenience wrappers
  that accept any source string (local path, URL, ``owner/repo`` shorthand).

Section detection is keyword-driven but word-aware (so ``cli`` no longer matches
``client``); the runnable-example check considers code blocks in *any* language;
badges are recognized by image URL, never by the word "badge" in prose.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from .models import Asset, CodeBlock, Section
from .parser import parse
from .sources import describe_source, read_source

__all__ = [
    "Analysis",
    "ChecklistItem",
    "analyze",
    "render_brief",
    "render_checklist",
    "extract_demo_brief",
    "extract_checklist",
]

# Section-title keyword groups. Single tokens match at a word start (so "install"
# also matches "Installation"); tokens in _EXACT_KEYWORDS match as whole words
# (so the acronym "cli" does not match "Client"); phrases match as substrings.
SECTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "install": ("install", "setup", "getting started", "quickstart", "quick start", "prerequisite"),
    "usage": ("usage", "how to use", "run", "example", "cli", "command"),
    "faq": ("faq", "troubleshoot", "limitation", "known issue", "gotcha", "caveat", "q&a", "notes"),
    "license": ("license", "licence"),
}
_EXACT_KEYWORDS = frozenset({"cli", "faq", "ci", "q&a"})

# Fenced-code languages treated as shell commands for install/usage classification.
_SHELL_LANGS = frozenset(
    {"", "bash", "sh", "shell", "console", "zsh", "shell-session", "shellsession"}
)

_INSTALL_HINTS = (
    "pip install",
    "pip3 install",
    "uv pip",
    "uv add",
    "uv sync",
    "poetry add",
    "pipx install",
    "npm install",
    "npm i ",
    "yarn add",
    "pnpm add",
    "brew install",
    "apt-get install",
    "cargo add",
    "go get",
    "git clone",
    "gem install",
)
_RUN_HINTS = (
    "npm run",
    "npm start",
    "yarn dev",
    "pnpm dev",
    "python ",
    "python3 ",
    "node ",
    "make ",
    "docker run",
    "uvicorn",
    "flask run",
    "go run",
    "cargo run",
    "pytest",
    "readme-to-demo",
    "./",
    "-m ",
)


@dataclass(frozen=True)
class ChecklistItem:
    label: str
    present: bool


@dataclass(frozen=True)
class Analysis:
    """Structured view of a README used to render the brief and checklist."""

    title: str
    summary: str
    install: str
    usage: str
    images: list[str] = field(default_factory=list)  # screenshots (badges excluded)
    faq_sections: list[tuple[str, str]] = field(default_factory=list)
    checklist: list[ChecklistItem] = field(default_factory=list)
    missing_assets: list[str] = field(default_factory=list)
    has_badge: bool = False
    source_label: str = "README.md"
    install_line: int | None = None
    usage_line: int | None = None

    @property
    def score(self) -> tuple[int, int]:
        done = sum(1 for item in self.checklist if item.present)
        return done, len(self.checklist)


def analyze(
    text: str,
    *,
    base_dir: Path | None = None,
    source_label: str = "README.md",
) -> Analysis:
    """Extract structured demo content from README ``text``.

    ``base_dir`` (when the source is a local file) is used to flag referenced
    screenshots that do not exist on disk. ``source_label`` is cited in provenance.
    """
    parsed = parse(text)

    install_sec = _first_section(parsed.sections, "install")
    usage_sec = _first_section(parsed.sections, "usage")
    faq_sections = [
        (s.title, s.body)
        for s in parsed.sections
        if _matches(s.title.lower(), SECTION_KEYWORDS["faq"])
    ]

    shell_blocks = [b for b in parsed.code_blocks if b.lang in _SHELL_LANGS]
    install_cmd, usage_cmd = _classify_command_blocks(shell_blocks)

    install, install_line = _pick(install_sec, install_cmd, "No installation steps detected.")
    usage, usage_line = _pick(usage_sec, usage_cmd, "No usage steps detected.")

    screenshots = [a for a in parsed.assets if not a.is_badge]
    has_badge = any(a.is_badge for a in parsed.assets)
    missing_assets = _missing_assets(screenshots, base_dir)

    summary = parsed.first_paragraph or "Project summary unavailable."

    checklist = _build_checklist(
        title=parsed.title,
        summary=summary,
        install_present=bool(install_sec or install_cmd),
        usage_present=bool(usage_sec or usage_cmd),
        has_code=bool(parsed.code_blocks),
        has_screenshot=bool(screenshots),
        has_faq=bool(faq_sections),
        has_license=any(
            _matches(s.title.lower(), SECTION_KEYWORDS["license"]) for s in parsed.sections
        ),
        has_badge=has_badge,
    )

    return Analysis(
        title=parsed.title,
        summary=summary,
        install=install,
        usage=usage,
        images=[a.src for a in screenshots],
        faq_sections=faq_sections,
        checklist=checklist,
        missing_assets=missing_assets,
        has_badge=has_badge,
        source_label=source_label,
        install_line=install_line,
        usage_line=usage_line,
    )


def _first_section(sections: list[Section], group: str) -> Section | None:
    for section in sections:
        if _matches(section.title.lower(), SECTION_KEYWORDS[group]):
            return section
    return None


def _matches(title_lower: str, keywords: tuple[str, ...]) -> bool:
    for key in keywords:
        if " " in key:
            if key in title_lower:
                return True
        elif key in _EXACT_KEYWORDS:
            if re.search(rf"\b{re.escape(key)}\b", title_lower):
                return True
        elif re.search(rf"\b{re.escape(key)}", title_lower):  # word-start prefix
            return True
    return False


def _classify_command_blocks(blocks: list[CodeBlock]) -> tuple[CodeBlock | None, CodeBlock | None]:
    install = next((b for b in blocks if _has_hint(b.content, _INSTALL_HINTS)), None)
    # A block that itself looks like an install command (e.g. "pip install -e ./")
    # must never be presented as the run step, even if it contains a run hint.
    usage = next(
        (
            b
            for b in blocks
            if b is not install
            and _has_hint(b.content, _RUN_HINTS)
            and not _has_hint(b.content, _INSTALL_HINTS)
        ),
        None,
    )

    remaining = [b for b in blocks if b not in (install, usage)]
    if install is None and remaining:
        install = remaining.pop(0)
    if usage is None:
        usage = next((b for b in remaining if not _has_hint(b.content, _INSTALL_HINTS)), None)
    return install, usage


def _has_hint(block: str, hints: tuple[str, ...]) -> bool:
    lowered = block.lower()
    return any(hint in lowered for hint in hints)


def _pick(
    section: Section | None, block: CodeBlock | None, fallback: str
) -> tuple[str, int | None]:
    if section is not None and section.body:
        return section.body, section.line
    if block is not None:
        return block.content, block.line
    if section is not None:  # matched heading but empty body
        return fallback, section.line
    return fallback, None


def _missing_assets(screenshots: list[Asset], base_dir: Path | None) -> list[str]:
    if base_dir is None:
        return []
    missing: list[str] = []
    for asset in screenshots:
        src = asset.src
        parsed = urlparse(src)
        if parsed.scheme or src.startswith(("//", "data:", "#")):
            continue  # remote or inline asset — nothing to check on disk
        # Check only the path component: "docs/demo.png?raw=true" must resolve
        # to docs/demo.png, not a literal file with the query in its name.
        path_part = parsed.path
        if not path_part:
            continue
        candidate = base_dir / path_part.lstrip("/")
        if not candidate.exists():
            missing.append(src)
    return missing


def _build_checklist(
    *,
    title: str,
    summary: str,
    install_present: bool,
    usage_present: bool,
    has_code: bool,
    has_screenshot: bool,
    has_faq: bool,
    has_license: bool,
    has_badge: bool,
) -> list[ChecklistItem]:
    has_title = title not in ("", "Untitled project")
    has_summary = bool(summary) and summary != "Project summary unavailable."
    return [
        ChecklistItem("Project title (H1)", has_title),
        ChecklistItem("One-paragraph summary", has_summary),
        ChecklistItem("Installation instructions", install_present),
        ChecklistItem("Usage / run steps", usage_present),
        ChecklistItem("Runnable code example", has_code),
        ChecklistItem("Screenshot or demo image", has_screenshot),
        ChecklistItem("FAQ / troubleshooting", has_faq),
        ChecklistItem("License section", has_license),
        ChecklistItem("Status badges", has_badge),
    ]


def render_brief(analysis: Analysis) -> str:
    lines = [
        "# Demo Brief",
        "",
        "> Auto-generated by readme-to-demo — review before publishing.",
        "",
        "## Project Summary",
        analysis.summary,
        "",
        "## Installation",
        analysis.install,
    ]
    lines.extend(_provenance(analysis.install_line, analysis.source_label))

    lines.extend(["", "## Usage", analysis.usage])
    lines.extend(_provenance(analysis.usage_line, analysis.source_label))

    lines.extend(["", "## Screenshot Assets"])
    if analysis.images:
        lines.extend(f"- {img}" for img in analysis.images)
    else:
        lines.append("- No screenshot assets detected.")

    if analysis.missing_assets:
        lines.extend(["", "## ⚠️ Missing Local Assets"])
        lines.extend(
            f"- {src} (referenced but not found on disk)" for src in analysis.missing_assets
        )

    lines.extend(["", "## FAQ Candidates"])
    if analysis.faq_sections:
        for section_title, body in analysis.faq_sections[:3]:
            lines.append(f"### {section_title}".rstrip())
            lines.append(body if body else "_No details captured._")
            lines.append("")
        lines.pop()  # drop trailing spacer
    else:
        lines.append("No FAQ-like sections detected.")

    done, total = analysis.score
    lines.extend(["", "## Launch Checklist"])
    lines.extend(f"- [{'x' if item.present else ' '}] {item.label}" for item in analysis.checklist)
    lines.extend(["", f"Readiness score: {done} / {total}"])

    lines.extend(["", "## Maintainer Cleanup Suggestions"])
    lines.extend(f"- {tip}" for tip in _cleanup_suggestions(analysis))
    lines.append("")

    return "\n".join(lines)


def _provenance(line: int | None, label: str) -> list[str]:
    if line is None:
        return []
    return ["", f"_Source: {label}:L{line}_"]


def _cleanup_suggestions(analysis: Analysis) -> list[str]:
    tips: list[str] = []
    missing = {item.label for item in analysis.checklist if not item.present}

    if analysis.missing_assets:
        tips.append("Fix or remove README image links that do not exist on disk.")
    if "One-paragraph summary" in missing:
        tips.append("Add a one-paragraph summary near the top so the project explains itself.")
    if "Installation instructions" in missing:
        tips.append("Document install steps in a dedicated Installation section.")
    if "Usage / run steps" in missing:
        tips.append("Add a Usage section with a copy-pasteable run command.")
    if "Screenshot or demo image" in missing:
        tips.append("Add a demo screenshot or GIF near the top of the README.")
    if "Status badges" in missing:
        tips.append("Add build/version status badges for at-a-glance project health.")
    if "License section" in missing:
        tips.append("State the license explicitly so downstream users know their rights.")
    if "FAQ / troubleshooting" in missing:
        tips.append("Promote troubleshooting notes into explicit FAQ sections.")

    tips.append("Keep install and usage commands clearly separated and copy-pasteable.")
    return tips


def render_checklist(analysis: Analysis, *, as_json: bool = False) -> str:
    done, total = analysis.score
    if as_json:
        payload = {
            "title": analysis.title,
            "summary": analysis.summary,
            "source": analysis.source_label,
            "score": {"done": done, "total": total},
            "checklist": [
                {"label": item.label, "present": item.present} for item in analysis.checklist
            ],
            "missing_assets": analysis.missing_assets,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    lines = [
        f"# Launch Readiness: {analysis.title}",
        "",
        f"Score: {done} / {total}",
        "",
    ]
    lines.extend(f"- [{'x' if item.present else ' '}] {item.label}" for item in analysis.checklist)
    if analysis.missing_assets:
        lines.extend(["", "Missing local assets:"])
        lines.extend(f"- {src}" for src in analysis.missing_assets)
    lines.append("")
    return "\n".join(lines)


def extract_demo_brief(source: str) -> str:
    """Read ``source`` (path, URL, or ``owner/repo``) and render a demo brief."""
    base_dir, label = describe_source(source)
    return render_brief(analyze(read_source(source), base_dir=base_dir, source_label=label))


def extract_checklist(source: str, *, as_json: bool = False) -> str:
    """Read ``source`` and render a launch-readiness checklist."""
    base_dir, label = describe_source(source)
    return render_checklist(
        analyze(read_source(source), base_dir=base_dir, source_label=label), as_json=as_json
    )
