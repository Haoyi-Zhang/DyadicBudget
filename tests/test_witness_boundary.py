"""Derived rational coordinates are checked against envelopes, not input sizes."""
from fractions import Fraction as F
import sys
import unittest
from src.cases import program
from src.language import analyze, witness, rational, evaluate
from src.exact_io import exact_value, exact_text
from src.verify import replay_witness


class WitnessBoundaryTests(unittest.TestCase):
    def test_unattained_support_at_input_bit_limit(self):
        old_limit = sys.get_int_max_str_digits() if hasattr(sys, 'get_int_max_str_digits') else None
        p = program({0: F(-1)})
        beta = F(1, 2) - F(1, 1 << 16383)
        self.assertEqual(rational(beta), beta)
        w = witness(p, analyze(p), beta)
        q = exact_value(w['valuation']['captures']['g']['ideal'])
        self.assertEqual(q.denominator.bit_length(), 16386)
        self.assertTrue(replay_witness(p, w))
        self.assertGreater(abs(exact_value(w['errors'][0])), beta)
        self.assertEqual(exact_value(exact_text(beta)), beta)
        if old_limit is not None:
            self.assertEqual(sys.get_int_max_str_digits(), old_limit)

    def test_input_limit_and_domain_checks_remain(self):
        with self.assertRaises(ValueError):
            rational(F(1, 1 << 16384))
        p = program({0: F(-1)})
        w = witness(p, analyze(p), F(1, 4))
        w['valuation']['captures']['g']['ideal'] = '2'
        with self.assertRaises(ValueError):
            evaluate(p, w['valuation'])
        with self.assertRaises(ValueError):
            replay_witness(p, w)


if __name__ == '__main__':
    unittest.main()
