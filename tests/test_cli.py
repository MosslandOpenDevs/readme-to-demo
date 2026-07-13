from __future__ import annotations

import json

from readme_to_demo import cli

SAMPLE = """# Sample

A sample project.

## Installation

```bash
pip install sample
```

## Usage

```bash
sample --run
```

## License

MIT
"""


def _write(tmp_path, text=SAMPLE):
    path = tmp_path / "README.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_convert_to_stdout(tmp_path, capsys):
    readme = _write(tmp_path)
    code = cli.main(["convert", str(readme)])
    out = capsys.readouterr().out
    assert code == 0
    assert "# Demo Brief" in out
    assert "## Project Summary" in out
    assert "_Source: README.md:L" in out  # provenance present


def test_convert_to_file(tmp_path, capsys):
    readme = _write(tmp_path)
    out_file = tmp_path / "nested" / "brief.md"
    code = cli.main(["convert", str(readme), "--output", str(out_file)])
    assert code == 0
    assert out_file.exists()
    assert "# Demo Brief" in out_file.read_text(encoding="utf-8")
    assert "Wrote demo brief to" in capsys.readouterr().out


def test_convert_warns_about_missing_local_asset(tmp_path, capsys):
    readme = _write(tmp_path, "# S\n\nSummary.\n\n![shot](./ghost.png)\n")
    cli.main(["convert", str(readme)])
    assert "Missing Local Assets" in capsys.readouterr().out


def test_check_returns_two_when_incomplete(tmp_path, capsys):
    readme = _write(tmp_path, "# Bare\n\nJust a summary.\n")
    code = cli.main(["check", str(readme)])
    assert code == 2
    assert "Launch Readiness" in capsys.readouterr().out


def test_check_json_output(tmp_path, capsys):
    readme = _write(tmp_path)
    code = cli.main(["check", str(readme), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["title"] == "Sample"
    assert isinstance(payload["score"]["done"], int)
    assert code == 2  # sample lacks screenshots + badges + FAQ


def test_missing_input_reports_error(tmp_path, capsys):
    code = cli.main(["convert", str(tmp_path / "absent.md")])
    assert code == 1
    assert "error:" in capsys.readouterr().err
