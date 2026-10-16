"""The capture summary uses Boolean attainment flags, like its support pieces."""
from copy import deepcopy
from fractions import Fraction as F
import unittest
from src.cases import program
from src.language import analyze
from src.verify import check_result

class GroupAttainmentTests(unittest.TestCase):
    def test_numeric_boolean_substitutes_are_rejected(self):
        p=program({0:F(1)})
        r=analyze(p)
        self.assertTrue(check_result(p,r))
        for side in ('lower','upper'):
            expected=r['rows'][0]['groups']['g'][side]['attained']
            for numeric in (int(expected),float(expected)):
                with self.subTest(side=side, numeric=numeric):
                    bad=deepcopy(r)
                    bad['rows'][0]['groups']['g'][side]['attained']=numeric
                    with self.assertRaisesRegex(ValueError,'group optimum'):
                        check_result(p,bad)

    def test_true_boolean_and_exact_support_are_unchanged(self):
        for weights in ({0:F(1)}, {0:F(-1)}, {-1:F(1),0:F(-1)}):
            p=program(weights)
            r=analyze(p)
            self.assertTrue(check_result(p,r))
            for group in r['rows'][0]['groups'].values():
                for side in ('lower','upper'):
                    self.assertIs(type(group[side]['attained']),bool)
