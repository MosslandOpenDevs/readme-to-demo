from __future__ import annotations

from readme_to_demo.parser import parse


def test_hash_inside_code_fence_is_not_a_heading():
    text = "# Real Title\n\nSummary.\n\n## Usage\n\n```bash\n# a shell comment\necho hi\n```\n"
    titles = [s.title for s in parse(text).sections]
    assert "a shell comment" not in titles
    assert titles == ["Real Title", "Usage"]


def test_setext_headings_are_recognized():
    text = "Setext Title\n===========\n\nSummary.\n\nInstall Steps\n-------------\n\n```bash\npip install x\n```\n"
    parsed = parse(text)
    assert parsed.title == "Setext Title"
    assert "Install Steps" in [s.title for s in parsed.sections]


def test_reference_style_image_is_resolved():
    text = "# T\n\nS.\n\n![alt][logo]\n\n[logo]: ./pics/logo.png\n"
    srcs = [a.src for a in parse(text).assets]
    assert "./pics/logo.png" in srcs


def test_html_img_detected_with_line():
    text = '# T\n\nS.\n\n<img src="./shot.png" width="50" />\n'
    assets = parse(text).assets
    shot = next(a for a in assets if a.src == "./shot.png")
    assert shot.kind == "html"
    assert shot.line == 5


def test_shields_badge_flagged_but_screenshot_is_not():
    text = "# T\n\nS.\n\n![ci](https://img.shields.io/badge/x-y-green)\n\n![shot](./demo.png)\n"
    assets = {a.src: a for a in parse(text).assets}
    assert assets["https://img.shields.io/badge/x-y-green"].is_badge is True
    assert assets["./demo.png"].is_badge is False


def test_crlf_input_is_normalized():
    text = "# T\r\n\r\nSummary line.\r\n\r\n## Usage\r\n\r\nrun it\r\n"
    parsed = parse(text)
    assert parsed.title == "T"
    assert parsed.first_paragraph == "Summary line."


def test_first_paragraph_skips_badge_only_paragraph():
    text = "# T\n\n![a](https://img.shields.io/badge/a-b-c) ![d](https://img.shields.io/badge/d-e-f)\n\nActual summary.\n"
    assert parse(text).first_paragraph == "Actual summary."


def test_code_block_language_preserved():
    text = "# T\n\nS.\n\n```python\nprint(1)\n```\n"
    blocks = parse(text).code_blocks
    assert len(blocks) == 1
    assert blocks[0].lang == "python"
    assert blocks[0].line == 5


def test_gitlab_badges_recognized():
    # Regression: GitLab /badges/<branch>/coverage.svg and pipeline.svg are badges.
    text = (
        "# T\n\nS.\n\n"
        "![cov](https://gitlab.com/u/r/badges/main/coverage.svg)\n\n"
        "![pipe](https://gitlab.com/u/r/badges/main/pipeline.svg)\n"
    )
    assets = parse(text).assets
    assert all(a.is_badge for a in assets), [a.src for a in assets]


def test_unresolved_reference_image_is_not_the_summary():
    # Regression: "![shot][undefined]" must not leak literal markdown as summary.
    text = "# Cool Project\n\n![screenshot][shot]\n\nThis is the real summary.\n"
    assert parse(text).first_paragraph == "This is the real summary."
