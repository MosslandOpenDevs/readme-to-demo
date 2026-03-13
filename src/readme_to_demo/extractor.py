from __future__ import annotations

from pathlib import Path
import re


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
CODE_RE = re.compile(r"```(?:bash|sh|shell)?\n(.*?)```", re.DOTALL)


def split_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_title = "Introduction"
    current_lines: list[str] = []

    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    sections.append((current_title, "\n".join(current_lines).strip()))
    return [(title, body) for title, body in sections if title or body]


def extract_demo_brief(path: str) -> str:
    content = Path(path).read_text(encoding="utf-8")
    sections = split_sections(content)

    intro = next((body for title, body in sections if title == "Introduction" and body), "")
    install = ""
    usage = ""
    faq_candidates: list[str] = []

    for title, body in sections:
        lower = title.lower()
        if not install and any(key in lower for key in ["install", "setup", "quickstart"]):
            install = body
        if not usage and any(key in lower for key in ["usage", "run", "getting started", "example"]):
            usage = body
        if any(key in lower for key in ["faq", "troubleshooting", "limitations", "notes"]):
            faq_candidates.append(f"## {title}\n\n{body}".strip())

    images = IMAGE_RE.findall(content)
    code_blocks = [block.strip() for block in CODE_RE.findall(content) if block.strip()]

    summary = intro.split("\n\n")[0].strip() if intro else "Project summary unavailable."
    install_block = install if install else (code_blocks[0] if code_blocks else "No installation steps detected.")
    usage_block = usage if usage else (code_blocks[1] if len(code_blocks) > 1 else "No usage steps detected.")

    lines = [
        "# Demo Brief",
        "",
        "## Project Summary",
        summary,
        "",
        "## Installation",
        install_block,
        "",
        "## Usage",
        usage_block,
        "",
        "## Screenshot Assets",
    ]

    if images:
        lines.extend([f"- {img}" for img in images])
    else:
        lines.append("- No screenshot assets detected.")

    lines.extend(["", "## FAQ Candidates"])
    if faq_candidates:
        lines.extend(faq_candidates[:3])
    else:
        lines.append("No FAQ-like sections detected.")

    lines.extend([
        "",
        "## Maintainer Cleanup Suggestions",
        "- Tighten the top-level summary into one paragraph.",
        "- Ensure install and usage commands are clearly separated.",
        "- Add a demo screenshot or GIF near the top of the README.",
        "- Promote troubleshooting notes into explicit FAQ sections if needed.",
        "",
    ])

    return "\n".join(lines)
