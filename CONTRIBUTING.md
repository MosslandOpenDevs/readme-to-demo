# Contributing

Thanks for helping improve `readme-to-demo`. This is a small, dependency-light
Python project — contributions of any size are welcome.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Before you push

```bash
pytest              # run the test suite (unit + dogfood + golden)
ruff check .        # lint
ruff format .       # auto-format (CI runs `ruff format --check`)
```

## Regenerating the sample

`sample_output.md` is a **golden file** verified by `tests/test_golden.py`. If a
change intentionally alters the generated brief, regenerate and commit it:

```bash
readme-to-demo convert sample_input.md --output sample_output.md
```

Otherwise the golden test will fail — that failure is the guardrail working.

## Guidelines

- Keep the runtime footprint small; prefer the standard library plus the existing
  `markdown-it-py` parser over new dependencies.
- The tool must always process **its own README** correctly — see
  `tests/test_dogfood.py`. If you touch extraction, keep those green.
- Add or update tests for any behavior change, and note user-facing changes in
  `CHANGELOG.md` under `[Unreleased]`.
- The tool analyzes READMEs; it must never execute commands it extracts. See
  `SECURITY.md`.
