"""Portable owned exact regressions for capture grouping, without timing."""
from copy import deepcopy
from fractions import Fraction as F
import unittest
from unittest.mock import patch
from src.cases import program, specimens
from src import language
from src.oracle import group_oracle
from src.verify import check_result, replay_witness, reverse_effect


def own_program(inactive=20):
    p = program({-1: F(1), 0: F(-1)}, analog_weight=F(-1, 2),
                encoding=('-1/8', '1/8'), analog=('-1/16', '1/16'), noise=('-1/5', '1/4'))
    p['noises']['g'] = p['noises'].pop('n')
    next(n for n in p['nodes'] if n['op'] == 'noise')['origin'] = 'g'
    other = program({-1: F(-1), 0: F(2)}, analog_weight=F(1, 3),
                    encoding=('-1/8', '1/8'), analog=('-1/16', '1/16'))
    p['captures']['h'] = deepcopy(other['captures']['g'])
    for node in other['nodes']:
        n = deepcopy(node); n['id'] = 'h_' + n['id']
        for key in ('arg', 'left', 'right'):
            if key in n:
                n[key] = 'h_' + n[key]
        if 'source' in n:
            n['source'] = 'h'
        p['nodes'].append(n)
    p['outputs'].append('h_' + other['outputs'][0])
    p['nodes'].extend([{'id': 'duplicate', 'op': 'round', 'source': 'g', 'exponent': -1},
                       {'id': 'duplicate_neg', 'op': 'scale', 'arg': 'duplicate', 'factor': '-1'},
                       {'id': 'cancelled', 'op': 'add', 'left': 'duplicate', 'right': 'duplicate_neg'}])
    p['outputs'].append('cancelled')
    for i in range(inactive):
        p['captures'][f'unused{i}'] = deepcopy(p['captures']['g'])
    return p


def oracle_rows(p, result):
    check_result(p, result)
    for output, row in zip(p['outputs'], result['rows']):
        effect = reverse_effect(p, output)
        low = high = F(0)
        for name, decl in p['captures'].items():
            c = effect.get(('u', name), F(0))
            ws = {k[2]: v for k, v in effect.items() if k[:2] == ('q', name)}
            if not c and not ws:
                continue
            x, u = language.capture_domain(decl)
            support = group_oracle(x, u, c, ws)
            item = row['groups'][name]
            if (F(item['lower']['value']), F(item['upper']['value']),
                item['lower']['attained'], item['upper']['attained']) != support[:4]:
                raise AssertionError('group differs from independent threshold oracle')
            low += support.lower; high += support.upper
        for name, domain in p['noises'].items():
            c = effect.get(('e', name), F(0)); a, b = map(F, domain)
            low += min(c*a, c*b); high += max(c*a, c*b)
        if (str(low), str(high)) != (row['lower'], row['upper']):
            raise AssertionError('row differs from independent threshold oracle')


class CaptureIndexTests(unittest.TestCase):
    def test_exact_groups_signed_multioutput_and_cancellation(self):
        for p in [own_program(n) for n in (0, 1, 20, 100)] + list(specimens().values()):
            result = language.analyze(p)
            oracle_rows(p, result)
            if F(result['budget']):
                self.assertTrue(replay_witness(p, language.witness(p, result, F(result['budget']) * F(999, 1000))))
        result = language.analyze(own_program())
        self.assertEqual(list(result['rows'][0]['groups']), ['g'])
        self.assertEqual(list(result['rows'][1]['groups']), ['h'])
        self.assertEqual(list(result['rows'][0]['boxes']), ['g'])
        self.assertEqual(result['rows'][2]['groups'], {})
        self.assertEqual(result['rows'][2]['budget'], '0')

    def test_unused_declarations_and_nodes_still_admitted(self):
        cases = []
        p = own_program(); p['captures']['unused0']['analog'] = ['1', '-1']; cases.append(p)
        p = own_program(); p['nodes'].append({'id': 'unused_bad', 'op': 'round', 'source': 'missing', 'exponent': 0}); cases.append(p)
        p = own_program(); p['nodes'].append({'id': 'unused_cycle', 'op': 'scale', 'arg': 'unused_cycle', 'factor': '0'}); cases.append(p)
        for p in cases:
            with patch.object(language, 'group_support', wraps=language.group_support) as support:
                with self.assertRaises(ValueError):
                    language.analyze(p)
                self.assertEqual(support.call_count, 0)

    def test_one_grouping_traversal_per_output(self):
        class Counted(dict):
            calls = 0
            def items(self):
                self.calls += 1
                return super().items()
        p = own_program(100)
        expected = language.analyze(p)
        effects = [Counted(e) for e in language.effects(p)]
        with patch.object(language, 'effects', return_value=effects):
            self.assertEqual(language.analyze(p), expected)
        # One grouping traversal and the unchanged final sorted effect encoding.
        self.assertEqual([e.calls for e in effects], [2, 2, 2])


if __name__ == '__main__':
    unittest.main()
