# Principal relational error budgets for shared-signal dyadic quantization

This standalone research artifact contains an exact-rational analyzer, a separately
implemented certificate replayer, a threshold-enumeration oracle, complete written
mathematical arguments, and frozen finite validation data. It concerns a specified
static mathematical language, not a physical analog device or a measured software
kernel. The accompanying manuscript is a complete internal scientific draft, but
neither the paper nor this repository is an external submission, an independently
reviewed proof, or a certification of publication priority.

## What the mathematics establishes

For parallel, zero-offset, unsaturated, nearest dyadic quantizers reading the same
frozen signal, the closed convex hull of their joint residual trace admits a
compressed support formula. On consecutive precisions, separating half-step error
intervals loses at most, and sometimes exactly, a factor `(m+1)/2`; the extremal
weights can be nonnegative and sum to one. All normalized full-period minimax
fusers are characterized.

A finite affine capture language preserves signed error origins and reduces its
least closed output-error interval to exact bounded support queries.
Pre-quantization encoding and analog boxes are eliminated through exact fibers
without separating them from quantizer phase. The returned interval is the best
correct abstraction in the closed-interval domain, and its absolute or maximum-norm
projection is principal. A rational admissible input strictly violating every
smaller nonnegative rational declaration can be produced, including when a support
endpoint is only a limit. The certificate theorem states the sufficient replay
obligations under exact arithmetic.

`proofs/principal-budgets.md` contains the hand arguments. These are not
proof-assistant-certified theorems. Python replay, finite exhaustive instances, and
mutation checks are separate implementation evidence. The replayer is a second code
path by the same research executor, not independent human or blind review.

## Run the worked three-rate example

Use Python's standard library on a POSIX/Linux host. No package installation,
network connection, solver, model, API, GPU, external compute, or dataset is needed.
The CLI applies POSIX resource limits, accepts input JSON up to 8 MiB, and limits
itself to 30 CPU seconds and 3 GiB of virtual address space. Exceeding a limit never
certifies a budget.

```sh
python budget.py analyze inputs/example.json --budget 1/10 > example-certificate.json
python budget.py verify example-certificate.json
```

The example averages quantizers of steps `1/4`, `1/2`, and `1`. Its least budget is
`1/6`, while the separated half-step radius is `7/24`; `v=1/2` is an attained strict
witness against the declaration `1/10`. The checker independently rederives effects,
checks all support pieces, and directly evaluates the witness. The retained result
is `results/example-certificate.json`.

## Reproduce the finite evidence

The recommended command runs every frozen obligation sequentially with a 35-second
limit per scientific subprocess. It writes a machine-readable report to
`results/clean-reproduction.json` and returns nonzero on any failure:

```sh
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python run_all.py
```

For a clean-extraction comparison against another artifact root, use:

```sh
python run_all.py --baseline /absolute/path/to/reference-artifact-root
```

The comparison checks all retained scientific input/result products, ignoring only
the named timing/RSS diagnostic fields in JSON, and compares the listed scientific
source/proof files byte-for-byte. It does not treat a timing difference as a
scientific mismatch.

The equivalent explicit sequence is:

```sh
export PYTHONDONTWRITEBYTECODE=1
python -m unittest discover -s tests -v
timeout 35s python pilot.py
for suite in support envelopes periods programs scaling mutations baselines separation fusion ablation; do
    timeout 35s python reproduce.py --suite "$suite" || exit "$?"
done
timeout 35s python -O reproduce.py --suite periods
python export_tables.py
python budget.py verify results/example-certificate.json
```

The supplied campaign contains 15 command groups and 36 current unit tests,
including three portable capture-index regressions. The unit suite also
launches the pilot under `python -O`; all scientific cross-checks use explicit
runtime guards, not removable Python `assert` statements. The protocol and all
post-pilot repairs are documented in `docs/experiment-plan.md`.

The retained Linux clean-reproduction report ran the earlier 29-test suite. The
preceding 33-test suite adds four regressions for vector-baseline aggregation, output-order
invariance, and origin-name admission. Native Windows library replay exercised
30 of that preceding 33-test suite and all ten frozen suite functions; the three
POSIX-dependent tests were not run on that host. Thirty regenerated input/result
products matched the retained scientific values after excluding only the listed
timing/RSS fields. The seven table/phase exports matched as text; six TeX files
differed only in Windows line endings. Historical Linux CPU/RSS values are retained
and are not current-host measurements.

Current analysis indexes each output's quantizer effect coefficients once by
capture rather than filtering the entire effect map for every capture. Signed
coefficients, declared capture order, full unused-input admission, support
certificates, exact-marginal baselines and witnesses are unchanged. This is a
grouping-work change, not a tighter interval, a new support algorithm or a
measured speedup. Frozen CPU/RSS results remain tied to the pre-index sources.
The new tests run in the existing discovery step; their portable standalone
command is:

```sh
python -B -m unittest discover -s tests -p test_capture_index.py -v
```

The release manifest describes current distributed file bytes, not scientific
replay success. Historical replay reports remain unchanged. Source comparison
includes all current test modules and still rejects differing scientific source
bytes when comparing to a genuinely different implementation.

For multiple outputs, each exact-marginal decomposition takes its maximum row
budget before their minimum is selected. The rowwise hybrid is a different,
stronger baseline. This correction leaves all 512 frozen comparison rows and
their reported statistics unchanged.

The 500 seeded programs and 12 analytical specimens are implementation tests, not
512 independent application workloads. The five published fusion rows are
attributed numerical inputs, not a reproduction of the source's physical or
stochastic experiment.

The frozen campaign covers 8,250 support queries, 3,750 capture-envelope queries,
750 full-period comparisons, 512 programs, 1,506 strict program witnesses, 15 scale
cases, 24 invalid mutations, and two excluded-semantics counterexamples. Derived
checks cover 2,800 integer-weight banks, 1,440 transformed-norm vertices, nine
extremal families, 781 normalized cases, 60 wide-range cases, ten published-weight
envelope cases, and ten additional witnesses. The four-interface partial-order ablation evaluates all
512 unchanged programs; the two exact-marginal decompositions are incomparable and
the reported separation row is their pointwise minimum. Counts overlap and must not be summed into a workload-breadth
claim.

`results/clean-reproduction.json` records the clean-extraction replay. Exact budgets,
predicates, witnesses, CSV, and TeX products must agree; CPU/wall time and RSS may
vary. `results/resource-accounting.json` separates measured replay diagnostics from
unmetered literature, editing, rendering, and TeX work rather than inventing an exact
whole-campaign total.

`results/frozen-value-baseline-check.json` records the independent comparison with
the untouched originally supplied project archive: all 512 baseline rows and the
reported 356, `13/12`, `68/49`, `4`, and 57/290/165 statistics are retained.
`results/cache-integrity-validation.json` records the writable-clean-copy sequence
of integrity check, replay, second integrity check, and repeated verifier entry.

The `scientific-checks.yml` workflow is prepared for a flat artifact repository on
Ubuntu 24.04. It enforces the existing failure gates, a 600-second whole-run wall
bound, a 3-GiB address-space limit and CPU limits, and uploads raw output even on
failure. Preparing the workflow is not evidence that a remote run has completed.
`run_all.py` now retains full subprocess stdout/stderr in `results/raw/`; those
logs are diagnostic and excluded from deterministic scientific comparisons.

## Repository map

- `src/language.py`: finite affine DAG admission, signed effects, paired interpreters,
  analyzer integration, and strict witnesses.
- `src/dyadic.py`: phase-bit coefficients, aligned covers, fibers, and full-period
  support.
- `src/oracle.py`: independently written exact threshold sweep, capped at 200,000
  set points, with separate cumulative set-point and actual objective-call counters.
- `src/verify.py`: separate admission, reverse effects, coefficient reconstruction,
  cover replay, and witness evaluation.
- `src/comparisons.py`: specified local relaxation baselines, not external tools.
- `src/cases.py`: deterministic specimens and seeded generator.
- `claim_evidence_ledger.csv`: each material claim mapped to proof, code, input,
  result, and manuscript location.
- `reference_audit.csv` and `docs/reference-audit.md`: per-record bibliography
  evidence depth, locator, calibration role, and corrected high-risk metadata.
- `external_resources.csv`: scientific/workflow sources, access state, and use.
- `run_all.py`: bounded 15-group campaign runner and optional clean-baseline
  comparator.
- `results/paper/`: deterministic TeX table rows and exact phase-curve data.

## Boundaries

The admitted set is a Cartesian product of closed rational intervals. Separate
capture names cannot hide a correlation; every converter attached to one capture
sees the same frozen value. Rounding ties go toward positive infinity. Downstream
affine arithmetic is exact; digital rounding must be supplied as a separate valid
contract. Saturation, offsets, cascades, nonlinear downstream operations, stochastic
tails, Euclidean vector maxima, and empirical energy/speed/device claims are outside
the results. Principality is for this concrete semantics and the closed-interval or
absolute/maximum-norm targets, not every mixed-signal program or abstract domain.
Finite tests do not establish the general proof or universal checker correctness.
No categorical “first” claim is made.

## Provenance and licensing

The exact scientific computations ran locally on CPU and did not invoke an external model service.

See `LICENSE` and `licenses/README.md`. No scholarly PDF, third-party solver,
private material, credentials, or external-model artifact is included. Source
attribution for the five numerical rows is in
`inputs/published-fusion-README.md`; the live-policy and literature boundary is in
`docs/readiness.md`.
