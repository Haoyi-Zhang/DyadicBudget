# Release closure

This record closes the internal research-delivery cycle for the frozen model. It reports checks performed on the packaged sources and generated PDF; it does not claim peer review, proof-assistant certification, acceptance, or real-hardware validation.

## Distribution facts

- Project release date: 2026-09-19
- Paper PDF: `main.pdf`
- PDF pages: 23
- References begin on page: 21
- Embedded fonts check: FAIL
- BibTeX records: 62
- Unique DOI fields: 52
- Additional URL fields: 2
- Artifact Python files: 15

## Required release gates

1. `python run_all.py` must return zero in a clean extraction.
2. `python verify_release.py --integrity-only` must validate the immutable manifest.
3. The paper's `python build.py` must return zero and enforce the page, anonymity, bibliography, font, and log contracts.
4. The full-project and standalone-artifact archives must contain a single safe root and no symbolic links, absolute paths, path traversal, or packaged caches.
5. A second clean extraction must reproduce the retained scientific files without a scientific difference.

## Scientific boundary

The implementation uses exact rational arithmetic and retained deterministic inputs. Finite executable checks support the implementation and examples. General statements rely on the written proofs in the paper. Saturation, biased quantizers, non-dyadic steps, nonlinear downstream operators, stochastic or temporal noise, physical-device calibration, energy, latency, and deployment performance remain outside the frozen theorem and experiment boundary unless explicitly stated otherwise in the paper.
