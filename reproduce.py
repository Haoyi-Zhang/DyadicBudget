#!/usr/bin/env python3
"""Run one bounded exact-check suite. No third-party Python dependencies."""
import argparse
import csv
import itertools as it
import json
from pathlib import Path
from fractions import Fraction as F
import random
import resource
import time
from copy import deepcopy
from src.dyadic import support, group_support, full_period_budget, pow2
from src.oracle import sweep, group_oracle
from src.language import analyze, effects, evaluate, witness, capture_domain
from src.verify import check_support, check_result, replay_witness, check_group
from src.cases import INTERVALS, BOXES, specimens, generated
from src.checks import require

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT/'results'


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')


def suite_support():
    rows = []; points = 0
    for ps in it.combinations(range(-3, 2), 2):
        for ws in it.product(range(-2, 3), repeat=2):
            weights = dict(zip(ps, map(F, ws)))
            for a, b in INTERVALS:
                for lam in [F(-2), F(0), F(3)]:
                    s = support(weights, a, b, lam)
                    v = sweep(weights, a, b, lam)
                    expected = (s.lower.value, s.upper.value, s.lower.attained, s.upper.attained)
                    require(expected == v[:4], (weights, a, b, lam, expected, v))
                    check_support(s.certificate, weights, a, b, lam)
                    points += v[4]
                    rows.append([*ps, *ws, str(a), str(b), str(lam), str(s.lower.value), str(s.upper.value), s.lower.attained, s.upper.attained, v[4]])
    with (RESULTS/'support.csv').open('w', newline='') as f:
        w = csv.writer(f); w.writerow(['p','q','wp','wq','a','b','linear','inf','sup','inf_attained','sup_attained','oracle_points']); w.writerows(rows)
    return {'checks': len(rows), 'oracle_points': points, 'failures': 0}


def suite_envelopes():
    rows = []; points = 0
    for ps in it.combinations(range(-3, 2), 2):
        for ws in it.product(range(-2, 3), repeat=2):
            weights = dict(zip(ps, map(F, ws)))
            for j, (x, u) in enumerate(BOXES):
                for c in [F(-2), F(0), F(3)]:
                    s = group_support(x, u, c, weights)
                    actual = (F(s['lower']['value']), F(s['upper']['value']), s['lower']['attained'], s['upper']['attained'])
                    v = group_oracle(x, u, c, weights)
                    require(actual == v[:4], (x, u, c, weights, actual, v))
                    check_group(s, x, u, c, weights)
                    points += v[4]
                    rows.append([*ps, *ws, j, str(c), *map(str, actual), v[4]])
    with (RESULTS/'envelopes.csv').open('w', newline='') as f:
        w = csv.writer(f); w.writerow(['p','q','wp','wq','box','coefficient','inf','sup','inf_attained','sup_attained','oracle_points']); w.writerows(rows)
    return {'checks': len(rows), 'oracle_points': points, 'failures': 0}


def suite_periods():
    cases = [dict(zip(ps, map(F, ws))) for ps in it.combinations(range(-3, 2), 2) for ws in it.product(range(-2, 3), repeat=2)]
    rng = random.Random(1729)
    for _ in range(500):
        ps = rng.sample(range(-6, 3), rng.randint(1, 7))
        cases.append({p: F(rng.randint(-4, 4), rng.choice([1, 2, 3, 5])) for p in ps})
    rows = []
    for ws in cases:
        p = pow2(max(ws)); s = support(ws, F(0), p)
        exact = full_period_budget(ws); v = sweep(ws, F(0), p)
        require(-s.lower.value == s.upper.value == exact, (ws, s.lower.value, s.upper.value, exact))
        require(v[0] == -exact and v[1] == exact, (ws, v, exact))
        rows.append({'weights': [[p, str(w)] for p, w in sorted(ws.items())], 'budget': str(exact)})
    write_json(RESULTS/'periods.json', rows)
    return {'checks': len(rows), 'failures': 0}


def suite_programs():
    named = specimens()
    write_json(ROOT/'inputs'/'specimens.json', named)
    specimen_results = {}; specimen_witnesses = {}; generated_inputs = []; witnesses = []; checks = 0
    for name, p in named.items():
        r = analyze(p); check_result(p, r)
        specimen_results[name] = r
        for beta in ([F(0), F(r['budget'])/2, F(r['budget'])*F(999, 1000)] if F(r['budget']) else []):
            wit = witness(p, r, beta); replay_witness(p, wit)
            specimen_witnesses.setdefault(name, []).append(wit); checks += 1
    write_json(RESULTS/'specimens.json', specimen_results)
    write_json(RESULTS/'specimen-witnesses.json', specimen_witnesses)
    random_results = []
    for index, p in enumerate(generated()):
        generated_inputs.append(p)
        r = analyze(p); check_result(p, r)
        require(F(r['budget']) <= max(F(row['independent_budget']) for row in r['rows']), ('separation-dominance', index, r))
        # End-to-end independent threshold oracle for each product component.
        for ef, row in zip(effects(p), r['rows']):
            lo = hi = F(0)
            for name, decl in p['captures'].items():
                x, u = capture_domain(decl)
                c = ef.get(('u', name), F(0)); ws = {k[2]: v for k, v in ef.items() if k[:2] == ('q', name)}
                z = group_oracle(x, u, c, ws)
                lo += z[0]; hi += z[1]
            for name, dom in p['noises'].items():
                c = ef.get(('e', name), F(0)); a, b = map(F, dom)
                lo += min(c*a, c*b); hi += max(c*a, c*b)
            require((lo, hi) == (F(row['lower']), F(row['upper'])), ('program-oracle', index, lo, hi, row))
        for beta in ([F(0), F(r['budget'])/2, F(r['budget'])*F(999, 1000)] if F(r['budget']) else []):
            wit = witness(p, r, beta); replay_witness(p, wit)
            witnesses.append({'case': index, 'witness': wit}); checks += 1
        for ratio in [F(0), F(1, 3), F(1)]:
            valuation = {'captures': {}, 'noises': {}}
            for name, decl in p['captures'].items():
                valuation['captures'][name] = {key: str(F(d[0])+ratio*(F(d[1])-F(d[0]))) for key, d in decl.items()}
            valuation['noises'] = {name: str(F(d[0])+ratio*(F(d[1])-F(d[0]))) for name, d in p['noises'].items()}
            for ef, (ideal, actual) in zip(effects(p), evaluate(p, valuation)):
                direct = F(0)
                for key, c in ef.items():
                    kind, name = key[:2]
                    if kind == 'e':
                        val = F(valuation['noises'][name])
                    else:
                        cap = valuation['captures'][name]
                        u = F(cap['encoding'])+F(cap['analog'])
                        s = F(cap['ideal'])+u
                        if kind == 'u':
                            val = u
                        else:
                            d = pow2(key[2]); q = s/d+F(1, 2)
                            val = d*(q.numerator//q.denominator)-s
                    direct += c*val
                require(direct == actual-ideal, ('effect-identity', index, ratio, direct, actual-ideal))
        random_results.append({'case': index, 'budget': r['budget'], 'independent_budget': str(max(F(row['independent_budget']) for row in r['rows']))})
    write_json(ROOT/'inputs'/'generated.json', generated_inputs)
    write_json(RESULTS/'generated.json', random_results)
    write_json(RESULTS/'generated-witnesses.json', witnesses)
    return {'specimens': len(named), 'generated_programs': len(random_results), 'strict_witnesses': checks, 'sample_valuations': 3*len(random_results), 'failures': 0}


def suite_scaling():
    rows = []
    for bits in [8, 16, 32, 80, 128, 256, 512, 1024]:
        ws = {-bits: F(1), 0: F(-1)}
        t = time.process_time(); s = support(ws, F(0), F(1)); elapsed = time.process_time()-t
        t = time.process_time(); check_support(s.certificate, ws, F(0), F(1)); replay = time.process_time()-t
        require(-s.lower.value == s.upper.value == F(1, 2), ('gap-scaling', bits, s.lower.value, s.upper.value))
        rows.append({'kind': 'gap', 'size': bits, 'bits': len(s.certificate['coefficients']), 'pieces': len(s.certificate['pieces']),
                     'budget': str(s.upper.value), 'threshold_count': str(1 << bits), 'analysis_cpu_seconds': elapsed,
                     'replay_cpu_seconds': replay, 'certificate_bytes': len(json.dumps(s.certificate).encode())})
    for m in [2, 4, 8, 16, 32, 64, 128]:
        ws = {-i: F((-1)**i, i+1) for i in range(m)}
        t = time.process_time(); s = support(ws, F(0), F(1)); elapsed = time.process_time()-t
        t = time.process_time(); check_support(s.certificate, ws, F(0), F(1)); replay = time.process_time()-t
        require(-s.lower.value == s.upper.value == full_period_budget(ws), ('bank-scaling', m, s.lower.value, s.upper.value))
        rows.append({'kind': 'bank', 'size': m, 'bits': len(s.certificate['coefficients']), 'pieces': len(s.certificate['pieces']),
                     'budget': str(s.upper.value), 'threshold_count': str(1 << (m-1)), 'analysis_cpu_seconds': elapsed,
                     'replay_cpu_seconds': replay, 'certificate_bytes': len(json.dumps(s.certificate).encode())})
    write_json(RESULTS/'scaling.json', rows)
    return {'checks': len(rows), 'failures': 0}


def suite_mutations():
    from src.language import validate
    p = specimens()['two_captures_and_box']; r = analyze(p)
    failures = []
    def reject(name, fn):
        try:
            fn()
        except (ValueError, KeyError, AssertionError, IndexError, TypeError):
            failures.append({'mutation': name, 'rejected': True}); return
        raise RuntimeError('mutation accepted: '+name)
    mutations = [
        ('global-budget', lambda z: z.__setitem__('budget', '0')),
        ('effect-sign', lambda z: z['rows'][0]['effect'][0].__setitem__(-1, '17')),
        ('group-deletion', lambda z: z['rows'][0]['groups'].pop('g')),
        ('origin-alias', lambda z: z['rows'][0]['groups'].__setitem__('g2', z['rows'][0]['groups'].pop('g'))),
        ('metric', lambda z: z.__setitem__('metric', 'l2')),
        ('box-bound', lambda z: z['rows'][0]['boxes']['n'].__setitem__('upper', '0')),
        ('attainment', lambda z: z['rows'][0]['groups']['g']['upper'].__setitem__('attained', not z['rows'][0]['groups']['g']['upper']['attained'])),
        ('fiber-slope', lambda z: z['rows'][0]['groups']['g']['upper']['segments'][0].__setitem__('u_slope', '7')),
        ('fiber-segment-removal', lambda z: z['rows'][0]['groups']['g']['lower']['segments'].pop()),
        ('baseline-bound', lambda z: z['rows'][0].__setitem__('independent_budget', '0')),
    ]
    for name, change in mutations:
        z = deepcopy(r); change(z); reject(name, lambda: check_result(p, z))
    ws = {-4: F(1), 0: F(-1)}; s = support(ws, F(-1, 7), F(13, 7))
    changes = [
        ('coefficient', lambda z: z['coefficients'].__setitem__(0, '99')),
        ('cover-gap', lambda z: z['pieces'].pop(1)),
        ('block-alignment', lambda z: z['pieces'][1].__setitem__('start', z['pieces'][1]['start']+1)),
        ('partial-open', lambda z: z['pieces'][0].__setitem__('hi_closed', True)),
        ('domain', lambda z: z['interval'].__setitem__(0, '0')),
        ('translation', lambda z: z.__setitem__('shift', '0')),
        ('witness-index', lambda z: z['upper'].__setitem__('n', 100000)),
        ('witness-attainment', lambda z: z['lower'].__setitem__('attained', not z['lower']['attained'])),
    ]
    for name, change in changes:
        z = deepcopy(s.certificate); change(z); reject(name, lambda: check_support(z, ws, F(-1, 7), F(13, 7)))
    w = witness(p, r, F(0))
    z = deepcopy(w); z['valuation']['captures']['g']['ideal'] = '999'
    reject('inadmissible-input', lambda: replay_witness(p, z))
    z = deepcopy(w); z['errors'][0] = '0'
    reject('changed-witness-error', lambda: replay_witness(p, z))
    z = deepcopy(w); z['requested_budget'] = '999'
    reject('nonviolating-witness', lambda: replay_witness(p, z))
    z = deepcopy(p); z['nodes'][1]['source'] = z['nodes'][0]['id']
    reject('cascade-is-not-a-capture', lambda: validate(z))
    z = deepcopy(p); z['nodes'][1]['exponent'] = 0.5
    reject('nondyadic-step', lambda: validate(z))
    z = deepcopy(p); z['contract'] = 'correlated-captures'
    reject('cross-capture-correlation', lambda: validate(z))
    # Explicit semantic boundary counterexamples, not mutations of actual implementation.
    def q(x, step): return step*((x/step+F(1, 2)).numerator//(x/step+F(1, 2)).denominator)
    require(q(F(-1, 2), F(1)) != -q(F(1, 2), F(1)), 'tie rule unexpectedly odd')
    require(q(q(F(3, 5), F(1)), F(2)) != q(F(3, 5), F(2)), 'cascade unexpectedly collapsed')
    write_json(RESULTS/'mutations.json', failures)
    return {'rejected_mutations': len(failures), 'boundary_counterexamples': 2, 'failures': 0}


def suite_baselines():
    from src.comparisons import separation_bounds
    named = json.loads((ROOT/'inputs'/'specimens.json').read_text())
    source = json.loads((RESULTS/'specimens.json').read_text())
    programs = json.loads((ROOT/'inputs'/'generated.json').read_text())
    actual = json.loads((RESULTS/'generated.json').read_text())
    rows = []
    for name, p in named.items():
        z = separation_bounds(p); exact = F(source[name]['budget'])
        require(exact <= F(z['separation']), ('baseline-dominance', exact, z))
        rows.append({'kind': 'specimen', 'case': name, 'exact': str(exact),
                     'halfstep': str(max(F(r['independent_budget']) for r in source[name]['rows'])), **z})
    for i, p in enumerate(programs):
        z = separation_bounds(p); exact = F(actual[i]['budget'])
        require(exact <= F(z['separation']), ('baseline-dominance', exact, z))
        rows.append({'kind': 'generated', 'case': str(i), 'exact': str(exact),
                     'halfstep': actual[i]['independent_budget'], **z})
    write_json(RESULTS/'baselines.json', rows)
    return {'checks': len(rows), 'strictly_tighter_than_separation': sum(F(r['exact']) < F(r['separation']) for r in rows), 'failures': 0}



def suite_ablation():
    """Summarize the three abstraction levels on the frozen 512-program corpus.

    Ratios are reported only when the principal budget is positive.  Empirical
    quantiles use the deterministic nearest-rank definition ceil(q*n).
    """
    rows = json.loads((RESULTS/'baselines.json').read_text())
    strategies = ['halfstep', 'marginal', 'residual', 'separation']

    def quantile(values, numerator, denominator):
        values = sorted(values)
        if not values:
            return F(0)
        rank = (numerator * len(values) + denominator - 1) // denominator
        return values[max(1, rank)-1]

    summary = {'programs': len(rows), 'positive_exact': 0, 'zero_exact': 0,
               'strategies': {}, 'selected_relaxation': {'marginal': 0, 'residual': 0, 'tie': 0}}
    ratio_rows = []
    positive = [r for r in rows if F(r['exact']) > 0]
    summary['positive_exact'] = len(positive)
    summary['zero_exact'] = len(rows) - len(positive)
    for name in strategies:
        ratios = [F(r[name]) / F(r['exact']) for r in positive]
        require(all(x >= 1 for x in ratios), ('ablation-underbound', name, ratios))
        summary['strategies'][name] = {
            'strict': sum(x > 1 for x in ratios),
            'equal': sum(x == 1 for x in ratios),
            'zero_exact_positive_bound': sum(F(r['exact']) == 0 and F(r[name]) > 0 for r in rows),
            'median_ratio': str(quantile(ratios, 1, 2)),
            'p90_ratio': str(quantile(ratios, 9, 10)),
            'p95_ratio': str(quantile(ratios, 19, 20)),
            'max_ratio': str(max(ratios, default=F(1))),
        }
        for rank, value in enumerate(sorted(ratios), 1):
            ratio_rows.append({'strategy': name, 'rank': rank, 'count': len(ratios),
                               'fraction': f'{rank}/{len(ratios)}', 'ratio': str(value)})
    for r in rows:
        a, b = F(r['marginal']), F(r['residual'])
        key = 'marginal' if a < b else 'residual' if b < a else 'tie'
        summary['selected_relaxation'][key] += 1
    write_json(RESULTS/'ablation.json', summary)
    with (RESULTS/'ablation.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['strategy','rank','count','fraction','ratio'])
        w.writeheader(); w.writerows(ratio_rows)
    return {'checks': len(rows), 'positive_exact': len(positive),
            'strategies': len(strategies), 'failures': 0}

def suite_separation():
    rows = []; count = 0
    for m in range(1, 5):
        for vals in it.product(range(-3, 4), repeat=m):
            ws = {i-m+1: F(w) for i, w in enumerate(vals)}
            b = full_period_budget(ws)
            t = sum((pow2(p)*abs(w)/2 for p, w in ws.items()), F(0))
            require(b <= t <= F(m+1, 2)*b, ('separation-bound', m, ws, b, t))
            count += 1
    for m in [1, 2, 3, 4, 8, 16, 32, 64, 128]:
        # Finest-first convex weights: 1/2,1/4,...,2^(1-m),2^(1-m).
        ws = {i-m: pow2(-i) if i < m else pow2(1-m) for i in range(1, m+1)}
        require(sum(ws.values(), F(0)) == 1, ('convex-weights', m, ws))
        b = full_period_budget(ws)
        t = sum((pow2(p)*w/2 for p, w in ws.items()), F(0))
        s = support(ws, F(0), F(1)); check_support(s.certificate, ws, F(0), F(1))
        require(b == pow2(-m) == s.upper.value == -s.lower.value, ('extremal-budget', m, b, s.lower.value, s.upper.value))
        require(t/b == F(m+1, 2), ('sharp-ratio', m, t, b))
        if m <= 8:
            z = sweep(ws, F(0), F(1))
            require((z[0], z[1]) == (-b, b), ('extremal-oracle', m, z, b))
        rows.append({'quantizers': m, 'exact_budget': str(b), 'independent_budget': str(t), 'ratio': str(t/b)})
    vertices = 0
    for m in [1, 2, 3, 4, 8, 16, 32]:
        vectors = []
        for i in range(m):
            z = [F(0)]*m; z[i] = F(1, 2); vectors.extend([z, [-v for v in z]])
        for i in range(m):
            for j in range(i+1, m):
                z = [F(0)]*m; z[i] = F(1, 2); z[j] = F(-1, 2)
                vectors.extend([z, [-v for v in z]])
        observed = F(0)
        for y in vectors:
            weights = {i-m+1: 4/pow2(i-m+1)*(y[i]+sum(y[i+1:], F(0))/2) for i in range(m)}
            b = full_period_budget(weights)
            expected = abs(sum(y, F(0)))+sum(map(abs, y), F(0))
            require(b == expected == 1, ('norm-vertex-budget', m, y, b, expected))
            t = sum((pow2(p)*abs(w)/2 for p, w in weights.items()), F(0))
            observed = max(observed, t); vertices += 1
        require(observed == F(m+1, 2), ('norm-operator', m, observed))
    write_json(RESULTS/'separation.json', rows)
    return {'integer_weight_checks': count, 'convex_fusion_examples': len(rows),
            'norm_vertex_checks': vertices, 'failures': 0}


def suite_fusion():
    """Unchanged published numeric weights; exact static kernels, not device runs."""
    from src.cases import program
    rows = []; witnesses = []; wide = 0; normalized = 0
    with (ROOT/'inputs'/'published-fusion.csv').open(newline='') as stream:
        published = list(csv.DictReader(stream))
    for entry in published:
        m = int(entry['converters']); vals = [F(w) for w in entry['weights_finest_first'].split(';')]
        require(len(vals) == m and sum(vals, F(0)) == 1, ('published-weights', entry))
        ws = dict(enumerate(vals)); P = pow2(m-1)
        for uncertainty in [F(0), F(1, 64)]:
            p = program(ws, (F(0), P), (F(0), F(0)), (-uncertainty, uncertainty))
            result = analyze(p); check_result(p, result)
            exact = F(result['budget']); baseline = F(result['rows'][0]['independent_budget'])
            z = group_oracle((F(0), P), (-uncertainty, uncertainty), F(1), ws)
            require((-z[0], z[1]) == (exact, exact) == (F(1,2)+uncertainty,)*2, ('fusion-envelope', entry, uncertainty, z, exact))
            require(baseline == F(m+3, 8)+uncertainty, ('fusion-baseline', entry, uncertainty, baseline))
            y = [pow2(i)*(vals[i]-sum(vals[i+1:], F(0)))/4 for i in range(m)]
            require(y == [F(1,4*m)]*m, ('fusion-transform', entry, y))
            w = witness(p, result, exact*F(999,1000)); replay_witness(p,w)
            witnesses.append({'converters': m, 'uncertainty_radius':str(uncertainty),
                              'program':p, 'result':result, 'witness':w})
            rows.append({'converters':m, 'uncertainty_radius':str(uncertainty),
                         'exact_budget':str(exact), 'separated_budget':str(baseline),
                         'ratio':str(baseline/exact), 'uniform_phase_variance':str(F(m+3,48*m))})
    # Falsify the algebraic characterization of all normalized minimax fusers.
    for m in range(1,6):
        for prefix in it.product(range(-2,3), repeat=m-1):
            vals = list(map(F,prefix))+[F(1-sum(prefix))]
            ws = dict(enumerate(vals)); b = full_period_budget(ws)
            criterion = all(vals[i] >= sum(vals[i+1:],F(0)) for i in range(m))
            require(b >= F(1,2) and (b == F(1,2)) == criterion, ('minimax-characterization', m, vals, b, criterion))
            normalized += 1
    # The full-period envelope corollary: varied signs, offset ranges and widths.
    for m in range(1,6):
        P=pow2(m-1)
        for sign in [-1,1]:
            ws={i:F(sign*((-1)**i),i+1) for i in range(m)}
            b=full_period_budget(ws)
            for c in map(F, [-2,0,3]):
                for offset,width in [(F(-3,7),P),(F(2,5),P+F(1,3))]:
                    u=(F(-1,9),F(2,7)); x=(offset,offset+width)
                    g=group_support(x,u,c,ws); check_group(g,x,u,c,ws)
                    expected=(min(c*u[0],c*u[1])-b,max(c*u[0],c*u[1])+b)
                    require((F(g['lower']['value']),F(g['upper']['value'])) == expected, ('wide-envelope', m, ws, c, x, u, g, expected))
                    require(group_oracle(x,u,c,ws)[:2] == expected, ('wide-oracle', m, ws, c, x, u, expected))
                    wide+=1
    write_json(RESULTS/'fusion.json',rows)
    write_json(RESULTS/'fusion-witnesses.json',witnesses)
    return {'published_weight_rows':len(published), 'static_envelope_cases':len(rows),
            'strict_witnesses':len(witnesses), 'normalized_weight_checks':normalized,
            'wide_range_checks':wide, 'failures':0}


SUITES = {'support': suite_support, 'envelopes': suite_envelopes, 'periods': suite_periods,
          'programs': suite_programs, 'scaling': suite_scaling, 'mutations': suite_mutations,
          'baselines': suite_baselines, 'ablation': suite_ablation, 'separation': suite_separation, 'fusion':suite_fusion}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=SUITES, required=True)
    args = parser.parse_args()
    RESULTS.mkdir(exist_ok=True)
    cpu, wall = time.process_time(), time.monotonic()
    stats = SUITES[args.suite]()
    stats.update({'cpu_seconds': time.process_time()-cpu, 'wall_seconds': time.monotonic()-wall,
                  'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, 'workers': 1})
    write_json(RESULTS/(args.suite+'-summary.json'), stats)
    print(json.dumps(stats, sort_keys=True))


if __name__ == '__main__': main()
