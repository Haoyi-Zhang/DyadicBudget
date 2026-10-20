# Principal relational error budgets for shared-signal dyadic quantization

An exact-rational analyzer for a finite affine capture language, with a separately
implemented certificate replayer, threshold-enumeration oracle, handwritten
proofs, deterministic inputs and frozen finite results.

Quantizers are parallel, zero-offset, unsaturated, nearest dyadic converters
reading the same frozen capture value; ties go toward positive infinity.
Signed origins and pre-quantization uncertainty are retained in the support
calculation. The mathematical model and its interval/absolute/maximum-norm
targets are specified in `proofs/principal-budgets.md`; finite tests are
implementation evidence rather than proof-assistant certification.

## Setup and worked example

Scientific code needs Python 3.10 or newer and the standard library. No package
installation, network, external solver, model API, GPU or external dataset is
required. `environment-lock.json` records the retained Linux/CPython 3.13.5
environment and deterministic controls.

The CLI and complete campaign require POSIX/Linux resource/process-group support.
Run from the standalone repository root:

```sh
python -B budget.py analyze inputs/example.json --budget 1/10 > example-certificate.json
python -B budget.py verify example-certificate.json
```

The example averages quantizer steps `1/4`, `1/2` and `1`. Its least budget
is `1/6`, the separated half-step radius is `7/24`, and `v=1/2` is an
attained strict witness against `1/10`. The saved packet includes its program,
analysis and optional declaration/witness; `results/example-certificate.json`
retains the supplied example.

The CLI rejects duplicate JSON keys and input above 8 MiB, and applies a
30-CPU-second limit and 3 GiB address-space limit. Failure to finish does not
certify a budget. Native Windows supports pure-library analysis/replay and the
portable unit tests, not the bounded CLI or complete runner.

## Reproduction and integrity

Use a writable fresh extraction to keep the supplied measurements unchanged:

```sh
export PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python verify_release.py --integrity-only
python run_all.py
python verify_release.py --integrity-only
```

`python verify_release.py --run` combines integrity, full replay and post-check.
The SHA-256 manifest binds immutable source/input/document/font bytes, excluding
generated result files, logs and itself. The verifier also checks required files,
safe paths, Python syntax and absence of packaged caches.

`run_all.py` runs 15 sequential command groups: the current 45 unit methods,
pilot, ten frozen suites, a second period suite under `python -O`, table
export and example replay. Each child has a 35-second wall timeout and a failed
gate returns nonzero. It refreshes `inputs/`, `results/` and table products
in place, retaining child stdout/stderr under `results/raw/` and a report at
`results/clean-reproduction.json`.

For comparison against a separate artifact root:

```sh
python run_all.py --baseline /absolute/path/to/reference-artifact-root
```

The comparison checks scientific inputs/results, ignoring only the explicitly
listed timing/RSS fields in JSON, and compares scientific source/proof files
byte-for-byte. CSV/TeX products are byte-compared; line endings therefore matter.
A frozen unit-test count is historical metadata, while a fresh run must execute
every current source method.

The current suite has 42 portable methods and three POSIX-only CLI/pilot methods.
Focused portable commands include:

```sh
python -B -m unittest discover -s tests -p test_capture_index.py -v
python -B -m unittest discover -s tests -p test_exact_pipeline.py -v
python -B -m unittest discover -s tests -p test_witness_boundary.py -v
```

The scientific-checks workflow runs the bounded full campaign on Ubuntu 24.04,
with a clean baseline, 600-second whole-run wall limit, 3 GiB address-space limit,
CPU limits and raw-output upload on failure. Full protocol, exclusions and
post-pilot baseline changes remain in `docs/experiment-plan.md`; supported
runtime and release checks are in `docs/REPRODUCIBILITY.md`.

## Inputs, outputs and figures

`inputs/specimens.json` contains 12 analytical semantic specimens;
`inputs/generated.json` contains 500 seeded programs. These are implementation
tests, not 512 independent application workloads. The five attributed fusion
weight rows in `inputs/published-fusion.csv` are numerical inputs, not replay
of their source's physical/stochastic experiment; attribution and restrictions
are in `inputs/published-fusion-README.md`.

`results/` retains exact budgets, supports, strict witnesses, finite suite
summaries, ablations, resource accounting and historical clean-replay records.
`results/current-replay/` keeps native replay output separate from the original
measurements. Historical CPU/RSS values belong to their original source/runtime
boundary and are not current-host performance measurements.

`export_tables.py` reads retained results and writes five exact tables and the
phase-curve data under `results/paper/`; it does not run an experiment.
Optional vector rendering uses `requirements-figures.txt` and
`scripts/plot_figures.py`. See `FIGURES.md` for bundled Libertine font licenses
and output controls; by default the renderer also copies the figure to an
existing sibling paper. Use a private copy or explicit destinations to preserve
a frozen manuscript.

`src/language.py` implements admission, signed effects, analysis and witnesses;
`src/dyadic.py` implements support/fibers; `src/oracle.py` is the separately
written threshold sweep; `src/verify.py` reconstructs and replays certificates.
`src/comparisons.py` contains local relaxation baselines, not external tools.
`claim_evidence_ledger.csv` maps claims to proof/code/input/result consumers.

## Conditions, provenance and licensing

Admissible captures form a Cartesian product of closed rational intervals;
separate names cannot hide a correlation. Downstream affine arithmetic is exact.
Digital rounding requires a separate valid contract. Saturation, offsets,
cascades, nonlinear downstream operations, stochastic tails, Euclidean vector
maxima and empirical device/energy/speed claims are outside the model.
Principality concerns this semantics and these targets, not every mixed-signal
program. Analyzer/replayer code paths share development history.

Original rational parameters retain their 16,384-bit admission bound. Derived
support/budget/witness coordinates use exact chunked conversion without
reapplying the original-input bound; CLI resource limits still apply.

`reference_audit.csv`, `docs/reference-audit.md` and
`external_resources.csv` preserve source identities, reading depth and access
limits, including metadata-only coverage of the 2026 Shem publisher version.
The complete 2024 preprint has a separately recorded comparison. No categorical
priority or policy-compliance claim follows from these records.

The exact scientific computations ran locally on CPU and did not invoke an
external model service. See `LICENSE` and `licenses/README.md`; scholarly PDFs,
third-party solvers, credentials and external-model artifacts are not bundled.

## Source repository

[DyadicBudget](https://github.com/Haoyi-Zhang/DyadicBudget)
