#!/usr/bin/env python3
"""Verify the packaged artifact and optionally run the full replay."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import py_compile
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "release-manifest.json"
REQUIRED = [
    "run_all.py", "budget.py", "pilot.py", "reproduce.py",
    "export_tables.py", "requirements.txt", "environment-lock.json",
    "docs/REPRODUCIBILITY.md",
]
FORBIDDEN_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fail(message: str) -> None:
    raise SystemExit("release verification failed: " + message)


def check_integrity() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            fail(f"missing required file: {rel}")
    if not MANIFEST.is_file():
        fail("missing release-manifest.json")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = data.get("files", {})
    if not expected:
        fail("empty manifest")
    for rel, meta in sorted(expected.items()):
        p = ROOT / rel
        try:
            p.resolve().relative_to(ROOT.resolve())
        except ValueError:
            fail(f"unsafe manifest path: {rel}")
        if not p.is_file():
            fail(f"manifest file missing: {rel}")
        if p.stat().st_size != int(meta["size"]):
            fail(f"size mismatch: {rel}")
        if digest(p) != meta["sha256"]:
            fail(f"hash mismatch: {rel}")
    for p in ROOT.rglob("*"):
        if p.is_symlink():
            fail(f"symbolic link is not permitted: {p.relative_to(ROOT)}")
        if any(part in FORBIDDEN_PARTS for part in p.parts):
            fail(f"cache directory is packaged: {p.relative_to(ROOT)}")
    for p in sorted(ROOT.rglob("*.py")):
        if any(part in FORBIDDEN_PARTS for part in p.parts):
            continue
        py_compile.compile(str(p), doraise=True, cfile=str(Path('/tmp') / (p.name + '.pyc')))
    print(f"integrity: PASS ({len(expected)} immutable files)")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--integrity-only", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = parser.parse_args()
    check_integrity()
    if args.run:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.run([sys.executable, "run_all.py"], cwd=ROOT, env=env)
        if proc.returncode:
            fail(f"run_all.py exited with {proc.returncode}")
        check_integrity()
        print("scientific replay and post-replay integrity: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
