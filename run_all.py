#!/usr/bin/env python3
"""Run the complete bounded artifact campaign and optionally compare a baseline.

The runner uses one process at a time. Child CPU is measured with POSIX resource
accounting; peak RSS is the cumulative child maximum and remains a diagnostic, not a scientific output.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
import resource
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
DIAGNOSTIC_FIELDS = {
    "analysis_cpu_seconds",
    "cpu_seconds",
    "peak_child_rss_kib",
    "peak_rss_kib",
    "replay_cpu_seconds",
    "wall_seconds",
}


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise RuntimeError(detail)


def display(command: list[str]) -> str:
    shown = list(command)
    if shown and Path(shown[0]).resolve() == Path(sys.executable).resolve():
        shown[0] = "python"
    return " ".join(shown)


def run_command(obligation: str, command: list[str], timeout: int = 35) -> dict[str, Any]:
    env = os.environ.copy()
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
    )
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
    wall = time.perf_counter() - started
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (after.ru_utime + after.ru_stime) - (before.ru_utime + before.ru_stime)
    result: dict[str, Any] = {
        "obligation": obligation,
        "command": display(command),
        "exit_code": process.returncode,
        "passed": process.returncode == 0 and not timed_out,
        "timed_out": timed_out,
        "wall_seconds": wall,
        "cpu_seconds": cpu,
        "peak_child_rss_kib": int(after.ru_maxrss),
    }
    if obligation == "unit":
        match = re.search(r"Ran\s+(\d+)\s+tests?", stderr + "\n" + stdout)
        if match:
            result["tests_run"] = int(match.group(1))
    if obligation in {"pilot", "example"}:
        candidate = stdout.strip()
        try:
            result["result"] = json.loads(candidate)
        except json.JSONDecodeError:
            result["stdout_tail"] = candidate[-2000:]
    if not result["passed"]:
        result["stdout_tail"] = stdout[-4000:]
        result["stderr_tail"] = stderr[-4000:]
    return result


def strip_diagnostics(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: strip_diagnostics(item)
            for key, item in value.items()
            if key not in DIAGNOSTIC_FIELDS
        }
    if isinstance(value, list):
        return [strip_diagnostics(item) for item in value]
    return value


def generated_files(root: Path) -> list[Path]:
    files = [
        path
        for path in (root / "results").rglob("*")
        if path.is_file() and path.name not in {"clean-reproduction.json", "resource-accounting.json"}
    ]
    files.extend(path for path in (root / "inputs").rglob("*") if path.is_file())
    return sorted(files)


def source_files(root: Path) -> list[Path]:
    candidates = [
        root / "budget.py",
        root / "export_tables.py",
        root / "pilot.py",
        root / "reproduce.py",
        root / "run_all.py",
        root / "proofs" / "principal-budgets.md",
        root / "tests" / "test_core.py",
    ]
    candidates.extend(sorted((root / "src").glob("*.py")))
    return [path for path in candidates if path.is_file()]


def compare_file(current: Path, baseline: Path) -> bool:
    if current.suffix == ".json":
        try:
            left = strip_diagnostics(json.loads(current.read_text(encoding="utf-8")))
            right = strip_diagnostics(json.loads(baseline.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return current.read_bytes() == baseline.read_bytes()
        return left == right
    return current.read_bytes() == baseline.read_bytes()


def compare_baseline(baseline_root: Path) -> dict[str, Any]:
    require((baseline_root / "results").is_dir(), f"baseline is not an artifact root: {baseline_root}")
    mismatches: list[str] = []
    current_files = generated_files(ROOT)
    baseline_files = generated_files(baseline_root)
    current_rel = {path.relative_to(ROOT) for path in current_files}
    baseline_rel = {path.relative_to(baseline_root) for path in baseline_files}
    if current_rel != baseline_rel:
        missing = sorted(str(path) for path in baseline_rel - current_rel)
        extra = sorted(str(path) for path in current_rel - baseline_rel)
        mismatches.append(f"generated-file set differs; missing={missing}; extra={extra}")
    for relative in sorted(current_rel & baseline_rel):
        if not compare_file(ROOT / relative, baseline_root / relative):
            mismatches.append(str(relative))

    current_sources = source_files(ROOT)
    baseline_sources = source_files(baseline_root)
    current_source_rel = {path.relative_to(ROOT) for path in current_sources}
    baseline_source_rel = {path.relative_to(baseline_root) for path in baseline_sources}
    if current_source_rel != baseline_source_rel:
        mismatches.append("scientific source-file set differs")
    for relative in sorted(current_source_rel & baseline_source_rel):
        if (ROOT / relative).read_bytes() != (baseline_root / relative).read_bytes():
            mismatches.append(f"source:{relative}")

    return {
        "baseline_label": baseline_root.name,
        "compared_result_and_input_files": len(current_rel & baseline_rel),
        "scientific_source_files_byte_compared": len(current_source_rel & baseline_source_rel),
        "comparison": (
            "JSON compared after removing only the listed diagnostic timing/RSS fields; "
            "other JSON values and all CSV/TeX/input/source bytes compared exactly."
        ),
        "ignored_diagnostic_json_fields": sorted(DIAGNOSTIC_FIELDS),
        "scientific_mismatches": mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baseline",
        type=Path,
        help="optional previously generated artifact root for exact scientific comparison",
    )
    args = parser.parse_args()
    RESULTS.mkdir(exist_ok=True)
    commands: list[tuple[str, list[str], int]] = [
        ("unit", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], 35),
        ("pilot", [sys.executable, "pilot.py"], 35),
    ]
    for suite in (
        "support",
        "envelopes",
        "periods",
        "programs",
        "scaling",
        "mutations",
        "baselines",
        "separation",
        "fusion",
        "ablation",
    ):
        commands.append((suite, [sys.executable, "reproduce.py", "--suite", suite], 35))
    commands.extend(
        [
            ("optimized_periods", [sys.executable, "-O", "reproduce.py", "--suite", "periods"], 35),
            ("tables", [sys.executable, "export_tables.py"], 35),
            ("example", [sys.executable, "budget.py", "verify", "results/example-certificate.json"], 35),
        ]
    )

    results: list[dict[str, Any]] = []
    for obligation, command, timeout in commands:
        print(f"[run_all] {obligation}: {display(command)}", flush=True)
        record = run_command(obligation, command, timeout)
        results.append(record)
        print(
            f"[run_all] {obligation}: exit={record['exit_code']} "
            f"wall={record['wall_seconds']:.3f}s",
            flush=True,
        )
        if not record["passed"]:
            break

    unit = next((record for record in results if record["obligation"] == "unit"), None)
    if unit:
        (RESULTS / "unit-tests.json").write_text(
            json.dumps(
                {
                    "passed": bool(unit["passed"]),
                    "tests_run": int(unit.get("tests_run", 0)),
                    "optimized_guard_regression_included": True,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    all_passed = len(results) == len(commands) and all(record["passed"] for record in results)
    report: dict[str, Any] = {
        "all_commands_passed": all_passed,
        "command_groups": len(commands),
        "commands": results,
        "scope": "One-worker bounded replay of all frozen scientific suites and certificate/table products.",
        "source": "artifact/run_all.py",
        "standalone_without_paper": True,
        "finite_checks_are_not_general_proofs": True,
        "optimized_mode_checks": ["unit-test subprocess for pilot", "full periods suite"],
        "scientific_mismatches": [],
    }
    if args.baseline:
        comparison = compare_baseline(args.baseline.resolve())
        report.update(comparison)
        if comparison["scientific_mismatches"]:
            all_passed = False
            report["all_commands_passed"] = False
    (RESULTS / "clean-reproduction.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not all_passed:
        failed = [record["obligation"] for record in results if not record["passed"]]
        raise RuntimeError(f"artifact campaign failed; failed obligations={failed}; see results/clean-reproduction.json")
    tests = unit.get("tests_run", "unknown") if unit else "unknown"
    print(
        f"Artifact campaign passed: {len(commands)} command groups, {tests} unit tests, "
        "all frozen suites, optimized-mode periods, table export, and certificate replay."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"run_all failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
