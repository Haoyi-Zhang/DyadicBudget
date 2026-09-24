# Published converter-fusion coefficients

`published-fusion.csv` transcribes only the rational numeric weights in Table II
of Joseph G. McMichael, Shay Maymon, and Alan V. Oppenheim, “Exploiting Cross-Channel
Quantizer Error Correlation in Time-Interleaved Analog-to-Digital Converters,”
ASILOMAR 2011, pp. 525–529. The five rows are parameterizations of one published
fusion design, not five independent applications or measured workloads.

Primary author manuscript:
https://dsp-group.mit.edu/wp-content/uploads/2024/11/AsilomarFinal_McMichael_Maymon_Oppenheim.pdf

Institutional record:
https://dspace.mit.edu/entities/publication/f3cc3287-02a5-4525-bbf8-67e60a2ee300

Source location: PDF page 5, Table II; deterministic residual relationship in
Section IV, equation (3); statistical fusion in equations (13)–(14).
Acquisition: table visually inspected through the primary PDF and exact rational
numeric entries transcribed. No source PDF, diagram, prose, code, recordings,
or simulation results are redistributed. These factual coefficients are the
complete external numerical input consumed by the experiment.

The original ordering is finest precision first, as is this CSV. The local
experiment normalizes the finest step to one, places all parallel reads on the
same exact source, and gives that source a complete coarsest-step period. A
separate explicitly labeled envelope case adds uncertainty in [-1/64,1/64].
Neither case reproduces the source's temporal sampling or reconstruction filter
experiments. Both are static mathematical kernel evaluations. The source's
uniform-phase variance assumptions are not needed for the worst-case support
checks. No new physical noise distribution is asserted.

The transcribed weights are evaluated under this artifact's explicit tie-to-positive-
infinity semantics. No claim is made to reproduce the source's exact threshold
endpoint behavior. Numerical coefficient reuse does not import unstated device
or timing assumptions.
