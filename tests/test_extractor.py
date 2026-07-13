from __future__ import annotations

import json

from readme_to_demo.extractor import analyze, render_brief, render_checklist

FULL_README = """# Awesome Tool

A tiny tool that turns chaos into order.

![badge](https://img.shields.io/badge/build-passing-green)

## Installation

```bash
pip install awesome-tool
```

## Usage

```bash
awesome-tool run --fast
```

## Screenshots

<img src="./docs/demo.png" alt="demo" />

## FAQ

Answers to common questions.

## License

MIT
"""


def test_summary_is_first_prose_paragraph_not_badge():
    assert analyze(FULL_README).summary == "A tiny tool that turns chaos into order."


def test_command_blocks_classified_by_content():
    analysis = analyze(FULL_README)
    assert "pip install awesome-tool" in analysis.install
    assert "awesome-tool run --fast" in analysis.usage


def test_html_img_is_detected_as_screenshot():
    assert "./docs/demo.png" in analyze(FULL_README).images


def test_badges_excluded_from_screenshots_but_counted():
    analysis = analyze(FULL_README)
    assert not any("shields.io" in img for img in analysis.images)
    assert analysis.has_badge is True


def test_checklist_full_readme_scores_high():
    done, total = analyze(FULL_README).score
    assert (done, total) == (9, 9)


def test_language_tagged_code_block_counts_as_runnable_example():
    # Regression: a ```python-only README must still score "Runnable code example".
    text = "# Cool Lib\n\nA greeter.\n\n## Usage\n\n```python\nfrom cool import greet\nprint(greet('x'))\n```\n"
    labels = {i.label: i.present for i in analyze(text).checklist}
    assert labels["Runnable code example"] is True


def test_badge_word_in_prose_is_not_a_status_badge():
    # Regression: the bare word "badge" in prose must not flag Status badges.
    text = "# Thing\n\nWe reward top users with a shiny badge in the profile UI.\n"
    labels = {i.label: i.present for i in analyze(text).checklist}
    assert labels["Status badges"] is False


def test_cli_keyword_does_not_match_client_section():
    # Regression: 'cli' must not substring-match 'Client'.
    text = "# App\n\nIntro.\n\n## Client\n\nOur client library talks to the server.\n\n## Install\n\n```bash\npip install app\n```\n"
    analysis = analyze(text)
    assert "client library" not in analysis.usage


def test_missing_local_asset_is_flagged(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# T\n\nS.\n\n![shot](./nope.png)\n", encoding="utf-8")
    analysis = analyze(readme.read_text(), base_dir=tmp_path, source_label="README.md")
    assert analysis.missing_assets == ["./nope.png"]


def test_existing_local_asset_is_not_flagged(tmp_path):
    (tmp_path / "there.png").write_bytes(b"x")
    readme = tmp_path / "README.md"
    readme.write_text("# T\n\nS.\n\n![shot](./there.png)\n", encoding="utf-8")
    analysis = analyze(readme.read_text(), base_dir=tmp_path, source_label="README.md")
    assert analysis.missing_assets == []


def test_remote_asset_never_flagged_missing(tmp_path):
    text = "# T\n\nS.\n\n![shot](https://example.com/a.png)\n"
    assert analyze(text, base_dir=tmp_path).missing_assets == []


def test_summary_falls_back_when_absent():
    assert analyze("## No title, no intro\n").summary == "Project summary unavailable."


def test_render_brief_includes_provenance_and_headings():
    brief = render_brief(analyze(FULL_README, source_label="README.md"))
    for token in (
        "## Project Summary",
        "## Installation",
        "Readiness score: 9 / 9",
        "_Source: README.md:L",
    ):
        assert token in brief


def test_render_checklist_json_is_valid():
    payload = json.loads(render_checklist(analyze(FULL_README), as_json=True))
    assert payload["title"] == "Awesome Tool"
    assert payload["score"] == {"done": 9, "total": 9}
    assert len(payload["checklist"]) == 9
    assert payload["missing_assets"] == []


def test_cleanup_suggestions_target_gaps():
    brief = render_brief(analyze("# Bare\n\nOnly a summary line.\n"))
    assert "status badges" in brief.lower()
    assert "license" in brief.lower()


def test_query_string_asset_found_on_disk(tmp_path):
    # Regression: "docs/demo.png?raw=true" must resolve to docs/demo.png on disk.
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "demo.png").write_bytes(b"x")
    text = "# T\n\nS.\n\n![demo](docs/demo.png?raw=true)\n"
    assert analyze(text, base_dir=tmp_path).missing_assets == []


def test_install_style_block_never_becomes_usage():
    # Regression: "pip install -e ./" contains the "./" run hint but is an install
    # command; it must not be presented as the Usage step.
    text = (
        "# T\n\nS.\n\n## Setup\n\n"
        "```bash\ngit clone https://example.com/r.git\n```\n\n"
        "```bash\npip install -e ./\n```\n"
    )
    analysis = analyze(text)
    assert "pip install" not in analysis.usage
    assert analysis.usage == "No usage steps detected."
