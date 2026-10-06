# Release verification

This record describes the current internal delivery checks for the frozen model. It
does not claim peer review, proof-assistant certification, acceptance, or physical-
hardware validation.

## Distribution facts

- Paper PDF: `paper/main.pdf` in the matching full project.
- PDF pages: 23, with 20 content pages and references beginning on page 21.
- Embedded-font audit: passed.
- Bibliography: 62 unique cited records, including 60 DOI records and two stable-URL-only records.
- Artifact Python files: 15.
- Retained historical Linux replay: 15 sequential command groups and 29 unit tests.
- Current suite: 33 tests; native Windows library replay exercised 30, with three
  POSIX-dependent tests not run on that host. The ten frozen suite functions and
  current library regressions passed without changing the frozen scientific values.

## Required release gates

1. `python verify_release.py --integrity-only` must validate required files, safe paths,
   the immutable source manifest, Python syntax, and absence of packaged caches.
2. `python run_all.py` must return zero in a writable clean copy. The runner suppresses
   bytecode for itself and all child processes, even when the parent environment does
   not set `PYTHONDONTWRITEBYTECODE`.
3. A second integrity check must pass after replay. `python verify_release.py --run`
   performs the pre-check, replay, and post-check as one controlled entry.
4. The paper's `python build.py` must return zero and enforce page, anonymity,
   bibliography, embedded-font, and LaTeX-log contracts.
5. The full-project and standalone-artifact archives must contain one safe root and no
   symbolic links, absolute paths, path traversal, or packaged bytecode caches.

`results/cache-integrity-validation.json` records the completed writable-clean-copy
sequence. All 34 manifest-listed immutable hashes remained unchanged and no
`__pycache__` directory or `.pyc` file remained. The earlier incomplete pre-repair
attempt is not reported as an observed failure.

`results/frozen-value-baseline-check.json` records a separate comparison with the
untouched originally supplied project archive. It verifies that the repair did not
change the 512 frozen numerical baseline rows or the reported ablation statistics.

## Scientific boundary

The implementation uses exact rational arithmetic and deterministic retained inputs.
Finite executable checks support the implementation and examples; general statements
rely on the written proofs. Saturation, biased quantizers, non-dyadic steps, cascaded
quantizers, nonlinear downstream operators, stochastic or temporal noise, physical-
device calibration, energy, latency, and deployment performance remain outside the
frozen theorem and experiment boundary unless explicitly stated otherwise in the
paper.
