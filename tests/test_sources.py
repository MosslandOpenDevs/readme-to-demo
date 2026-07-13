from __future__ import annotations

import pytest

from readme_to_demo import sources
from readme_to_demo.sources import SourceError, describe_source, read_source


class _FakeHeaders:
    def __init__(self, charset):
        self._charset = charset

    def get_content_charset(self):
        return self._charset


class _FakeResponse:
    """Honors the read-size argument so a bounded-read regression is observable."""

    def __init__(self, body: bytes, charset="utf-8"):
        self._body = body
        self.headers = _FakeHeaders(charset)
        self.requested = None

    def read(self, amt=None):
        self.requested = amt
        return self._body if amt is None else self._body[:amt]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_local_path_wins(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# Local\n", encoding="utf-8")
    assert read_source(str(readme)) == "# Local\n"


def test_missing_local_path_raises_oserror(tmp_path):
    with pytest.raises(OSError):
        read_source(str(tmp_path / "nope.md"))


def test_http_url_is_fetched(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["ua"] = request.get_header("User-agent")
        return _FakeResponse(b"# Remote\n")

    monkeypatch.setattr(sources, "urlopen", fake_urlopen)
    assert read_source("https://example.com/README.md") == "# Remote\n"
    assert captured["url"] == "https://example.com/README.md"
    assert "readme-to-demo" in captured["ua"]


def test_github_shorthand_tries_candidates(monkeypatch):
    calls: list[str] = []

    def fake_urlopen(request, timeout=None):
        calls.append(request.full_url)
        if request.full_url.endswith("HEAD/README.md"):
            from urllib.error import HTTPError

            raise HTTPError(request.full_url, 404, "Not Found", hdrs=None, fp=None)
        return _FakeResponse(b"# Shorthand\n")

    monkeypatch.setattr(sources, "urlopen", fake_urlopen)
    assert read_source("octo/repo") == "# Shorthand\n"
    assert calls[0].startswith("https://raw.githubusercontent.com/octo/repo/")


def test_read_is_bounded_and_oversize_rejected(monkeypatch):
    big = b"x" * (sources._MAX_BYTES + 10)
    resp = _FakeResponse(big)
    monkeypatch.setattr(sources, "urlopen", lambda request, timeout=None: resp)
    with pytest.raises(SourceError):
        read_source("https://example.com/big.md")
    # The code must request at most _MAX_BYTES + 1 bytes, never an unbounded read.
    assert resp.requested == sources._MAX_BYTES + 1


def test_unknown_server_charset_falls_back_to_utf8(monkeypatch):
    body = "# café\n".encode()
    monkeypatch.setattr(
        sources,
        "urlopen",
        lambda request, timeout=None: _FakeResponse(body, charset="nonsense-codec"),
    )
    # Must not raise LookupError; falls back to utf-8.
    assert read_source("https://example.com/x.md") == "# café\n"


def test_non_http_url_never_fetched(monkeypatch):
    def boom(*args, **kwargs):  # pragma: no cover - must not be called
        raise AssertionError("urlopen should not be called for file:// scheme")

    monkeypatch.setattr(sources, "urlopen", boom)
    with pytest.raises(OSError):
        read_source("file:///etc/passwd")


def test_describe_source_local_file(tmp_path):
    readme = tmp_path / "docs" / "README.md"
    readme.parent.mkdir()
    readme.write_text("x", encoding="utf-8")
    base_dir, label = describe_source(str(readme))
    assert base_dir == readme.parent
    assert label == "README.md"


def test_describe_source_url():
    base_dir, label = describe_source("https://example.com/R.md")
    assert base_dir is None
    assert label == "https://example.com/R.md"


def test_describe_source_shorthand():
    base_dir, label = describe_source("octo/repo")
    assert base_dir is None
    assert label == "octo/repo"
