"""Targeted regression checks; none is a proof of a quantified theorem."""
from copy import deepcopy
from fractions import Fraction as F
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from src.cases import program, specimens
from src.dyadic import support, full_period_budget, round_dyadic, cover
from src.language import analyze, evaluate, validate, witness
from src.oracle import sweep, group_oracle
from src.verify import well_formed, check_result, replay_witness
from src.checks import require
from src.comparisons import separation_bounds

ROOT = Path(__file__).resolve().parents[1]


class Core(unittest.TestCase):
    def test_positive_tie(self):
        self.assertEqual(round_dyadic(F(1,2),0),1)

    def test_negative_tie(self):
        self.assertEqual(round_dyadic(F(-1,2),0),0)

    def test_singleton_tie(self):
        z=support({0:F(1)},F(1,2),F(1,2))
        self.assertEqual((z.lower.value,z.upper.value),(F(1,2),)*2)
        self.assertTrue(z.lower.attained and z.upper.attained)

    def test_unattained_infimum(self):
        z=support({0:F(1)},F(0),F(1))
        self.assertEqual((z.lower.value,z.upper.value),(F(-1,2),F(1,2)))
        self.assertFalse(z.lower.attained)
        self.assertTrue(z.upper.attained)

    def test_no_quantizers(self):
        z=support({},F(-4,7),F(3,5),F(-2),F(1))
        self.assertEqual((z.lower.value,z.upper.value),(F(-1,5),F(15,7)))

    def test_oracle_count_interval(self):
        z=sweep({0:F(1)},F(0),F(1))
        self.assertEqual(z.set_points,3)
        self.assertEqual(z.value_calls,5)

    def test_oracle_count_singleton(self):
        z=sweep({0:F(1)},F(1,2),F(1,2))
        self.assertEqual(z.set_points,1)
        self.assertEqual(z.value_calls,1)

    def test_group_oracle_count_fiber_boundaries(self):
        z=group_oracle((F(0),F(1)),(F(-1,4),F(1,4)),F(1),{0:F(1)})
        # Six threshold-sweep subqueries process shared fiber boundaries again.
        self.assertEqual(z.set_points,14)
        self.assertEqual(z.value_calls,22)

    def test_value_reuse(self):
        self.assertEqual(analyze(specimens()['value_alias'])['budget'],'0')

    def test_converter_reuse(self):
        self.assertEqual(analyze(specimens()['converter_alias'])['budget'],'0')

    def test_distinct_capture_not_alias(self):
        self.assertEqual(analyze(specimens()['separate_captures'])['budget'],'1')

    def test_narrow_range(self):
        self.assertEqual(analyze(specimens()['subthreshold_capture'])['budget'],'0')

    def test_sharp_positive_fusion(self):
        for m in range(1,9):
            weights={i:F(1,2**(i+1)) if i<m-1 else F(1,2**i) for i in range(m)}
            self.assertEqual(full_period_budget(weights),F(1,2))
            self.assertEqual(sum((F(2**i)*w/2 for i,w in weights.items()),F(0)),F(m+1,4))

    def test_strict_approach(self):
        p=program({0:F(1)},('0','1'))
        z=analyze(p)
        w=witness(p,z,F(499999,1000000))
        self.assertTrue(replay_witness(p,w))
        self.assertGreater(abs(F(w['errors'][0])),F(499999,1000000))

    def test_refinement_not_monotone(self):
        self.assertEqual(analyze(specimens()['converter_alias'])['budget'],'0')
        self.assertGreater(F(analyze(specimens()['multirate_difference'])['budget']),0)

    def test_cover_complete(self):
        for a in range(33):
            for b in range(a,40):
                cells=cover(a,b)
                vals=[]
                for start,k in cells:
                    self.assertEqual(start%(1<<k),0)
                    vals.extend(range(start,start+(1<<k)))
                self.assertEqual(vals,list(range(a,b+1)))

    def test_unused_bad_node_rejected(self):
        p=program({0:F(1)})
        p['nodes'].append({'id':'unused','op':'round','source':'missing','exponent':0})
        for fn in (validate,well_formed):
            with self.assertRaises((ValueError,KeyError)):
                fn(p)

    def test_unused_cycle_rejected(self):
        p=program({0:F(1)})
        p['nodes'].append({'id':'unused','op':'scale','arg':'unused','factor':'0'})
        for fn in (validate,well_formed):
            with self.assertRaises(ValueError): fn(p)

    def test_floats_rejected(self):
        p=program({0:F(1)}); p['nodes'][0]['value']=0.1
        for fn in (validate,well_formed):
            with self.assertRaises(ValueError): fn(p)

    def test_boolean_exponent_rejected(self):
        p=program({0:F(1)}); p['nodes'][1]['exponent']=True
        for fn in (validate,well_formed):
            with self.assertRaises(ValueError): fn(p)

    def test_invalid_envelope_rejected(self):
        p=program({0:F(1)}); p['captures']['g']['analog']=['1','-1']
        for fn in (validate,well_formed):
            with self.assertRaises(ValueError): fn(p)

    def test_correlated_contract_rejected(self):
        p=program({0:F(1)}); p['contract']='latent-correlated'
        for fn in (validate,well_formed):
            with self.assertRaises(ValueError): fn(p)

    def test_nonstring_capture_name_rejected(self):
        p=program({0:F(1)})
        p['captures'][7]=p['captures'].pop('g'); p['nodes'][1]['source']=7
        for fn in (validate,well_formed):
            with self.assertRaises(ValueError): fn(p)

    def test_nonstring_noise_name_rejected(self):
        p=program({0:F(1)},noise=('0','1'))
        p['noises'][7]=p['noises'].pop('n')
        next(n for n in p['nodes'] if n['op']=='noise')['origin']=7
        for fn in (validate,well_formed):
            with self.assertRaises(ValueError): fn(p)

    def test_vector_baseline_minimum_after_maximum(self):
        p=program({0:F(1)},x=('0','0'),analog=('-1/4','1/4'),analog_weight=F(1))
        q=program({0:F(1)},x=('-3/8','3/8'),analog=('-1/4','1/4'),analog_weight=F(-1))
        p['captures']['h']=q['captures']['g']
        for node in q['nodes']:
            n=deepcopy(node); n['id']='h_'+n['id']
            for key in ('arg','left','right'):
                if key in n: n[key]='h_'+n[key]
            if 'source' in n: n['source']='h'
            p['nodes'].append(n)
        p['outputs'].append('h_'+q['outputs'][0])
        result=analyze(p)
        self.assertEqual(result['budget'],'1/2')
        self.assertTrue(check_result(p,result))
        self.assertEqual(separation_bounds(p),{'marginal':'1','residual':'3/4','separation':'3/4'})
        # Each standalone row prefers the opposite decomposition.
        row_bounds=[]
        for output in p['outputs']:
            row=deepcopy(p); row['outputs']=[output]
            row_bounds.append(separation_bounds(row))
        self.assertEqual(row_bounds[0],{'marginal':'1/4','residual':'3/4','separation':'1/4'})
        self.assertEqual(row_bounds[1],{'marginal':'1','residual':'1/2','separation':'1/2'})

    def test_baseline_vector_output_order_invariant(self):
        p=specimens()['vector_outputs']
        before=separation_bounds(p)
        p['outputs'].reverse()
        self.assertEqual(separation_bounds(p),before)

    def test_changed_result_rejected(self):
        p=program({0:F(1)}); r=analyze(p); r['budget']='0'
        with self.assertRaises(ValueError): check_result(p,r)

    def test_changed_witness_rejected(self):
        p=program({0:F(1)}); r=analyze(p); w=witness(p,r,F(1,3)); w['errors']=['0']
        with self.assertRaises(ValueError): replay_witness(p,w)

    def test_zero_budget_has_no_nonnegative_violation(self):
        p=specimens()['converter_alias']; r=analyze(p)
        with self.assertRaises(ValueError): witness(p,r,F(0))

    def test_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            packet=Path(directory)/'result.json'
            a=subprocess.run([sys.executable,str(ROOT/'budget.py'),'analyze',str(ROOT/'inputs/example.json'),'--budget','1/10'],capture_output=True,text=True,timeout=10)
            self.assertEqual(a.returncode,0,a.stderr)
            packet.write_text(a.stdout)
            b=subprocess.run([sys.executable,str(ROOT/'budget.py'),'verify',str(packet)],capture_output=True,text=True,timeout=10)
            self.assertEqual(b.returncode,0,b.stderr)
            self.assertTrue(json.loads(b.stdout)['strict_witness_replayed'])

    def test_cli_duplicate_json_key(self):
        with tempfile.TemporaryDirectory() as directory:
            f=Path(directory)/'bad.json'; f.write_text('{"nodes":[],"nodes":[]}')
            r=subprocess.run([sys.executable,str(ROOT/'budget.py'),'analyze',str(f)],capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,2)
            self.assertIn('duplicate JSON',r.stderr)

    def test_scientific_guard_is_not_an_assert(self):
        with self.assertRaises(RuntimeError):
            require(False, 'sentinel')
        run=subprocess.run([sys.executable,'-O','-c',
            'from src.checks import require; require(False, "optimized-sentinel")'],
            cwd=ROOT,capture_output=True,text=True,timeout=10)
        self.assertNotEqual(run.returncode,0)
        self.assertIn('optimized-sentinel',run.stderr)

    def test_pilot_runs_with_optimized_python(self):
        run=subprocess.run([sys.executable,'-O',str(ROOT/'pilot.py')],
            cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)['failures'],0)


if __name__ == '__main__': unittest.main()
