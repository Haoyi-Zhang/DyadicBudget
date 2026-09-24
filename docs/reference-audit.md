# Bibliography and source audit

This note records what was actually checked. It is not a claim that every cited
paper was freshly downloaded or reread during the final reproduction.

## Closure results

The final bibliography contains 62 unique records. All 62 are cited by the
manuscript; there are no missing citation keys and no uncited bibliography rows.
Sixty records use unique DOI identifiers. Two records use unique stable archive
URLs instead: the University of Washington ACCEPT technical report and the AES
E-Library record for the Lipshitz--Wannamaker--Vanderkooy survey. Every entry has an
author, title, year, a type-appropriate venue or institution field, and one of
those persistent locators.

`paper/check_references.py` performs this check with only the Python standard
library. It also locks the corrected high-risk records, compares every bibliography
row with `artifact/reference_audit.csv`, checks per-key citation counts, and writes
`paper/reference-audit-summary.json`. The check is deliberately reproducible and
offline; it does not silently turn DOI syntax checking into a claim that every
publisher page was fetched during reproduction.

## Full-text calibration count

`artifact/external_resources.csv` records 22 full substantive source reads used for
venue and related-work calibration:

- 12 TACO research articles;
- 5 influential or foundational papers;
- 5 adjacent-venue papers.

The numbered sequences are checked for completeness and duplicates. The 2026
publisher version of Shem remains explicitly metadata-only and is not included in
the 22-source full-text count. Seventeen of the 22 calibration sources are also
manuscript references. Five TACO papers were read only to calibrate venue-native
problem framing, evidence, and narrative structure; they are not added to the
bibliography merely to increase its size.

## Material repairs

The final audit found and repaired four conflated records rather than preserving a
nominal reference count at the expense of accuracy:

| Key | Repair |
|---|---|
| `coqinterval` | Replaced a mixed 2012 ITP/other-DOI record with Guillaume Melquiond, IJCAR 2008, pp. 2--17, DOI `10.1007/978-3-540-71070-7_2`. |
| `accept` | Replaced a false proceedings/DOI record with the seven-author University of Washington report UW-CSE-15-01-01 and its archival PDF. |
| `floatx` | Corrected the author list and ACM TOMS 45(4), Article 40, 23-page, 2019 metadata; DOI `10.1145/3368086`. |
| `cpfloat` | Corrected the authors, title, and ACM TOMS 49(2), Article 18, 32-page, 2023 metadata; DOI `10.1145/3585515`. |

The same review completed page/DOI metadata for Ark and Legno, normalized FPTaylor
as an article-number record, corrected the 2026 Shem venue record, and retained an
AES archive URL instead of inventing a DOI for the 1992 dither survey. These records
are executable invariants in `paper/check_references.py`.

## Evidence levels

`artifact/reference_audit.csv` assigns each manuscript reference one of three
explicit evidence levels:

1. full substantive source read for one of the recorded calibration roles;
2. publisher or institutional archive metadata manually reverified for a repaired
   or otherwise high-risk record;
3. persistent identifier, uniqueness, required local fields, and manuscript use
   checked offline, with no claim of a fresh publisher-page fetch or full-text read.

This separation prevents a valid DOI and a full-paper reading from being reported as
if they were the same kind of evidence.
