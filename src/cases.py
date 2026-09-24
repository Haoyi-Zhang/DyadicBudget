"""Deterministic analytical specimens and finite falsification inputs."""
from fractions import Fraction as F
import random

INTERVALS = [(F(-2), F(2)), (F(0), F(1)), (F(1, 7), F(13, 7)),
             (F(-3, 4), F(-1, 4)), (F(1, 2), F(1, 2)),
             (F(-1, 2), F(-1, 2)), (F(0), F(0)),
             (F(3, 8), F(5, 8)), (F(-1, 100), F(1, 100)),
             (F(-11, 7), F(-5, 7)), (F(31, 16), F(33, 16))]
BOXES = [((F(0), F(0)), (F(-1, 4), F(1, 4))),
         ((F(-1), F(1)), (F(-1, 8), F(1, 8))),
         ((F(1, 2), F(1, 2)), (F(-1, 100), F(1, 100))),
         ((F(-4, 7), F(13, 7)), (F(1, 7), F(3, 7))),
         ((F(-1, 2), F(1, 2)), (F(0), F(0)))]


def program(weights, x=('0', '1'), encoding=('0', '0'), analog=('0', '0'),
            analog_weight=F(0), noise=None):
    """Program whose output is a weighted converter bank plus optional analog."""
    nodes = [{'id': 'zero', 'op': 'const', 'value': '0'}]
    out = 'zero'
    for i, (p, w) in enumerate(sorted(weights.items())):
        nodes.extend([{'id': f'q{i}', 'op': 'round', 'source': 'g', 'exponent': p},
                      {'id': f't{i}', 'op': 'scale', 'arg': f'q{i}', 'factor': str(w)},
                      {'id': f's{i}', 'op': 'add', 'left': out, 'right': f't{i}'}])
        out = f's{i}'
    if analog_weight:
        nodes.extend([{'id': 'a', 'op': 'analog', 'source': 'g'},
                      {'id': 'at', 'op': 'scale', 'arg': 'a', 'factor': str(analog_weight)},
                      {'id': 'as', 'op': 'add', 'left': out, 'right': 'at'}])
        out = 'as'
    noises = {}
    if noise:
        noises['n'] = list(map(str, noise))
        nodes.extend([{'id': 'n', 'op': 'noise', 'origin': 'n'},
                      {'id': 'ns', 'op': 'add', 'left': out, 'right': 'n'}])
        out = 'ns'
    return {'contract': 'cartesian-closed-rational-captures',
            'captures': {'g': {'ideal': list(map(str, x)), 'encoding': list(map(str, encoding)),
                               'analog': list(map(str, analog))}},
            'noises': noises, 'nodes': nodes, 'outputs': [out]}


def specimens():
    cases = {}
    p = program({0: F(1)}, noise=('-1/5', '2/5'))
    q = p['outputs'][0]
    p['nodes'].extend([{'id': 'neg', 'op': 'scale', 'arg': q, 'factor': '-1'},
                       {'id': 'cancel', 'op': 'add', 'left': q, 'right': 'neg'}])
    p['outputs'] = ['cancel']; cases['value_alias'] = p
    p = program({0: F(1)})
    q = p['outputs'][0]
    p['nodes'].extend([{'id': 'second', 'op': 'round', 'source': 'g', 'exponent': 0},
                       {'id': 'neg', 'op': 'scale', 'arg': 'second', 'factor': '-1'},
                       {'id': 'cancel', 'op': 'add', 'left': q, 'right': 'neg'}])
    p['outputs'] = ['cancel']; cases['converter_alias'] = p
    import copy
    p = copy.deepcopy(p)
    p['captures']['h'] = copy.deepcopy(p['captures']['g'])
    p['nodes'][-3]['source'] = 'h'; cases['separate_captures'] = p
    cases['multirate_difference'] = program({-2: F(1), 0: F(-1)})
    p = program({}, analog_weight=F(1), analog=('-1/4', '1/4'))
    q = p['outputs'][0]
    p['nodes'].extend([{'id': 'a2', 'op': 'analog', 'source': 'g'},
                       {'id': 'neg', 'op': 'scale', 'arg': 'a2', 'factor': '-1'},
                       {'id': 'cancel', 'op': 'add', 'left': q, 'right': 'neg'}])
    p['outputs'] = ['cancel']; cases['common_mode'] = p
    cases['subthreshold_capture'] = program({0: F(1)}, x=('0', '0'), analog=('-1/4', '1/4'))
    cases['threshold_crossing'] = program({0: F(1)}, x=('1/2', '1/2'), analog=('-1/100', '1/100'))
    cases['signed_three_rate'] = program({-2: F(1), -1: F(-2), 0: F(1)}, x=('-2', '2'))
    cases['three_rate_average'] = program({-2: F(1, 3), -1: F(1, 3), 0: F(1, 3)})
    cases['prequantization_compensation'] = program({0: F(1)}, x=('-3/8', '3/8'),
                                                   encoding=('-1/16', '1/16'),
                                                   analog=('-1/16', '1/16'), analog_weight=F(-1))
    p = program({-1: F(1)}, encoding=('-1/7', '1/7'), analog=('-1/9', '1/9'), noise=('-1/5', '1/5'))
    p['captures']['h'] = {'ideal': ['-1', '1'], 'encoding': ['0', '0'], 'analog': ['-1/8', '1/8']}
    p['nodes'].extend([{'id': 'hq', 'op': 'round', 'source': 'h', 'exponent': -2},
                       {'id': 'hn', 'op': 'scale', 'arg': 'hq', 'factor': '-2'},
                       {'id': 'sum', 'op': 'add', 'left': p['outputs'][0], 'right': 'hn'}])
    p['outputs'] = ['sum']; cases['two_captures_and_box'] = p
    p = program({-2: F(1), 0: F(-1)})
    p['nodes'].extend([{'id': 'neg', 'op': 'scale', 'arg': p['outputs'][0], 'factor': '-3'},
                       {'id': 'ideal', 'op': 'ideal', 'source': 'g'}])
    p['outputs'].extend(['neg', 'ideal']); cases['vector_outputs'] = p
    return cases


def generated(count=500):
    rng = random.Random(20260914)
    for i in range(count):
        ps = sorted(rng.sample(range(-5, 2), rng.randint(1, 5)))
        weights = {p: F(rng.randint(-3, 3), rng.choice([1, 2, 3])) for p in ps}
        lo = F(rng.randint(-8, 4), 4); hi = lo+F(rng.randint(0, 8), 4)
        z = F(rng.randint(0, 3), 16); a = F(rng.randint(0, 3), 32)
        p = program(weights, x=(lo, hi), encoding=(-z, z), analog=(-a, a),
                    analog_weight=F(rng.randint(-2, 2)), noise=('-1/16', '1/32') if i % 3 == 0 else None)
        if i % 7 == 0:
            out = p['outputs'][0]
            p['nodes'].append({'id': 'extra', 'op': 'scale', 'arg': out, 'factor': '-2'})
            p['outputs'].append('extra')
        yield p
