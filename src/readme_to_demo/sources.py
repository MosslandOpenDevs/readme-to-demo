"""Input source resolution for readme-to-demo.

A "source" may be one of:

* a local markdown file path (``README.md``, ``./docs/guide.md``),
* an ``http``/``https`` URL pointing at a raw markdown file,
* a GitHub shorthand ``owner/repo`` (optionally prefixed ``gh:``), which is
  resolved to the repository's top-level ``README.md``.

Only ``http``/``https`` URLs are fetched over the network; every other scheme
is rejected so a stray ``file://`` argument can never read an arbitrary path.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

__all__ = ["read_source", "describe_source", "SourceError"]

_USER_AGENT = "readme-to-demo/0.2 (+https://github.com/MosslandOpenDevs/readme-to-demo)"
_DEFAULT_TIMEOUT = 30.0
# Cap downloads so a hostile or runaway URL cannot exhaust memory.
_MAX_BYTES = 5 * 1024 * 1024

# owner/repo — single slash, no scheme, no spaces. `gh:` prefix is optional.
_GITHUB_SHORTHAND = re.compile(r"^(?:gh:)?([\w.-]+)/([\w.-]+)$")
# Candidate raw locations to try, in order, for a GitHub shorthand.
_GITHUB_REF_CANDIDATES = ("HEAD", "main", "master")
_GITHUB_README_CANDIDATES = ("README.md", "readme.md", "Readme.md", "README.markdown", "README")


class SourceError(RuntimeError):
    """Raised when a source cannot be resolved to markdown text."""


def read_source(source: str, *, timeout: float = _DEFAULT_TIMEOUT) -> str:
    """Resolve ``source`` to markdown text.

    Resolution order: existing local path first (so a real file always wins),
    then ``http(s)`` URL, then GitHub ``owner/repo`` shorthand.
    """
    if _looks_like_url(source):
        return _fetch_url(source, timeout=timeout)

    path = Path(source)
    if path.exists():
        return path.read_text(encoding="utf-8")

    match = _GITHUB_SHORTHAND.match(source.strip())
    if match:
        return _fetch_github_readme(match.group(1), match.group(2), timeout=timeout)

    # Fall back to a plain read so the caller gets a normal FileNotFoundError
    # with the offending path, matching prior behaviour.
    return path.read_text(encoding="utf-8")


def describe_source(source: str) -> tuple[Path | None, str]:
    """Return ``(base_dir, label)`` for a source without reading it.

    ``base_dir`` is the directory to resolve relative asset paths against (only
    for local files; ``None`` for URLs/shorthand), and ``label`` is a short name
    to cite in provenance output.
    """
    if _looks_like_url(source):
        return None, source
    path = Path(source)
    if path.exists():
        return path.parent, path.name
    if _GITHUB_SHORTHAND.match(source.strip()):
        return None, source
    return path.parent, path.name


def _looks_like_url(source: str) -> bool:
    scheme = urlparse(source).scheme.lower()
    return scheme in ("http", "https")


def _fetch_url(url: str, *, timeout: float) -> str:
    scheme = urlparse(url).scheme.lower()
    if scheme not in ("http", "https"):  # defensive: never fetch other schemes
        raise SourceError(f"Unsupported URL scheme: {scheme!r}")

    request = Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - scheme checked above
            raw = response.read(_MAX_BYTES + 1)
            charset = response.headers.get_content_charset() or "utf-8"
    except HTTPError as exc:
        raise SourceError(f"Failed to fetch {url}: HTTP {exc.code} {exc.reason}") from exc
    except URLError as exc:
        raise SourceError(f"Failed to fetch {url}: {exc.reason}") from exc

    if len(raw) > _MAX_BYTES:
        raise SourceError(f"Refusing to read more than {_MAX_BYTES} bytes from {url}")

    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        # Server declared a charset Python has no codec for — fall back to UTF-8
        # rather than crashing the CLI with an uncaught LookupError.
        return raw.decode("utf-8", errors="replace")


def _fetch_github_readme(owner: str, repo: str, *, timeout: float) -> str:
    errors: list[str] = []
    for ref in _GITHUB_REF_CANDIDATES:
        for name in _GITHUB_README_CANDIDATES:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{name}"
            try:
                return _fetch_url(url, timeout=timeout)
            except SourceError as exc:
                errors.append(str(exc))
    detail = "; ".join(dict.fromkeys(errors)) or "no candidate URLs matched"
    raise SourceError(f"Could not locate a README for {owner}/{repo} ({detail})")
