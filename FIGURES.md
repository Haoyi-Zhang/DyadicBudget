## Vector figure reproduction

For the optional Matplotlib figure dependency, install
`requirements-figures.txt` and run `python -B scripts/plot_figures.py`.
This consumes the existing `results/paper/phase.csv`; the scientific exporter
`export_tables.py` remains responsible for its exact rational segment values.
The four segments, five actual values, three excluded right limits, and two
pairs of reference bounds are retained. No sampled curve or experiment is added.
The native asset is `figures/phase.pdf`, copied byte-identically to an existing
sibling paper's `figures/`; `--out` and `--paper-dir` can change destinations.

The packaged unmodified Libertine regular and italic TrueType fonts match the
ACM body's serif family. They come from the
[Libertine project's 5.3.0 distribution](https://sourceforge.net/projects/linuxlibertine/files/linuxlibertine/5.3.0/)
under the retained `fonts/OFL-1.1.txt`, so no system font path is needed.
The legacy `results/paper/phase-lines.tex` remains an unchanged scientific-export
record, not an input to the paper's vector wrapper. Re-exporting scientific
tables therefore cannot restore a PGFPlots container in the paper.
No TeX rendering or model API is used by the vector producer.

The shared-capture schematic is generated separately by
`python -B scripts/draw_schematics.py --out figures`, using the same packaged
Libertine fonts. Its fixed vector asset is `figures/capture.pdf`; pass
`--out ../paper/figures` to regenerate the companion paper copy. Both the phase
plot and the capture schematic are direct Python outputs without a TeX backend.
