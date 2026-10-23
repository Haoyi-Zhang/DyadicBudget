#!/usr/bin/env python3
"""Verify the paper-source distribution and optionally rebuild it."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT.parent / "artifact/.github/manuscript/release-manifest.json"
REQUIRED = ["build.py", "check_references.py", "acmart.cls", "ACM-Reference-Format.bst", "LICENSE", "BUILDING.md"]
FORBIDDEN_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fail(message: str) -> None:
    raise SystemExit("paper release verification failed: " + message)


def check_integrity() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            fail(f"missing required file: {rel}")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = data.get("files", {})
    if not expected:
        fail("empty manifest")
    for rel, meta in sorted(expected.items()):
        p = ROOT / rel
        try:
            p.resolve().relative_to(ROOT.resolve())
        except ValueError:
            fail(f"unsafe path: {rel}")
        if not p.is_file() or p.stat().st_size != int(meta["size"]) or digest(p) != meta["sha256"]:
            fail(f"manifest mismatch: {rel}")
    companion = ROOT.parent / "artifact"
    support = data.get("companion_files", {})
    if set(support) != {".github/manuscript/verify_release.py"}:
        fail("missing companion verifier binding")
    for rel, meta in support.items():
        p = companion / rel
        if not p.resolve().is_relative_to(companion.resolve()):
            fail(f"unsafe companion path: {rel}")
        if not p.is_file() or p.stat().st_size != int(meta["size"]) or digest(p) != meta["sha256"]:
            fail(f"companion manifest mismatch: {rel}")
    for p in ROOT.rglob("*"):
        if p.is_symlink():
            fail(f"symbolic link is not permitted: {p.relative_to(ROOT)}")
        if any(part in FORBIDDEN_PARTS for part in p.parts):
            fail(f"cache directory is packaged: {p.relative_to(ROOT)}")
    for p in ROOT.glob("*.py"):
        compile(p.read_bytes(), str(p), 'exec', dont_inherit=True)
    print(f"paper-source integrity: PASS ({len(expected)} immutable files)")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--integrity-only", action="store_true")
    mode.add_argument("--build", action="store_true")
    args = parser.parse_args()
    check_integrity()
    if args.build:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.run([sys.executable, "build.py"], cwd=ROOT, env=env)
        if proc.returncode:
            fail(f"build.py exited with {proc.returncode}")
        check_integrity()
        print("paper build, audit, and post-build integrity: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
