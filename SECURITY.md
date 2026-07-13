# Security Policy

## Reporting a vulnerability

Please report suspected security issues privately using GitHub's
[private vulnerability reporting](https://github.com/MosslandOpenDevs/readme-to-demo/security/advisories/new)
rather than opening a public issue. We aim to acknowledge reports within a few
business days.

## Security posture

`readme-to-demo` is a documentation tool, and it is designed to stay on the safe
side of a few sharp edges:

- **It does not execute anything from a README.** The tool *reads and analyzes*
  markdown; it never runs install or usage commands it extracts. Any future
  execution/verification feature will require an explicit, opt-in command on a
  locally checked-in plan — never on remote input.
- **Network fetches are constrained.** Only `http`/`https` sources are fetched;
  other URL schemes (e.g. `file://`) are rejected. Downloads are capped
  (currently 5 MiB) to avoid memory exhaustion, and a request timeout applies.
- **`owner/repo` shorthand** resolves only to `raw.githubusercontent.com` README
  paths for the given repository.

## Supported versions

Only the latest released `0.x` version receives fixes while the project is
pre-1.0.
