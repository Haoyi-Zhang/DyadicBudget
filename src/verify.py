"""Separate exact certificate replay; imports no analyzer or language module.

The front-end effects are checked by reverse accumulation, rather than the
analyzer's forward construction.  Bit coefficients are obtained by summing
individual converter signatures, rather than a suffix recurrence.  This is a
second implementation by the same research executor, NOT a verified proof
assistant or an independent external review.
"""
from fractions import Fraction as F
from .exact_io import exact_value


def need(condition, message):
    if not condition:
        raise ValueError(message)


def p2(p):
    return F(2**p) if p >= 0 else F(1, 2**(-p))


def fl(x):
    return x.numerator//x.denominator


def bounds(pair):
    a, b = map(F, pair)
    need(a <= b, 'invalid domain')
    return a, b


def check_support(cert, weights, a, b, lam=F(0), const=F(0)):
    """Replay a bounded bit-block support certificate against external inputs."""
    weights = {p: F(w) for p, w in weights.items() if w}
    need(list(map(F, cert['interval'])) == [a, b], 'support domain changed')
    need(F(cert['linear']) == lam and F(cert['constant']) == const, 'affine term changed')
    need(cert['weights'] == [[p, str(w)] for p, w in sorted(weights.items())], 'converter changed')
    delta = p2(min(weights)-1) if weights else F(1)
    period = p2(max(weights)) if weights else F(1)
    shift = fl(a/period)*period
    na, nb = fl((a-shift)/delta), fl((b-shift)/delta)
    width = max(nb.bit_length(), max(weights)-min(weights)+1 if weights else 0, 1)
    need(width <= 32768, 'certificate exceeds replay bit-size limit')
    need(F(cert['delta']) == delta and F(cert['shift']) == shift, 'lattice changed')
    cs = []
    p0 = min(weights)-1 if weights else 0
    for j in range(width):
        coefficient = lam*delta*(1 << j)
        for p, w in weights.items():
            h = p-p0
            if j < h:
                coefficient -= w*delta*(1 << j)
            if j == h-1:
                coefficient += w*delta*(1 << h)
        cs.append(coefficient)
    need(list(map(F, cert['coefficients'])) == cs, 'bit coefficients changed')
    rho = lam-sum(weights.values(), F(0))

    def fixed(n):
        return const+lam*shift+sum((c for j, c in enumerate(cs) if (n >> j) & 1), F(0))

    pieces = cert['pieces']
    need(0 < len(pieces) <= 2*width+4, 'missing or excessive cover')
    candidates = {'lower': [], 'upper': []}
    ranges = []
    cursor = na
    for index, piece in enumerate(pieces):
        if piece['kind'] == 'partial':
            n = piece['n']; rlo, rhi = F(piece['rlo']), F(piece['rhi'])
            closed = piece['hi_closed']
            need(type(n) is int and n == cursor, 'partial cell out of order')
            need(type(closed) is bool, 'endpoint flag must be Boolean')
            need(index == 0 or index == len(pieces)-1, 'internal partial cell')
            expected_lo = a-shift-na*delta if n == na else F(0)
            expected_hi = b-shift-nb*delta if n == nb else delta
            need(rlo == expected_lo and rhi == expected_hi and closed == (n == nb), 'wrong partial-cell boundary')
            need(0 <= rlo <= rhi <= delta and (rlo < rhi or closed), 'empty partial')
            need((n == nb) == (index == len(pieces)-1), 'last cell missing')
            low = fixed(n)+min(rho*rlo, rho*rhi)
            high = fixed(n)+max(rho*rlo, rho*rhi)
            low_att = rho >= 0 or closed
            high_att = rho <= 0 or closed
            ranges.append(('partial', n, n, rlo, rhi, closed))
            cursor = n+1
        else:
            need(piece['kind'] == 'block' and 0 < index < len(pieces)-1, 'invalid block position')
            start, k = piece['start'], piece['k']
            need(type(start) is int and type(k) is int and 0 <= k <= width, 'invalid block integer')
            need(start == cursor and start % (1 << k) == 0, 'noncontiguous or unaligned block')
            stop = start+(1 << k)-1
            need(stop < nb, 'block overlaps final cell')
            low = fixed(start)+sum((min(F(0), c) for c in cs[:k]), F(0))+min(F(0), rho*delta)
            high = fixed(start)+sum((max(F(0), c) for c in cs[:k]), F(0))+max(F(0), rho*delta)
            low_att, high_att = rho >= 0, rho <= 0
            ranges.append(('block', start, stop, F(0), delta, False))
            cursor = stop+1
        need(F(piece['lower']) == low and F(piece['upper']) == high, 'piece support changed')
        candidates['lower'].append((low, low_att))
        candidates['upper'].append((high, high_att))
    need(cursor == nb+1, 'incomplete interval cover')

    result = []
    for side in ('lower', 'upper'):
        value = (min if side == 'lower' else max)(v for v, _ in candidates[side])
        attained = any(att and v == value for v, att in candidates[side])
        ep = cert[side]
        need(F(ep['value']) == value and type(ep['attained']) is bool and ep['attained'] == attained, 'global extremum changed')
        n, r = ep['n'], F(ep['r'])
        need(type(n) is int and na <= n <= nb, 'endpoint index outside cover')
        piece = next(item for item in ranges if item[1] <= n <= item[2])
        _, _, _, rlo, rhi, closed = piece
        need(rlo <= r <= rhi, 'endpoint residual outside cell')
        actual_att = r < rhi or closed
        need(actual_att == attained, 'endpoint attainment inconsistent')
        need(F(ep['delta']) == delta and F(ep['shift']) == shift and F(ep['slope']) == rho and F(ep['r_lower']) == rlo, 'endpoint metadata changed')
        need(fixed(n)+rho*r == value, 'endpoint does not realize claimed limit')
        result.extend([value, attained])
    return tuple(result)


def well_formed(program):
    """Independent grammar and acyclic-graph admission check."""
    need(program.get('contract') == 'cartesian-closed-rational-captures', 'wrong contract')
    captures, noises, nodes = program['captures'], program['noises'], program['nodes']
    need(isinstance(captures, dict) and isinstance(noises, dict) and isinstance(nodes, list), 'bad program shape')
    need(len(captures)+len(noises) <= 128 and len(nodes) <= 2048, 'program too large')
    def rational(value):
        need(not isinstance(value, bool) and isinstance(value, (int, str, F)), 'inexact numeric input')
        v = F(value)
        need(max(v.numerator.bit_length(), v.denominator.bit_length()) <= 16384, 'numeric input too large')
        return v
    for name, cap in captures.items():
        need(isinstance(name, str) and set(cap) == {'ideal', 'encoding', 'analog'}, 'invalid capture declaration')
        for pair in cap.values():
            need(isinstance(pair, (list, tuple)) and len(pair) == 2, 'invalid interval shape')
            need(rational(pair[0]) <= rational(pair[1]), 'empty capture interval')
    for name, pair in noises.items():
        need(isinstance(name, str) and isinstance(pair, (list, tuple)) and len(pair) == 2, 'invalid noise')
        need(rational(pair[0]) <= rational(pair[1]), 'empty noise interval')
    positions = {}
    for i, node in enumerate(nodes):
        need(isinstance(node, dict) and isinstance(node.get('id'), str), 'invalid node')
        need(node['id'] not in positions, 'duplicate id'); positions[node['id']] = i
    extras = {'const': {'value'}, 'ideal': {'source'}, 'analog': {'source'}, 'round': {'source', 'exponent'},
              'noise': {'origin'}, 'scale': {'arg', 'factor'}, 'add': {'left', 'right'}}
    for i, node in enumerate(nodes):
        op = node.get('op')
        need(op in extras and set(node) == extras[op] | {'id', 'op'}, 'unknown grammar form')
        if op in ('ideal', 'analog', 'round'):
            need(node['source'] in captures, 'unbound capture')
        if op == 'round':
            need(type(node['exponent']) is int and abs(node['exponent']) <= 2048, 'invalid exponent')
        if op == 'noise': need(node['origin'] in noises, 'unbound error origin')
        if op == 'const': rational(node['value'])
        if op == 'scale': rational(node['factor'])
        for key in (['left', 'right'] if op == 'add' else ['arg'] if op == 'scale' else []):
            need(node[key] in positions and positions[node[key]] < i, 'non-topological edge')
    outputs = program['outputs']
    need(isinstance(outputs, list) and outputs and all(o in positions for o in outputs), 'invalid outputs')


def reverse_effect(program, output):
    """Reverse-mode linear accumulation directly over the declared DAG."""
    nodes = program['nodes']
    need(len({n['id'] for n in nodes}) == len(nodes), 'duplicate node')
    adj = {output: F(1)}
    effect = {}

    def plus(d, k, c):
        d[k] = d.get(k, F(0))+c

    for n in reversed(nodes):
        a = adj.pop(n['id'], F(0))
        op = n['op']
        if op == 'add':
            plus(adj, n['left'], a); plus(adj, n['right'], a)
        elif op == 'scale':
            plus(adj, n['arg'], a*F(n['factor']))
        elif op == 'round':
            plus(effect, ('q', n['source'], n['exponent']), a)
            plus(effect, ('u', n['source']), a)
        elif op == 'analog':
            plus(effect, ('u', n['source']), a)
        elif op == 'noise':
            plus(effect, ('e', n['origin']), a)
        else:
            need(op in ('ideal', 'const'), 'unrecognized operation')
    need(not any(adj.values()), 'unresolved or forward node dependency')
    return {k: v for k, v in effect.items() if v}


def check_group(item, x, u, c, weights):
    l, h = x; d, e = u
    answer = {}
    for side in ('lower', 'upper'):
        want_max_u = (c >= 0) == (side == 'upper')
        # Derive both endpoints of the projection fiber independently.
        if want_max_u:
            domains = [(l+d, l+e, F(1), -l), (l+e, h+e, F(0), e)]
        else:
            domains = [(l+d, h+d, F(0), d), (h+d, h+e, F(1), -h)]
        data = item[side]
        need(len(data['segments']) == 2, 'fiber segment missing')
        candidates = []
        for seg, (a, b, A, C) in zip(data['segments'], domains):
            need(F(seg['u_slope']) == A and F(seg['u_constant']) == C, 'fiber relation changed')
            v = check_support(seg['support'], weights, a, b, c*A, c*C)
            candidates.append(v[2:] if side == 'upper' else v[:2])
        optimum = (max if side == 'upper' else min)(v for v, _ in candidates)
        att = any(v == optimum and a for v, a in candidates)
        need(F(data['value']) == optimum and data['attained'] == att, 'wrong group optimum')
        chosen = data['chosen_segment']
        need(type(chosen) is int and 0 <= chosen < 2, 'bad selected segment')
        need(candidates[chosen] == (optimum, att), 'selected segment not optimal')
        need(data['endpoint'] == data['segments'][chosen]['support'][side], 'endpoint not tied to certificate')
        answer[side] = optimum
    return answer['lower'], answer['upper']


def check_result(program, result):
    well_formed(program)
    need(program['contract'] == 'cartesian-closed-rational-captures', 'wrong admissible set')
    need(result['metric'] == 'linfinity', 'wrong norm')
    need(len(result['rows']) == len(program['outputs']), 'output count changed')
    total = F(0)
    for out, row in zip(program['outputs'], result['rows']):
        ef = reverse_effect(program, out)
        need(row['effect'] == [[*k, str(v)] for k, v in sorted(ef.items())], 'effect changed')
        expected_groups = {k[1] for k in ef if k[0] in ('u', 'q')}
        expected_boxes = {k[1] for k in ef if k[0] == 'e'}
        need(set(row['groups']) == expected_groups and set(row['boxes']) == expected_boxes, 'lost or extra effect origin')
        low = high = relaxed_low = relaxed_high = F(0)
        for name in expected_groups:
            decl = program['captures'][name]
            enc, ana = bounds(decl['encoding']), bounds(decl['analog'])
            u = (enc[0]+ana[0], enc[1]+ana[1])
            c = ef.get(('u', name), F(0))
            weights = {k[2]: v for k, v in ef.items() if k[:2] == ('q', name)}
            a, b = check_group(row['groups'][name], bounds(decl['ideal']), u, c, weights)
            low += a; high += b
            independent = sum((abs(w)*p2(p)/2 for p, w in weights.items()), F(0))
            relaxed_low += min(c*u[0], c*u[1])-independent
            relaxed_high += max(c*u[0], c*u[1])+independent
        for name in expected_boxes:
            c = ef[('e', name)]; a, b = bounds(program['noises'][name])
            low_b, high_b = min(c*a, c*b), max(c*a, c*b)
            need(row['boxes'][name] == {'coefficient': str(c), 'lower': str(low_b), 'upper': str(high_b)}, 'box support changed')
            low += low_b; high += high_b
            relaxed_low += low_b; relaxed_high += high_b
        budget = max(-low, high, F(0))
        need(F(row['lower']) == low and F(row['upper']) == high and F(row['budget']) == budget, 'row support changed')
        need(F(row['independent_budget']) == max(-relaxed_low, relaxed_high, F(0)), 'baseline changed')
        total = max(total, budget)
    need(F(result['budget']) == total, 'global budget changed')
    return True


def replay_witness(program, wit):
    """Direct mathematical semantics without the analyzer's interpreter."""
    well_formed(program)
    v = wit['valuation']; xs = {}; ss = {}; ns = {}
    for name, domain in program['captures'].items():
        parts = v['captures'][name]
        for key in ('ideal', 'encoding', 'analog'):
            a, b = bounds(domain[key]); q = exact_value(parts[key])
            need(a <= q <= b, 'inadmissible capture witness')
        xs[name] = exact_value(parts['ideal'])
        ss[name] = sum((exact_value(parts[k]) for k in ('ideal', 'encoding', 'analog')), F(0))
    for name, domain in program['noises'].items():
        a, b = bounds(domain); q = exact_value(v['noises'][name])
        need(a <= q <= b, 'inadmissible noise witness'); ns[name] = q
    ideal, actual = {}, {}
    for n in program['nodes']:
        name, op = n['id'], n['op']
        if op == 'const':
            i = z = F(n['value'])
        elif op == 'ideal':
            i = z = xs[n['source']]
        elif op == 'analog':
            i, z = xs[n['source']], ss[n['source']]
        elif op == 'round':
            i = xs[n['source']]; d = p2(n['exponent']); q = ss[n['source']]/d+F(1, 2)
            z = d*(q.numerator//q.denominator)
        elif op == 'noise':
            i, z = F(0), ns[n['origin']]
        elif op == 'scale':
            i, z = F(n['factor'])*ideal[n['arg']], F(n['factor'])*actual[n['arg']]
        else:
            need(op == 'add', 'unsupported replay node')
            i = ideal[n['left']]+ideal[n['right']]
            z = actual[n['left']]+actual[n['right']]
        ideal[name], actual[name] = i, z
    errors = [actual[o]-ideal[o] for o in program['outputs']]
    need(list(map(exact_value, wit['errors'])) == errors, 'recorded witness errors changed')
    j = wit['output_index']; beta = exact_value(wit['requested_budget'])
    need(type(j) is int and 0 <= j < len(errors) and beta >= 0, 'invalid witness request')
    need(abs(errors[j]) > beta, 'not a strict budget violation')
    return True
