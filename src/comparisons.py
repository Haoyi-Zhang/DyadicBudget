"""Range-aware separation baselines from the independent small oracle."""
from fractions import Fraction as F
from .oracle import group_oracle
from .verify import reverse_effect


def separation_bounds(program):
    """Exact marginals but no dependence across distinct channels.

Two exact decompositions are independently relaxed. Their resulting bounds are
incomparable in general, so their pointwise minimum is reported. This is an
analytical baseline implemented here, not an external tool.
"""
    cache = {}
    for name, decl in program['captures'].items():
        x = tuple(map(F, decl['ideal']))
        enc, ana = tuple(map(F, decl['encoding'])), tuple(map(F, decl['analog']))
        u = (enc[0]+ana[0], enc[1]+ana[1])
        ps = {n['exponent'] for n in program['nodes'] if n['op'] == 'round' and n['source'] == name}
        for p in ps:
            for c in [0, 1]:
                v = group_oracle(x, u, F(c), {p: F(1)})
                cache[(name, p, c)] = v[:2]
    rows = []
    for output in program['outputs']:
        ef = reverse_effect(program, output)
        budgets = {}
        for decomposition in [0, 1]:
            lower = upper = F(0)
            for name, decl in program['captures'].items():
                enc, ana = tuple(map(F, decl['encoding'])), tuple(map(F, decl['analog']))
                u = (enc[0]+ana[0], enc[1]+ana[1])
                ws = {k[2]: v for k, v in ef.items() if k[:2] == ('q', name)}
                c = ef.get(('u', name), F(0))-decomposition*sum(ws.values(), F(0))
                lower += min(c*u[0], c*u[1]); upper += max(c*u[0], c*u[1])
                for p, w in ws.items():
                    a, b = cache[(name, p, decomposition)]
                    lower += min(w*a, w*b); upper += max(w*a, w*b)
            for name, dom in program['noises'].items():
                a, b = map(F, dom); c = ef.get(('e', name), F(0))
                lower += min(c*a, c*b); upper += max(c*a, c*b)
            budgets['marginal' if decomposition else 'residual'] = max(-lower, upper, F(0))
        budgets['separation'] = min(budgets.values())
        rows.append(budgets)
    # Each baseline first bounds the complete output vector. Choosing a different
    # decomposition per row would be a stronger hybrid, not the stated minimum
    # of these two vector budgets: max_e min(A_e,B_e) can be below
    # min(max_e A_e,max_e B_e).
    result = {k: max(row[k] for row in rows) for k in ['marginal', 'residual']}
    result['separation'] = min(result.values())
    return {k: str(v) for k, v in result.items()}
