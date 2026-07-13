# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]

### Added
- **AST-based parsing** via `markdown-it-py` (new `parser.py` + `models.py`),
  replacing line-by-line regex. Fixes a class of correctness bugs:
  `#` inside a code fence is no longer treated as a heading, setext (underline)
  headings are recognized, and reference-style images resolve to their target.
- **Input from anywhere**: local path, `http(s)` URL, or `owner/repo` GitHub
  shorthand (`sources.py`), with scheme validation and a download size cap.
- **`check` command**: launch-readiness checklist and score, as text or `--json`;
  exits `2` when gaps remain so it can gate CI.
- **Provenance**: extracted install/usage commands cite their source line
  (e.g. `README.md:L42`) in the generated brief.
- **Broken-asset detection**: local screenshots referenced but missing on disk
  are flagged in the brief, the checklist JSON, and cleanup suggestions.
- **HTML `<img>` screenshots** are detected (not just markdown images).
- Test suite: parser, extractor, sources, CLI, plus **dogfood** (processes its
  own README correctly) and **golden** (`sample_output.md`) regression tests.
- `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`.

### Changed
- Summary extraction now uses the first real prose paragraph (badges/logos
  skipped) instead of only pre-H1 content — the "Project summary unavailable"
  bug on ordinary READMEs is fixed.
- Section detection is word-aware: the acronym `cli` no longer matches `Client`.
- Status badges are recognized by image URL, not by the word "badge" in prose.
- The "runnable code example" check counts fenced blocks in **any** language.
- `--output` is now optional (`convert` prints to stdout when omitted).
- Packaging modernized: PEP 639 SPDX `license`/`license-files`, classifiers,
  project URLs, `requires-python >= 3.10`, dropped `wheel` from build requires.
- CI: Python 3.10–3.14 matrix, `ruff` lint + format check, wheel/sdist install
  smoke test, least-privilege permissions, concurrency, and job timeouts;
  bumped to `actions/checkout@v7` and `actions/setup-python@v6`.

### Fixed
- Unknown server-declared charset no longer crashes the CLI with `LookupError`
  (falls back to UTF-8).
- GitLab badge URLs (`/badges/<branch>/coverage.svg`, `pipeline.svg`) are
  recognized as badges instead of being misclassified as screenshots.
- An unresolved reference-style image (`![alt][missing-def]`) no longer leaks
  literal markdown into the project summary.
- Local assets referenced with a query string or fragment
  (`docs/demo.png?raw=true`) are checked against their real path, eliminating
  false "missing asset" warnings.
- An install-style command (e.g. `pip install -e ./`) is never presented as the
  Usage step.

## [0.1.0]

### Added
- Initial MVP: local markdown input, regex heading extraction, demo-brief
  markdown output, and a CI smoke test.

[Unreleased]: https://github.com/MosslandOpenDevs/readme-to-demo/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/MosslandOpenDevs/readme-to-demo/releases/tag/v0.2.0
[0.1.0]: https://github.com/MosslandOpenDevs/readme-to-demo/releases/tag/v0.1.0
