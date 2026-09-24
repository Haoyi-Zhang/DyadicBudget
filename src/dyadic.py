"""Exact support of dyadic nearest-quantizer residuals (standard library only).

Rational endpoints; rounding ties go toward +infinity. No saturation.  Values
called bounds are infima/suprema, not necessarily attained extrema.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as F
from typing import Iterable

ZERO = F(0)
ONE = F(1)


def pow2(p: int) -> F:
    return F(1 << p) if p >= 0 else F(1, 1 << (-p))


def floor(x: F) -> int:
    return x.numerator // x.denominator


def round_dyadic(x: F, p: int) -> F:
    d = pow2(p)
    return d * floor(x / d + F(1, 2))


def cover(start: int, stop: int) -> list[tuple[int, int]]:
    """Disjoint aligned power-of-two cover of the inclusive integer interval."""
    if start < 0:
        raise ValueError('cover expects nonnegative integers')
    result = []
    while start <= stop:
        remaining = stop - start + 1
        k = remaining.bit_length() - 1
        if start:
            k = min(k, (start & -start).bit_length() - 1)
        result.append((start, k))
        start += 1 << k
    return result


@dataclass(frozen=True)
class Endpoint:
    value: F
    attained: bool
    n: int
    r: F
    r_lower: F
    delta: F
    shift: F
    slope: F

    def to_json(self) -> dict:
        return {k: str(v) if isinstance(v, F) else v
                for k, v in self.__dict__.items()}


@dataclass
class Support:
    lower: Endpoint
    upper: Endpoint
    certificate: dict


def pick(candidates: list[Endpoint], upper: bool) -> Endpoint:
    value = (max if upper else min)(e.value for e in candidates)
    same = [e for e in candidates if e.value == value]
    return next((e for e in same if e.attained), same[0])


def coefficients(weights: dict[int, F], delta: F, width: int,
                 linear: F) -> list[F]:
    """Suffix recurrence. Checker uses a separate per-converter derivation."""
    if not weights:
        return [linear * delta * (1 << j) for j in range(width)]
    p0 = min(weights) - 1
    by_h = {p - p0: w for p, w in weights.items()}
    suffix = sum(by_h.values(), ZERO)
    result = []
    for j in range(width):
        here = by_h.get(j + 1, ZERO)
        result.append(delta * (1 << j) * (linear + 2 * here - suffix))
        suffix -= here
    return result


def support(weights: dict[int, F], a: F, b: F,
            linear: F = ZERO, constant: F = ZERO) -> Support:
    """Inf/sup of sum_p w_p*(Q_p(s)-s) + linear*s + constant on [a,b]."""
    if a > b:
        raise ValueError('empty interval')
    weights = {p: w for p, w in weights.items() if w}
    delta = pow2(min(weights) - 1) if weights else ONE
    period = pow2(max(weights)) if weights else ONE
    shift = floor(a / period) * period
    na, nb = floor((a-shift)/delta), floor((b-shift)/delta)
    width = max(nb.bit_length(), max(weights)-min(weights)+1 if weights else 0, 1)
    cs = coefficients(weights, delta, width, linear)
    rho = linear - sum(weights.values(), ZERO)
    constant_shift = constant + linear * shift
    low_prefix = [ZERO]
    high_prefix = [ZERO]
    for x in cs:
        low_prefix.append(low_prefix[-1] + min(ZERO, x))
        high_prefix.append(high_prefix[-1] + max(ZERO, x))

    def fixed(n: int) -> F:
        return constant_shift + sum((c for j, c in enumerate(cs) if (n >> j) & 1), ZERO)

    lowers: list[Endpoint] = []
    uppers: list[Endpoint] = []
    pieces: list[dict] = []

    def partial(n: int, rlo: F, rhi: F, hi_closed: bool) -> None:
        if rlo > rhi or (rlo == rhi and not hi_closed):
            raise ValueError('empty partial cell')
        base = fixed(n)
        for upper, out in [(False, lowers), (True, uppers)]:
            use_high = (rho > 0) == upper if rho else False
            r = rhi if use_high else rlo
            attained = hi_closed if use_high else True
            out.append(Endpoint(base+rho*r, attained, n, r, rlo, delta, shift, rho))
        pieces.append({'kind':'partial','n':n,'rlo':str(rlo),'rhi':str(rhi),
                       'hi_closed':hi_closed,
                       'lower':str(lowers[-1].value),'upper':str(uppers[-1].value)})

    if na == nb:
        partial(na, a-shift-na*delta, b-shift-na*delta, True)
    else:
        partial(na, a-shift-na*delta, delta, False)
        for start, k in cover(na+1, nb-1):
            base = fixed(start)
            for upper, out, prefix in [(False, lowers, low_prefix), (True, uppers, high_prefix)]:
                n = start
                for j in range(k):
                    if (cs[j] > 0 if upper else cs[j] < 0):
                        n |= 1 << j
                use_high = (rho > 0) == upper if rho else False
                r = delta if use_high else ZERO
                value = base+prefix[k]+rho*r
                out.append(Endpoint(value, not use_high, n, r, ZERO, delta, shift, rho))
            pieces.append({'kind':'block','start':start,'k':k,
                           'lower':str(lowers[-1].value),'upper':str(uppers[-1].value)})
        partial(nb, ZERO, b-shift-nb*delta, True)
    low, high = pick(lowers, False), pick(uppers, True)
    cert = {'interval':[str(a),str(b)],'linear':str(linear),'constant':str(constant),
            'weights':[[p,str(w)] for p,w in sorted(weights.items())],
            'delta':str(delta),'shift':str(shift),'coefficients':[str(c) for c in cs],
            'pieces':pieces,'lower':low.to_json(),'upper':high.to_json()}
    return Support(low, high, cert)


def envelope_segments(x: tuple[F,F], u: tuple[F,F], coefficient: F,
                      upper: bool) -> list[tuple[F,F,F,F]]:
    """(s_lo,s_hi,A,B), choosing u=A*s+B on the exact feasible fiber."""
    l,h=x; d,e=u
    if l>h or d>e:
        raise ValueError('empty source interval')
    a,b=l+d,h+e
    choose_max = (coefficient >= 0) == upper
    if choose_max:
        pivot = l+e
        return [(a,pivot,ONE,-l),(pivot,b,ZERO,e)]
    pivot=h+d
    return [(a,pivot,ZERO,d),(pivot,b,ONE,-h)]


def group_support(x: tuple[F,F], u: tuple[F,F], coefficient: F,
                  weights: dict[int,F]) -> dict:
    sides = {}
    for upper, name in [(False,'lower'),(True,'upper')]:
        candidates=[]
        certificates=[]
        for a,b,A,B in envelope_segments(x,u,coefficient,upper):
            s=support(weights,a,b,coefficient*A,coefficient*B)
            ep=s.upper if upper else s.lower
            candidates.append((ep,A,B))
            certificates.append({'u_slope':str(A),'u_constant':str(B),
                                 'support':s.certificate})
        ep=pick([x[0] for x in candidates],upper)
        chosen=next(i for i,c in enumerate(candidates) if c[0] is ep)
        sides[name]={'value':str(ep.value),'attained':ep.attained,
                     'chosen_segment':chosen,'segments':certificates,
                     'endpoint':ep.to_json()}
    return sides


def full_period_budget(weights: dict[int,F]) -> F:
    """Compressed exact support formula; useful for a second algebraic check."""
    items=sorted((p,w) for p,w in weights.items() if w)
    if not items:
        return ZERO
    S=sum((w for _,w in items),ZERO)
    out=pow2(items[0][0])*abs(S)/4
    for i,(p,w) in enumerate(items):
        S-=w
        out+=pow2(p)*abs(w-S)/4
        if i+1<len(items):
            out+=(pow2(items[i+1][0])/4-pow2(p)/2)*abs(S)
    return out
