"""The tool must process its OWN README correctly.

These are the regression tests for the bugs that shipped in v0.1.0: the summary
came back "unavailable", and none of the three HTML `<img>` screenshots were
detected. If any of these fail, readme-to-demo is once again failing to eat its
own dog food.
"""

from __future__ import annotations

from pathlib import Path

from readme_to_demo.extractor import analyze
from readme_to_demo.sources import describe_source

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"


def _analyze_own_readme():
    base_dir, label = describe_source(str(README))
    return analyze(README.read_text(encoding="utf-8"), base_dir=base_dir, source_label=label)


def test_own_title_and_summary():
    analysis = _analyze_own_readme()
    assert analysis.title == "readme-to-demo"
    assert analysis.summary != "Project summary unavailable."
    assert "README" in analysis.summary


def test_own_three_html_screenshots_detected():
    images = _analyze_own_readme().images
    for name in ("screenshot-1.svg", "screenshot-2.svg", "screenshot-3.svg"):
        assert any(name in img for img in images), f"missing {name} in {images}"


def test_own_usage_is_non_empty():
    analysis = _analyze_own_readme()
    assert analysis.usage != "No usage steps detected."


def test_own_readme_has_no_broken_local_assets():
    # Every local image the README references must exist on disk.
    assert _analyze_own_readme().missing_assets == []


def test_own_readme_scores_well():
    done, total = _analyze_own_readme().score
    assert total == 9
    assert done >= 8  # everything except (currently) a FAQ section
