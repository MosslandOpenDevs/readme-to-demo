"""Golden test: the checked-in sample_output.md must match freshly generated output.

This guards against silent drift — if extraction/rendering changes, regenerate
sample_output.md (``readme-to-demo convert sample_input.md -o sample_output.md``)
and commit it deliberately, rather than letting the documented example rot.
"""

from __future__ import annotations

from pathlib import Path

from readme_to_demo.extractor import extract_demo_brief

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_sample_output_matches_generated():
    generated = extract_demo_brief(str(REPO_ROOT / "sample_input.md"))
    committed = (REPO_ROOT / "sample_output.md").read_text(encoding="utf-8")
    assert generated == committed, (
        "sample_output.md is stale — regenerate with:\n"
        "  readme-to-demo convert sample_input.md --output sample_output.md"
    )
