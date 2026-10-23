"""Static check: no undefined name anywhere in the package (pyflakes). A missing import on a
default-on path otherwise fails only at run time, where a reader error records it and the
tables it touched are downgraded (2026-10-23: a stray trace() call in the scan build)."""
from pathlib import Path

from pyflakes import api, reporter

ROOT = Path(__file__).resolve().parent.parent


class _Collect(reporter.Reporter):
    def __init__(self):
        self.messages = []

    def flake(self, message):
        self.messages.append(message)

    def unexpectedError(self, filename, msg):
        self.messages.append(f"{filename}: {msg}")

    def syntaxError(self, filename, msg, lineno, offset, text):
        self.messages.append(f"{filename}:{lineno}: {msg}")


def _undefined(paths):
    rep = _Collect()
    for p in paths:
        api.checkPath(str(p), rep)
    return [str(m) for m in rep.messages if "undefined name" in str(m) or not hasattr(m, "message_args")]


def test_no_undefined_names_in_the_package():
    files = sorted((ROOT / "lib").rglob("*.py")) + [ROOT / "main.py"]
    bad = _undefined(files)
    assert not bad, "undefined names:\n" + "\n".join(bad)


def test_the_check_catches_a_missing_import(tmp_path):
    f = tmp_path / "m.py"
    f.write_text("def build():\n    trace('x')\n")
    assert _undefined([f])
