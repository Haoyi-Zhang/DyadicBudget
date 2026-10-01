# Exact-check protocol

The pilot precedes this protocol. The evidence campaign is fixed before its results
are inspected. Its purpose is implementation falsification, not an empirical claim
about hardware, applications, model behavior, or superiority over external tools.

## Model and inclusion

Only the declared affine capture language is admitted. Values and interval
endpoints are exact rationals. Quantizers are zero-offset, unsaturated, parallel,
dyadic nearest converters with ties toward positive infinity. Separate capture
coordinates form a Cartesian admissible set. No experimental input is an executed
neural network, physical measurement, or inherited portfolio workload.

1. Direct support: every pair of exponents in `{-3,-2,-1,0,1}`, every weight pair
   in `{-2,-1,0,1,2}^2`, eleven fixed intervals, and three affine slopes.
2. Envelope coupling: the same exponent and weight pairs, five input/noise boxes,
   and coefficients `{-2,0,3}`; compare both extrema and attainment against an exact,
   independently implemented threshold sweep.
3. Full-period formula: the same pairs and weights plus 500 deterministic seeded
   sparse banks, against both bit blocks and the small threshold oracle.
4. Twelve analytical kernel specimens: source aliases, capture separation, shared
   quantizers, common-mode cancellation, multirate differences, averaging,
   threshold crossing, pre-quantization compensation, and vector composition.
   These are semantic cases, not twelve independent application workloads.
5. Generated language programs: 500 cases, seed 20260914. The generator varies
   signs, affine weights, capture widths, encoding/analog intervals, and output
   reuse. Every nonzero inferred budget is challenged with three strict lower
   budgets: 0, `B/2`, and `999B/1000`. Replay every emitted witness in a separate
   direct interpreter. Sample three additional rational valuations per program to
   test the structural error identity; samples do not establish soundness.
6. Scaling: exponent gaps 8, 16, 32, 80, 128, 256, 512, and 1024 with two nonzero
   weights; also banks of 2, 4, 8, 16, 32, 64, and 128 distinct exponents. No
   threshold oracle runs when more than 200,000 threshold points are required.
7. Mutation checks: corrupt a coefficient, origin, interval endpoint, block,
   endpoint-attainment flag, fiber choice, effect, total budget, or witness and
   verify rejection. Each mutation is an accidental-invalid-artifact model, not an
   offensive exploit or a claim of complete checker security.

## Baselines and exclusions

The initial half-step baseline merges genuinely identical origins and assigns each
distinct quantizer the interval `[-step/2,step/2]`, separating pre-quantization
uncertainty from phase. It is a specified local relaxation, not NumFuzz, Daisy,
Gappa, Fluctuat, Aster, or a performance comparison with those systems. The small
oracle explicitly enumerates exact thresholds, actual ties, and both one-sided
limits. All methods use one process and exact rational arithmetic on the same
instances. Timeouts and failures are retained.

After the initial suites, a limitation was identified: half-step intervals are
unnecessarily weak on narrow source ranges. Two exact-marginal relaxations were
therefore added on all unchanged 512 programs:

- `marginal`: compute each quantizer channel's exact bounded marginal support but
  discard dependence between channels and pre-quantization uncertainty;
- `residual`: retain the capture-uncertainty term with the combined residual bank,
  but separate those two groups;
- `separation`: report the smaller of the two valid exact-marginal relaxations.

This repair was not treated as an untouched preplanned experiment. No input was
removed or selected according to its result.

## Theorem-strength checks

The sharp theorem-validation suite checks every weight vector in `{-3,...,3}` for
banks of one through four consecutive precisions, the transformed norm at its
finitely described extreme points, and convex-fusion extremal examples for
`m in {1,2,3,4,8,16,32,64,128}`. These are derived checks of the written proof, not
a fresh application test set. The checker admission boundary validates the entire
DAG, including unused nodes, without importing the analyzer's validation routine.

The fusion suite checks 781 normalized rational/integer cases, 60 wide-range cases,
and ten static envelope cases derived from five attributed published weight rows.
Those rows are factual coefficients only; the artifact does not reproduce the
source paper's timing constellation, sampling process, signal reconstruction, or
physical experiment.

## Frozen partial-order ablation

A four-interface ablation runs on the same 12 specimens and 500 generated
programs: `halfstep`, `marginal`, `residual`, and `separation`, each compared with
the exact relational budget. These rows are not a total hierarchy: the output- and
residual-marginal decompositions are incomparable, and `separation` is their
pointwise minimum. Ratios are reported only when the exact budget is positive;
zero-budget cases separately count whether a relaxation remains positive. The
ablation asks which discarded relation causes overapproximation. It is not a
population estimate, external-tool benchmark, or post-hoc workload-selection
claim. The selected exact-marginal relaxation is recorded per program so the
reported minimum is auditable rather than a hidden oracle.

## Budgets, repair, and clean reproduction

Use one worker, no GPU, no swap, no external computation, and one bounded suite per
process. Each scientific suite has a 35-second wall timeout. Reserve at least two of
the eight permitted CPU-hours for repair and clean reproduction. Measure CPU, wall
time, and peak resident set size for every command; these are diagnostics, not a
hardware-performance benchmark. Any exact-oracle mismatch, invalid accepted
certificate, failed strict witness, or surviving selected mutation blocks the
corresponding claim until repaired and rerun.

The final clean replay starts from the standalone repository ZIP extracted into an
empty directory and executes, in order: 29 unit tests, pilot, support, envelopes,
periods, programs, scaling, mutations, baselines, separation, fusion, ablation, a
second complete period suite under `python -O`, table export, and example-certificate
replay. The unit tests also launch the pilot under `python -O`. Scientific JSON is compared after
removing only explicitly listed timing/RSS fields; CSV and TeX products are compared
byte-for-byte. Timing differences are permitted, scientific differences are not.
The resulting 15-command-group report is `results/clean-reproduction.json`.
Scientific guards use explicit exceptions rather than removable Python `assert`
statements.
