"""Same PDF, same Markdown, whatever the process's hash seed (2026-10-23: p2688r1 converted two
ways because a tie was broken by set order, which follows PYTHONHASHSEED). Each paper is
converted in two fresh processes under different seeds; the outputs must be byte-identical."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = Path(__file__).parent / "fixtures" / "golden"
# p2688r1: the paper that exposed the seed dependence (a header row added or not)
SAMPLE = sorted(GOLDEN.glob("*.pdf"))[:4] + sorted((Path(__file__).parent / "fixtures" / "determinism").glob("*.pdf"))

_RUN = ("import sys, hashlib; sys.path.insert(0, sys.argv[1]); import tomd.lib.pdf as P; "
        "print(hashlib.sha256(P._run_pipeline(sys.argv[2]).md.encode()).hexdigest())")


def _digest(pdf: Path, seed: str) -> str:
    env = dict(os.environ, PYTHONHASHSEED=seed)
    out = subprocess.run([sys.executable, "-c", _RUN, str(ROOT.parent), str(pdf)], env=env,
                         capture_output=True, text=True, timeout=600)
    assert out.returncode == 0, out.stderr[-2000:]
    return out.stdout.strip().splitlines()[-1]


@pytest.mark.parametrize("pdf", SAMPLE, ids=[p.stem for p in SAMPLE])
def test_output_does_not_depend_on_the_hash_seed(pdf):
    assert _digest(pdf, "0") == _digest(pdf, "1")
