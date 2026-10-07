"""Finite affine capture language, exact error effects, and direct interpreter.

This implementation does not execute machine-learning models or physical devices.
The contract admits a Cartesian product of closed rational intervals.  Distinct
capture ids denote distinct independently selectable admissible coordinates.
"""
from __future__ import annotations
from fractions import Fraction as F
from copy import deepcopy
from typing import Any
from .dyadic import group_support, pow2, round_dyadic

MAX_NODES = 2048
MAX_SOURCES = 128
MAX_EXPONENT = 2048
MAX_RATIONAL_BITS = 16384


def rational(x: Any) -> F:
    if isinstance(x, bool) or not isinstance(x, (str, int, F)):
        raise ValueError('exact rational required, not floating point')
    q = F(x)
    if max(q.numerator.bit_length(), q.denominator.bit_length()) > MAX_RATIONAL_BITS:
        raise ValueError('rational exceeds admitted bit-size limit')
    return q


def interval(x: Any) -> tuple[F, F]:
    if not isinstance(x, (list, tuple)) or len(x) != 2:
        raise ValueError('interval requires exactly two endpoints')
    a, b = map(rational, x)
    if a > b:
        raise ValueError('empty interval')
    return a, b


def sparse(m: dict) -> dict:
    return {k: v for k, v in m.items() if v}


def combine(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, F(0)) + v
    return sparse(out)


def scale(a: dict, c: F) -> dict:
    return sparse({k: c*v for k, v in a.items()})


def validate(program: dict) -> None:
    if program.get('contract') != 'cartesian-closed-rational-captures':
        raise ValueError('missing Cartesian admissible-set contract')
    captures, noises, nodes = program.get('captures'), program.get('noises'), program.get('nodes')
    if not isinstance(captures, dict) or not isinstance(noises, dict) or not isinstance(nodes, list):
        raise ValueError('captures/noises/nodes have invalid shape')
    if len(captures) + len(noises) > MAX_SOURCES or len(nodes) > MAX_NODES:
        raise ValueError('program exceeds finite implementation admission limits')
    for name, s in captures.items():
        if not isinstance(name, str) or not isinstance(s, dict) or set(s) != {'ideal', 'encoding', 'analog'}:
            raise ValueError('capture requires ideal, encoding, and analog intervals')
        for x in s.values():
            interval(x)
    for name, x in noises.items():
        if not isinstance(name, str):
            raise ValueError('additive-error origin name must be a string')
        interval(x)
    ids: set[str] = set()
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get('id'), str) or n['id'] in ids:
            raise ValueError('invalid or duplicate node id')
        op = n.get('op')
        fields = {'const': {'value'}, 'ideal': {'source'}, 'analog': {'source'},
                  'round': {'source', 'exponent'}, 'noise': {'origin'},
                  'scale': {'arg', 'factor'}, 'add': {'left', 'right'}}
        if op not in fields or set(n) != fields[op] | {'id', 'op'}:
            raise ValueError('unsupported operation or unexpected fields')
        if op in {'ideal', 'analog', 'round'} and n['source'] not in captures:
            raise ValueError('unknown capture; cascaded rounding is not admitted')
        if op == 'round' and (type(n['exponent']) is not int or abs(n['exponent']) > MAX_EXPONENT):
            raise ValueError('dyadic exponent outside implementation bounds')
        if op == 'noise' and n['origin'] not in noises:
            raise ValueError('unknown additive-error origin')
        if op == 'const':
            rational(n['value'])
        if op == 'scale':
            rational(n['factor'])
            if n['arg'] not in ids:
                raise ValueError('forward or unknown argument')
        if op == 'add' and (n['left'] not in ids or n['right'] not in ids):
            raise ValueError('forward or unknown argument')
        ids.add(n['id'])
    outputs = program.get('outputs')
    if not isinstance(outputs, list) or not outputs or any(o not in ids for o in outputs):
        raise ValueError('nonempty known outputs required')


def effects(program: dict) -> list[dict]:
    """Canonical coefficients keyed by ('u',source), ('q',source,p), ('e',origin)."""
    validate(program)
    env: dict[str, dict] = {}
    for n in program['nodes']:
        op = n['op']
        if op in {'const', 'ideal'}:
            out = {}
        elif op == 'analog':
            out = {('u', n['source']): F(1)}
        elif op == 'round':
            out = {('u', n['source']): F(1), ('q', n['source'], n['exponent']): F(1)}
        elif op == 'noise':
            out = {('e', n['origin']): F(1)}
        elif op == 'scale':
            out = scale(env[n['arg']], rational(n['factor']))
        else:
            out = combine(env[n['left']], env[n['right']])
        env[n['id']] = out
    return [env[o] for o in program['outputs']]


def evaluate(program: dict, valuation: dict) -> list[tuple[F, F]]:
    """Direct ideal/implemented value pairs, not evaluation of error effects."""
    validate(program)
    x: dict[str, F] = {}; s: dict[str, F] = {}
    for name, declaration in program['captures'].items():
        vals = valuation['captures'][name]
        for key in ('ideal', 'encoding', 'analog'):
            v = rational(vals[key]); lo, hi = interval(declaration[key])
            if not lo <= v <= hi:
                raise ValueError('capture valuation outside its declared envelope')
        x[name] = rational(vals['ideal'])
        s[name] = sum((rational(vals[k]) for k in ('ideal', 'encoding', 'analog')), F(0))
    noise = {}
    for name, domain in program['noises'].items():
        v = rational(valuation['noises'][name]); lo, hi = interval(domain)
        if not lo <= v <= hi:
            raise ValueError('noise valuation outside envelope')
        noise[name] = v
    env = {}
    for n in program['nodes']:
        op = n['op']
        if op == 'const':
            pair = (rational(n['value']),)*2
        elif op == 'ideal':
            pair = (x[n['source']],)*2
        elif op == 'analog':
            pair = (x[n['source']], s[n['source']])
        elif op == 'round':
            pair = (x[n['source']], round_dyadic(s[n['source']], n['exponent']))
        elif op == 'noise':
            pair = (F(0), noise[n['origin']])
        elif op == 'scale':
            pair = tuple(rational(n['factor'])*v for v in env[n['arg']])
        else:
            pair = tuple(a+b for a, b in zip(env[n['left']], env[n['right']]))
        env[n['id']] = pair
    return [env[o] for o in program['outputs']]


def capture_domain(decl: dict) -> tuple[tuple[F, F], tuple[F, F]]:
    enc, ana = interval(decl['encoding']), interval(decl['analog'])
    return interval(decl['ideal']), (enc[0]+ana[0], enc[1]+ana[1])


def analyze(program: dict) -> dict:
    rows = []
    for effect in effects(program):
        weights_by_capture = {}
        for key, value in effect.items():
            if key[0] == 'q':
                weights_by_capture.setdefault(key[1], {})[key[2]] = value
        groups, boxes = {}, {}
        lo = hi = F(0)
        relaxed_lo = relaxed_hi = F(0)
        for name, decl in program['captures'].items():
            c = effect.get(('u', name), F(0))
            weights = weights_by_capture.get(name, {})
            x, u = capture_domain(decl)
            if not c and not weights:
                continue
            item = group_support(x, u, c, weights)
            groups[name] = item
            lo += F(item['lower']['value']); hi += F(item['upper']['value'])
            independent = sum((abs(w)*pow2(p)/2 for p, w in weights.items()), F(0))
            relaxed_lo += min(c*u[0], c*u[1])-independent
            relaxed_hi += max(c*u[0], c*u[1])+independent
        for name, domain in program['noises'].items():
            c = effect.get(('e', name), F(0))
            if not c:
                continue
            a, b = interval(domain)
            lower, upper = min(c*a, c*b), max(c*a, c*b)
            boxes[name] = {'coefficient': str(c), 'lower': str(lower), 'upper': str(upper)}
            lo += lower; hi += upper
            relaxed_lo += lower; relaxed_hi += upper
        rows.append({'effect': [[*k, str(v)] for k, v in sorted(effect.items())],
                     'groups': groups, 'boxes': boxes, 'lower': str(lo), 'upper': str(hi),
                     'budget': str(max(-lo, hi, F(0))),
                     'independent_budget': str(max(-relaxed_lo, relaxed_hi, F(0)))})
    return {'metric': 'linfinity', 'budget': str(max(F(r['budget']) for r in rows)), 'rows': rows}


def witness(program: dict, result: dict, beta: F) -> dict:
    """Construct a rational strict witness for every 0 <= beta < principal budget."""
    beta = rational(beta)
    B = F(result['budget'])
    if not F(0) <= beta < B:
        raise ValueError('witness requires 0 <= requested budget < inferred budget')
    i = next(i for i, r in enumerate(result['rows']) if F(r['budget']) == B)
    row = result['rows'][i]
    side = 'upper' if F(row['upper']) == B else 'lower'
    margin = B-beta
    share = margin/(2*max(1, len(row['groups'])))
    valuation = {'captures': {}, 'noises': {}}
    for name, decl in program['captures'].items():
        if name not in row['groups']:
            vals = {key: str(interval(domain)[0]) for key, domain in decl.items()}
        else:
            group = row['groups'][name][side]
            ep = group['endpoint']
            r = F(ep['r'])
            if not ep['attained']:
                slope = abs(F(ep['slope']))
                if slope == 0:
                    raise ValueError('zero-slope unattained certificate is invalid')
                epsilon = min((r-F(ep['r_lower']))/2, share/(2*slope))
                if epsilon <= 0:
                    raise ValueError('no rational interior approach to endpoint')
                r -= epsilon
            s = F(ep['shift']) + F(ep['delta'])*ep['n'] + r
            seg = group['segments'][group['chosen_segment']]
            u = F(seg['u_slope'])*s+F(seg['u_constant'])
            enc, ana = interval(decl['encoding']), interval(decl['analog'])
            z = max(enc[0], u-ana[1])
            vals = {'ideal': str(s-u), 'encoding': str(z), 'analog': str(u-z)}
        valuation['captures'][name] = vals
    for name, domain in program['noises'].items():
        a, b = interval(domain)
        coef = F(row['boxes'].get(name, {}).get('coefficient', '0'))
        use_b = (coef >= 0) == (side == 'upper')
        valuation['noises'][name] = str(b if use_b else a)
    values = evaluate(program, valuation)
    errors = [actual-ideal for ideal, actual in values]
    if abs(errors[i]) <= beta:
        raise RuntimeError('internal witness construction failed to violate requested budget')
    return {'requested_budget': str(beta), 'output_index': i, 'side': side,
            'valuation': valuation, 'errors': list(map(str, errors))}
