# readme-to-demo

Turn a raw GitHub README into a cleaner demo-oriented project brief.

> Extract installation, run steps, screenshots, FAQ candidates, and a launch-friendly summary from messy repository documentation.

[![CI](https://github.com/MosslandOpenDevs/readme-to-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/MosslandOpenDevs/readme-to-demo/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## The problem

Many open-source repositories have useful information, but it is buried inside long READMEs, inconsistent sections, or weak structure.

That creates friction for:

- first-time users,
- reviewers,
- contributors,
- and maintainers trying to present the project clearly.

`readme-to-demo` helps convert raw README content into a more demo-friendly structure that is easier to scan, explain, and reuse.

---

## Demo Preview

<table>
<tr>
<td><img src="./docs/assets/screenshot-1.svg" alt="Raw README input" width="100%"/></td>
<td><img src="./docs/assets/screenshot-2.svg" alt="Structured extraction" width="100%"/></td>
<td><img src="./docs/assets/screenshot-3.svg" alt="Demo-ready output" width="100%"/></td>
</tr>
</table>

### Demo flow
1. Point the tool at a README — local path, `http(s)` URL, or `owner/repo` shorthand
2. Extract key operational sections and score launch readiness
3. Output a cleaner demo-ready markdown brief (or a readiness report)

---

## 3-step how it works

### 1) Read the README
The tool accepts a local markdown path, an `http(s)` URL, or a GitHub `owner/repo`
shorthand (it fetches the repository's README for you) and parses it into a real
CommonMark/GFM syntax tree. Because it works on an AST rather than line-by-line
regex, it gets the tricky cases right: `#` inside a code fence is code (not a
heading), setext (underline) headings are recognized, reference-style images
resolve to their target, and screenshots embedded as raw HTML `<img>` are found.

### 2) Normalize the structure
It groups useful content into a stable public-repo format, keeping the **source
line** each element came from:

- project summary (first real prose paragraph, badges skipped)
- install steps (section-aware, with command-block fallback)
- run steps (classified by command, e.g. `pip install` vs `npm run`)
- demo assets (screenshots only — badges filtered out)
- FAQ candidates
- launch-readiness checklist
- broken local image links (referenced but missing on disk)

### 3) Generate a demo-ready brief
It outputs a markdown brief for project landing pages, launch docs, quick demos,
and contributor onboarding. Each extracted install/usage block cites where it came
from (`README.md:L42`), missing assets are flagged, and the brief ends with a
launch checklist and gap-aware cleanup suggestions. Use `check` when you only want
the readiness score.

---

## Sample scenario

**Input:** a long README with mixed sections, screenshots, setup commands, and scattered notes.

**Output:** a shorter markdown brief with:
- one-paragraph summary,
- install block,
- run block,
- screenshot section,
- FAQ candidates,
- maintainers' next cleanup suggestions.

---

## Quickstart

Install the package (editable install for local development):

```bash
pip install -e .
```

Convert a README into a demo brief:

```bash
# From a local file, writing to disk
readme-to-demo convert README.md --output demo-brief.md

# From a local file, printing to stdout (omit --output)
readme-to-demo convert README.md

# From a public URL or a GitHub owner/repo shorthand
readme-to-demo convert https://raw.githubusercontent.com/octocat/Hello-World/HEAD/README
readme-to-demo convert octocat/Hello-World
```

Score a README's launch readiness:

```bash
readme-to-demo check README.md          # human-readable checklist + score
readme-to-demo check README.md --json   # machine-readable JSON
```

Prefer not to install the package? Grab its single dependency and run from source:

```bash
pip install markdown-it-py
PYTHONPATH=src python3 -m readme_to_demo.cli convert README.md --output demo-brief.md
```

> `check` exits `0` when every item passes and `2` when gaps remain, so it fits
> cleanly into CI as a documentation-quality gate.

---

## See it work

This is real output — the tool scoring its own README (`readme-to-demo check README.md`):

```text
# Launch Readiness: readme-to-demo

Score: 8 / 9

- [x] Project title (H1)
- [x] One-paragraph summary
- [x] Installation instructions
- [x] Usage / run steps
- [x] Runnable code example
- [x] Screenshot or demo image
- [ ] FAQ / troubleshooting
- [x] License section
- [x] Status badges
```

And an excerpt of a generated brief — note the **source-line provenance** and the
**missing-asset warning** (`readme-to-demo convert sample_input.md`):

````markdown
## Installation
```bash
pip install sample-project
```

_Source: sample_input.md:L7_

## Screenshot Assets
- ./docs/demo.png

## ⚠️ Missing Local Assets
- ./docs/demo.png (referenced but not found on disk)
````

The full example input/output pair lives in
[`sample_input.md`](./sample_input.md) → [`sample_output.md`](./sample_output.md)
and is verified byte-for-byte by the test suite.

---

## Why this project exists

The open-source ecosystem has a documentation quality gap.
Even strong repos often underperform because their README is hard to scan, hard to demo, or hard to translate into a launch-friendly structure.

This project aims to make public repository presentation more reproducible.

---

## Product direction

This project is intended to become a lightweight documentation utility for open-source launches.

### Direction 1 — Documentation as infrastructure
README quality affects adoption, trust, sharing, and contributor conversion. It should be treated as infrastructure, not decoration.

### Direction 2 — Small tool, high leverage
The tool should remain lightweight, scriptable, and easy to integrate into maintainer workflows.

### Direction 3 — Demo-first repository hygiene
The output should help maintainers prepare:
- launch pages,
- quickstart docs,
- GitHub landing sections,
- project showcase summaries.

### Direction 4 — Extendable extraction model
Long term, this can expand into:
- issue template suggestions,
- release-note drafting,
- screenshot inventory extraction,
- repo launch checklist generation.

---

## Scope

Shipped (v0.2):
- AST-based parsing (`markdown-it-py`) — fence-safe, setext-aware, resolves
  reference images, finds HTML `<img>` screenshots
- input from local path, `http(s)` URL, or `owner/repo` shorthand
- word-aware section detection (`cli` no longer matches `Client`)
- smarter summary extraction (first real paragraph, badges skipped)
- command-block classification (install vs run)
- **source-line provenance** for extracted commands
- **broken local asset detection**
- launch-readiness checklist + score (`check`), as text or JSON
- gap-aware cleanup suggestions; markdown or JSON output

Near-term additions:
- template styles for different repo types
- richer FAQ question/answer synthesis
- multi-repo batch mode
- documentation-quality scoring thresholds for CI gating

---

## Repository structure

```text
readme-to-demo/
├─ README.md
├─ CHANGELOG.md · CONTRIBUTING.md · SECURITY.md
├─ pyproject.toml
├─ sample_input.md · sample_output.md   # golden example pair
├─ src/readme_to_demo/
│  ├─ __init__.py
│  ├─ models.py       # Section / CodeBlock / Asset / ParsedReadme
│  ├─ parser.py       # markdown-it-py AST -> structured, line-tagged model
│  ├─ extractor.py    # classification, brief + checklist rendering
│  ├─ sources.py      # local path / URL / owner/repo resolution
│  └─ cli.py          # convert + check commands
├─ tests/
│  ├─ test_parser.py · test_extractor.py · test_sources.py · test_cli.py
│  ├─ test_dogfood.py  # processes its own README correctly
│  └─ test_golden.py   # sample_output.md stays in sync
├─ docs/assets/
│  ├─ screenshot-1.svg · screenshot-2.svg · screenshot-3.svg
└─ .github/workflows/ci.yml
```

---

## Roadmap

**North star:** grow from *summarizing* a README into *compiling* a repository
into a reproducible, CI-verified demo pack — analyze → propose a reviewable plan →
verify it in a sandbox → render evidence. Today the tool does the analysis half
(and cites its sources); the verification half is deliberately future work, and it
will always run on an explicit, checked-in plan rather than on remote input.

### Phase 1 — done · analysis
- ✅ local markdown input, section extraction, demo-brief output
- ✅ URL + `owner/repo` shorthand input
- ✅ AST parsing, provenance line numbers, broken-asset detection
- ✅ launch checklist + readiness score (`check`)

### Phase 2 — next · reviewable plan
- ⬜ `inspect` a repo into a `demo.plan.yaml` (each step keeps its README source line)
- ⬜ per-step assertions (exit code, stdout contains, files exist)
- ⬜ repo-type presets

### Phase 3 — later · verification
- ⬜ `verify` a plan in a rootless, network-off sandbox
- ⬜ `demo.lock.json` (commit + environment + result hashes)
- ⬜ drift detection between README and verified behavior

### Phase 4 — later · rendering
- ⬜ render adapters (terminal cast, browser capture, evidence doc)
- ⬜ GitHub Action + PR demo-drift summary
- ⬜ batch mode for multiple repos

---

## License

MIT
