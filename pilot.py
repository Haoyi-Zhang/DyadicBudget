#!/usr/bin/env python3
"""Measured discriminating pilot for the exact support implementation."""
import itertools,time,resource,json
from pathlib import Path
from fractions import Fraction as F
from src.dyadic import support,group_support,full_period_budget,pow2
from src.oracle import sweep,group_oracle
from src.checks import require
start=time.process_time();wall=time.monotonic();tests=0;points=0
# Hardest interactions: signed weights, negative arguments, exact ties, open suprema.
for w1,w2 in itertools.product(range(-2,3),repeat=2):
 for a,b in [(F(-3,4),F(5,4)),(F(1,2),F(1,2)),(F(-1,2),F(-1,2)),(F(0),F(3)),(F(1,7),F(9,7))]:
  for lin in [F(-1),F(0),F(2)]:
   w={-1:F(w1),1:F(w2)}
   v=support(w,a,b,lin); o=sweep(w,a,b,lin)
   got=(v.lower.value,v.upper.value,v.lower.attained,v.upper.attained)
   require(got==o[:4],(w,a,b,lin,got,o))
   tests+=1;points+=o[4]
for w1,w2 in itertools.product(range(-2,3),repeat=2):
 w={0:F(w1),2:F(w2)}
 for x,u in [((F(0),F(0)),(F(-1,4),F(1,4))),((F(-1),F(1)),(F(-1,3),F(1,5))),((F(1,2),F(1,2)),(F(0),F(0)))]:
  for c in [F(-2),F(0),F(3)]:
   v=group_support(x,u,c,w);o=group_oracle(x,u,c,w)
   got=(F(v['lower']['value']),F(v['upper']['value']),v['lower']['attained'],v['upper']['attained'])
   require(got==o[:4],(w,x,u,c,got,o))
   tests+=1;points+=o[4]
 for p in [-4,-1,0,2]:
  ww={p:F(w1),p+5:F(w2)};v=support(ww,F(0),pow2(p+5));B=full_period_budget(ww)
  require((-v.lower.value,v.upper.value)==(B,B),(ww,B,v.lower.value,v.upper.value))
  tests+=1
# Very wide precision gap; one interval has exponentially many quantizer thresholds.
v=support({-80:F(1),0:F(-1)},F(0),F(1))
require(v.upper.value==full_period_budget({-80:F(1),0:F(-1)}),('wide-gap',v.upper.value))
tests+=1
# Negative control: independent local envelopes invent error for an unchanging output.
g=group_support((F(0),F(0)),(F(-1,4),F(1,4)),F(1),{0:F(1)})
require(g['lower']['value']=='0' and g['upper']['value']=='0',('negative-control',g))
report={'tests':tests,'oracle_point_evaluations':points,'failures':0,
'negative_control':{'true_budget':'0','independent_envelope':'3/4'},
'wide_gap':{'span_bits':80,'threshold_lower_bound':str(2**80),'pieces':len(v.certificate['pieces']),'budget':str(v.upper.value)},
'cpu_seconds':time.process_time()-start,'wall_seconds':time.monotonic()-wall,
'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'workers':1}
print(json.dumps(report,indent=2))
(Path(__file__).resolve().parent/'results').mkdir(exist_ok=True)
(Path(__file__).resolve().parent/'results'/'pilot.json').write_text(json.dumps(report,indent=2)+'\n')
