"""Small owned rational-I/O regressions; no boundary-sized input generation."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from fractions import Fraction as F
import io
import json
import sys
import unittest
from unittest.mock import patch

import budget
from src import exact_io
from src.language import analyze, evaluate, rational, witness
from src.verify import check_result, replay_witness


def toy():
    return {
        'contract': 'cartesian-closed-rational-captures',
        'captures': {'g': {'ideal': ['-1/3', '2/3'],
                           'encoding': ['0', '0'], 'analog': ['-1/9', '1/9']}},
        'noises': {'n': ['-2/7', '3/7']},
        'nodes': [{'id': 'a', 'op': 'analog', 'source': 'g'},
                  {'id': 'q', 'op': 'round', 'source': 'g', 'exponent': 0},
                  {'id': 's', 'op': 'scale', 'arg': 'q', 'factor': '5/3'},
                  {'id': 't', 'op': 'scale', 'arg': 's', 'factor': '-7/5'},
                  {'id': 'b', 'op': 'add', 'left': 'a', 'right': 't'},
                  {'id': 'n', 'op': 'noise', 'origin': 'n'},
                  {'id': 'out', 'op': 'add', 'left': 'b', 'right': 'n'}],
        'outputs': ['out']}


class ExactPipelineTests(unittest.TestCase):
    def test_analysis_certificate_and_witness_avoid_fraction_str(self):
        p = toy()
        expected = analyze(p)
        # Simulate an unavailable ordinary rational formatter using small values.
        with patch.object(F, '__str__', side_effect=ValueError('ordinary formatting unavailable')):
            result = analyze(p)
            self.assertEqual(result, expected)
            self.assertTrue(check_result(p, result))
            w = witness(p, result, F(0))
            self.assertTrue(replay_witness(p, w))
            self.assertGreater(abs(evaluate(p, w['valuation'])[0][1]
                                   - evaluate(p, w['valuation'])[0][0]), 0)

    def test_checker_and_cli_use_exact_parser(self):
        p = toy()
        p['nodes'][2]['factor'] = '+5 / 3'
        result = analyze(p)
        self.assertTrue(check_result(p, result))
        w = witness(p, result, F(0))
        packet = {'program': p, 'analysis': result, 'declared_budget': '0',
                  'within_budget': False, 'witness': w}
        # Mock POSIX limits and input files only; invoke real CLI analysis/replay.
        out = io.StringIO()
        with patch.object(budget, 'limits'), patch.object(budget, 'load', return_value=p), \
             patch.object(sys, 'argv', ['budget.py', 'analyze', 'owned.json', '--budget', '+0 / 1']), \
             redirect_stdout(out):
            self.assertEqual(budget.main(), 0)
        self.assertEqual(json.loads(out.getvalue())['analysis'], result)
        with patch.object(budget, 'limits'), patch.object(budget, 'load', return_value=packet), \
             patch.object(sys, 'argv', ['budget.py', 'verify', 'owned.json']), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(budget.main(), 0)

    def test_cli_zero_denominator_is_controlled_invalid_input(self):
        p = toy()
        result = analyze(p)
        packet = {'program': p, 'analysis': result}
        bad_program = deepcopy(p)
        bad_program['nodes'][2]['factor'] = '1/0'
        bad_packet = {'program': bad_program, 'analysis': result}
        bad_declaration = {**packet, 'declared_budget': '1/0', 'within_budget': False}
        bad_witness = witness(p, result, F(0))
        bad_witness['valuation']['captures']['g']['ideal'] = '1/0'
        cases = (
            ('program', ['analyze', 'owned.json'], bad_program),
            ('budget', ['analyze', 'owned.json', '--budget', '1/0'], p),
            ('replay program', ['verify', 'owned.json'], bad_packet),
            ('replay budget', ['verify', 'owned.json'], bad_declaration),
            ('replay witness', ['verify', 'owned.json'], {**packet, 'witness': bad_witness}),
        )
        for label, args, data in cases:
            with self.subTest(path=label):
                out, err = io.StringIO(), io.StringIO()
                with patch.object(budget, 'limits'), patch.object(budget, 'load', return_value=data), \
                     patch.object(sys, 'argv', ['budget.py', *args]), \
                     redirect_stdout(out), redirect_stderr(err):
                    self.assertEqual(budget.main(), 2)
                self.assertEqual(out.getvalue(), '')
                self.assertTrue(err.getvalue().startswith('error: ZeroDivisionError:'))
                self.assertNotIn('Traceback', err.getvalue())

    def test_cli_unexpected_internal_errors_propagate(self):
        for error_type in (RuntimeError, AssertionError):
            with self.subTest(error_type=error_type.__name__):
                out, err = io.StringIO(), io.StringIO()
                with patch.object(budget, 'limits'), patch.object(budget, 'load', return_value=toy()), \
                     patch.object(sys, 'argv', ['budget.py', 'analyze', 'owned.json']), \
                     patch('src.language.analyze', side_effect=error_type('owned internal failure')), \
                     redirect_stdout(out), redirect_stderr(err):
                    with self.assertRaisesRegex(error_type, 'owned internal failure'):
                        budget.main()
                self.assertEqual(out.getvalue(), '')
                self.assertEqual(err.getvalue(), '')

    def test_json_integer_types_and_original_input_limits(self):
        for text, expected in (('1_2.5_0e-1', F(5, 4)), ('.125', F(1, 8)),
                               ('-.125', F(-1, 8)), ('3.', F(3)), ('1e2', F(100)),
                               ('1_2 / 3', F(4))):
            self.assertEqual(exact_io.exact_value(text), expected)
        for malformed in ('1__2', '1._2', '1e', '1/2/3'):
            with self.assertRaises(ValueError):
                exact_io.exact_value(malformed)
        data = {'index': 125, 'rational': '5/7', 'flags': [True, None, -9]}
        self.assertEqual(json.loads(exact_io.exact_json_text(data),
                                    parse_int=exact_io.integer_value), data)
        from src import language
        with patch.object(language, 'MAX_RATIONAL_BITS', 3):
            self.assertEqual(rational('7/3'), F(7, 3))
            with self.assertRaises(ValueError):
                rational('8/3')
        for value in (True, 0.5):
            with self.assertRaises(ValueError):
                rational(value)


if __name__ == '__main__':
    unittest.main()
