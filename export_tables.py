#!/usr/bin/env python3
"""Export paper tables and one exact piecewise phase example from local results.

Outputs remain under results/paper. No dependency on the manuscript directory.
"""
from pathlib import Path
from fractions import Fraction as F
import csv
import json
from src.dyadic import round_dyadic
R=Path(__file__).resolve().parent/'results'
O=R/'paper'; O.mkdir(exist_ok=True)

def read(name): return json.loads((R/name).read_text())
def rational(s):
    f=F(s)
    return str(f.numerator) if f.denominator==1 else str(f.numerator)+'/'+str(f.denominator)
def tabular(name, rows):
    (O/name).write_text('\n'.join(' & '.join(row)+r' \\' for row in rows)+'\n'+r'\bottomrule'+'\n')

labels={'common_mode':'Common-mode cancellation','converter_alias':'Converter reuse',
'multirate_difference':'Multirate difference','prequantization_compensation':'Pre-quantization compensation',
'separate_captures':'Separate captures','signed_three_rate':'Signed three-rate bank',
'subthreshold_capture':'Subthreshold capture','three_rate_average':'Three-rate average',
 'threshold_crossing':'Threshold crossing','two_captures_and_box':'Two captures and one box',
 'value_alias':'Value reuse','vector_outputs':'Vector outputs'}
z=[r for r in read('baselines.json') if r['kind']=='specimen']
tabular('specimens.tex',[[labels[r['case']], *['$'+rational(r[k])+'$' for k in ['exact','halfstep','separation']]] for r in z])
tabular('fusion.tex',[[str(r['converters']),*['$'+rational(r[k])+'$' for k in ['exact_budget','separated_budget','ratio','uniform_phase_variance']]] for r in read('fusion.json') if r['uncertainty_radius']=='0'])
tabular('scaling.tex',[[str(r['size']),str(r['bits']),str(r['pieces']),f"{r['certificate_bytes']:,}",r'$2^{'+str(r['size'])+r'}$'] for r in read('scaling.json') if r['kind']=='gap'])
tabular('separation.tex',[[str(r['quantizers']),*['$'+rational(r[k])+'$' for k in ['exact_budget','independent_budget','ratio']]] for r in read('separation.json')])

ab=read('ablation.json')
ab_labels={'halfstep':'Half-step box','marginal':'Per-channel output marginal','residual':'Per-channel residual marginal','separation':'Best separated marginal'}
ab_rows=[]
for key in ['halfstep','marginal','residual','separation']:
    r=ab['strategies'][key]
    ab_rows.append([ab_labels[key], str(r['strict']), '$'+rational(r['median_ratio'])+'$', '$'+rational(r['p90_ratio'])+'$', '$'+rational(r['max_ratio'])+'$', str(r['zero_exact_positive_bound'])])
tabular('ablation.tex',ab_rows)
# d_fine=1/2 and d_coarse=1, weights 1/2,1/2. Threshold-side values are exact.
points=[F(0),F(1,4),F(1,2),F(3,4),F(1)]
vals=[]; tex=[]
for a,b in zip(points,points[1:]):
    value=sum((round_dyadic(a,p)/2 for p in [-1,0]),F(0))-a
    limit=value-(b-a)
    # Every last cell's right endpoint except 1 is excluded from that cell.
    vals.append([str(a),str(b),str(value),str(limit),b==1])
    coords=f'({float(a):.8g},{float(value):.8g}) ({float(b):.8g},{float(limit):.8g})'
    tex.append(r'\addplot[black,thick,no marks] coordinates {'+coords+'};')
    tex.append(r'\addplot[only marks,mark=*,mark size=1.5pt,black] coordinates {'+f'({float(a):.8g},{float(value):.8g})'+'};')
    if b<1:
        tex.append(r'\addplot[only marks,mark=o,mark size=1.7pt,black,mark options={fill=white}] coordinates {'+f'({float(b):.8g},{float(limit):.8g})'+'};')
tex.append(r'\addplot[only marks,mark=*,mark size=1.5pt,black] coordinates {(1,0)};')
with (O/'phase.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['left','right','left_value','right_limit','right_closed']);w.writerows(vals)
(O/'phase-lines.tex').write_text('\n'.join(tex)+'\n')
print('Exported 5 exact tables and an exact phase curve to results/paper')
