"""Small exact threshold oracle. Independent of digit signatures and covers."""
from fractions import Fraction as Q


def p2(p):
    return Q(2**p) if p>=0 else Q(1,2**(-p))


def rnd(x,p):
    d=p2(p); y=x/d+Q(1,2)
    return d*(y.numerator//y.denominator)


def sweep(weights,a,b,linear=Q(0),constant=Q(0),limit=200000):
    if a>b: raise ValueError('empty interval')
    points={a,b}
    for p in weights:
        d=p2(p)
        lo=a/d-Q(1,2); hi=b/d-Q(1,2)
        first=-((-lo.numerator)//lo.denominator)
        last=hi.numerator//hi.denominator
        if last-first+1>limit: raise ValueError('oracle threshold limit')
        for k in range(first,last+1):
            points.add(d*(k+Q(1,2)))
    if len(points)>limit: raise ValueError('oracle threshold limit')
    points=sorted(points)
    def value(x):
        return constant+linear*x+sum((w*(rnd(x,p)-x) for p,w in weights.items()),Q(0))
    candidates=[(value(x),True) for x in points]
    slope=linear-sum(weights.values(),Q(0))
    for left,right in zip(points,points[1:]):
        mid=(left+right)/2
        vm=value(mid)
        candidates.extend([(vm+slope*(left-mid),slope==0),
                           (vm+slope*(right-mid),slope==0)])
    low=min(t[0] for t in candidates); high=max(t[0] for t in candidates)
    return low,high,any(v==low and a for v,a in candidates),any(v==high and a for v,a in candidates),len(points)


def group_oracle(x,u,c,weights):
    # Separate derivation: eliminate x=s-u; enumerate breakpoints of both fiber ends.
    l,h=x;d,e=u;a=l+d;b=h+e
    cuts=sorted({a,b,l+e,h+d})
    values=[]
    n=0
    for lo,hi in zip(cuts,cuts[1:]):
        middle=(lo+hi)/2
        # Both ends of the fiber suffice for a function linear in u.
        for choose_max in (False,True):
            if choose_max:
                A,B=(Q(0),e) if e<=middle-l else (Q(1),-l)
            else:
                A,B=(Q(0),d) if d>=middle-h else (Q(1),-h)
            z=sweep(weights,lo,hi,c*A,c*B)
            values.append(z); n+=z[4]
    if a==b:
        v=sum((w*(rnd(a,p)-a) for p,w in weights.items()),Q(0))+c*d
        return v,v,True,True,1
    low=min(z[0] for z in values); high=max(z[1] for z in values)
    return low,high,any(z[0]==low and z[2] for z in values),any(z[1]==high and z[3] for z in values),n
