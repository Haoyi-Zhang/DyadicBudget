"""Runtime checks for scientific drivers.

Unlike Python ``assert`` statements, these obligations remain active under
``python -O``.  They are for reproduction-driver invariants, not user-input
validation (which raises ``ValueError`` in the analyzer and replayer).
"""


def require(condition: bool, detail: object = "scientific obligation failed") -> None:
    """Raise ``RuntimeError`` when a scientific cross-check fails."""
    if not condition:
        raise RuntimeError(f"scientific cross-check failed: {detail!r}")
