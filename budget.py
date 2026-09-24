#!/usr/bin/env python3
"""Analyze or replay one finite shared-capture program using exact rationals.

No network, third-party dependencies, or external solver. The CLI applies
Linux process limits; the limits are not a claim that every admitted input
can be solved within them. Failure to finish is not a proof of a budget.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys

MAX_BYTES = 8 * 1024 * 1024


def limits():
    try:
        import resource
        cap = 3 * 1024**3
        resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
        resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    except (ImportError, AttributeError):
        raise RuntimeError("This bounded CLI requires POSIX resource limits")


def load(path: str) -> dict:
    with Path(path).open('rb') as f:
        data = f.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("JSON input exceeds 8 MiB")
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate JSON object key")
            out[key] = value
        return out
    obj = json.loads(data, object_pairs_hook=pairs)
    if not isinstance(obj, dict):
        raise ValueError("a JSON object is required")
    return obj


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    analyze_cmd = sub.add_parser('analyze', help='emit a result with its input and optional strict witness')
    analyze_cmd.add_argument('program')
    analyze_cmd.add_argument('--budget', help='nonnegative exact rational declaration, e.g. 1/10')
    verify_cmd = sub.add_parser('verify', help='replay a saved result without importing the analyzer')
    verify_cmd.add_argument('packet')
    args = parser.parse_args()
    limits()
    try:
        if args.command == 'analyze':
            from src.language import analyze, witness
            from src.verify import check_result, replay_witness
            program = load(args.program)
            result = analyze(program)
            check_result(program, result)
            packet = {'program': program, 'analysis': result}
            if args.budget is not None:
                beta = Fraction(args.budget)
                if beta < 0:
                    raise ValueError('budget must be nonnegative')
                packet['declared_budget'] = str(beta)
                packet['within_budget'] = Fraction(result['budget']) <= beta
                if not packet['within_budget']:
                    packet['witness'] = witness(program, result, beta)
                    replay_witness(program, packet['witness'])
            print(json.dumps(packet, indent=2, sort_keys=True))
        else:
            from src.verify import check_result, replay_witness
            packet = load(args.packet)
            check_result(packet['program'], packet['analysis'])
            if 'declared_budget' in packet:
                beta = Fraction(packet['declared_budget'])
                if beta < 0 or type(packet['within_budget']) is not bool:
                    raise ValueError('invalid budget declaration')
                if packet['within_budget'] != (Fraction(packet['analysis']['budget']) <= beta):
                    raise ValueError('incorrect declaration outcome')
                if not packet['within_budget'] and 'witness' not in packet:
                    raise ValueError('strict-violation witness missing')
                if 'witness' in packet and Fraction(packet['witness']['requested_budget']) != beta:
                    raise ValueError('witness challenges a different budget')
            if 'witness' in packet:
                replay_witness(packet['program'], packet['witness'])
            print(json.dumps({'certificate_replayed': True,
                              'strict_witness_replayed': 'witness' in packet,
                              'budget': packet['analysis']['budget']}))
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError, MemoryError) as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
