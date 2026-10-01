"""Small exact threshold oracle. Independent of digit signatures and covers.

The returned counters have deliberately separate meanings:

``set_points``
    The sum of the endpoint/threshold-set cardinalities processed by each
    threshold-sweep subquery.  A point reused by two subqueries is counted in
    both, because both subqueries process it.

``value_calls``
    The actual number of calls to the scalar objective used by the oracle.
    A sweep evaluates every set point and one midpoint in every adjacent open
    interval, hence ``2 * set_points - 1`` for one nonempty sweep.  Limit values
    extrapolated from a midpoint and the known slope are not additional calls.
"""
from fractions import Fraction as Q
from typing import NamedTuple


class OracleResult(NamedTuple):
    lower: Q
    upper: Q
    lower_attained: bool
    upper_attained: bool
    value_calls: int
    set_points: int


def p2(p):
    return Q(2**p) if p >= 0 else Q(1, 2**(-p))


def rnd(x, p):
    d = p2(p)
    y = x / d + Q(1, 2)
    return d * (y.numerator // y.denominator)


def sweep(weights, a, b, linear=Q(0), constant=Q(0), limit=200000):
    """Enumerate exact ties/endpoints and evaluate one midpoint per open cell."""
    if a > b:
        raise ValueError("empty interval")
    points = {a, b}
    for p in weights:
        d = p2(p)
        lo = a / d - Q(1, 2)
        hi = b / d - Q(1, 2)
        first = -((-lo.numerator) // lo.denominator)
        last = hi.numerator // hi.denominator
        if last - first + 1 > limit:
            raise ValueError("oracle threshold limit")
        for k in range(first, last + 1):
            points.add(d * (k + Q(1, 2)))
    if len(points) > limit:
        raise ValueError("oracle threshold limit")
    points = sorted(points)

    def value(x):
        return constant + linear * x + sum(
            (w * (rnd(x, p) - x) for p, w in weights.items()), Q(0)
        )

    candidates = [(value(x), True) for x in points]
    value_calls = len(points)
    slope = linear - sum(weights.values(), Q(0))
    for left, right in zip(points, points[1:]):
        mid = (left + right) / 2
        vm = value(mid)
        value_calls += 1
        candidates.extend(
            [
                (vm + slope * (left - mid), slope == 0),
                (vm + slope * (right - mid), slope == 0),
            ]
        )
    low = min(t[0] for t in candidates)
    high = max(t[0] for t in candidates)
    return OracleResult(
        low,
        high,
        any(v == low and attained for v, attained in candidates),
        any(v == high and attained for v, attained in candidates),
        value_calls,
        len(points),
    )


def group_oracle(x, u, c, weights):
    """Exact fiber-end oracle with cumulative subquery counters.

    The same boundary may occur in adjacent fiber subqueries, so ``set_points``
    is a cumulative processing count rather than a count of globally unique
    rational coordinates.
    """
    # Separate derivation: eliminate x=s-u; enumerate breakpoints of both fiber ends.
    l, h = x
    d, e = u
    a = l + d
    b = h + e
    cuts = sorted({a, b, l + e, h + d})
    values = []
    value_calls = 0
    set_points = 0
    for lo, hi in zip(cuts, cuts[1:]):
        middle = (lo + hi) / 2
        # Both ends of the fiber suffice for a function linear in u.
        for choose_max in (False, True):
            if choose_max:
                A, B = (Q(0), e) if e <= middle - l else (Q(1), -l)
            else:
                A, B = (Q(0), d) if d >= middle - h else (Q(1), -h)
            z = sweep(weights, lo, hi, c * A, c * B)
            values.append(z)
            value_calls += z.value_calls
            set_points += z.set_points
    if a == b:
        v = sum((w * (rnd(a, p) - a) for p, w in weights.items()), Q(0)) + c * d
        return OracleResult(v, v, True, True, 1, 1)
    low = min(z.lower for z in values)
    high = max(z.upper for z in values)
    return OracleResult(
        low,
        high,
        any(z.lower == low and z.lower_attained for z in values),
        any(z.upper == high and z.upper_attained for z in values),
        value_calls,
        set_points,
    )
