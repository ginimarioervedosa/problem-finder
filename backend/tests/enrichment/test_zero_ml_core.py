"""The zero-ML guarantee at runtime: core imports load no ML library.

The import-linter contract stops direct ML imports outside enrichment.ml;
this test proves the imports inside enrichment.ml really are lazy, by
loading every core entry point in a fresh interpreter and asserting the ML
packages never arrived. It passes identically with and without the ml
extras installed, which is what makes it a guarantee rather than a hope.
"""

import subprocess
import sys

_PROBE = """
import sys
import problemfinder.api.app
import problemfinder.cli.main
import problemfinder.enrichment.ml.review
import problemfinder.enrichment.ml.suggest
import problemfinder.enrichment.run

loaded = {"numpy", "sklearn", "sentence_transformers", "torch"} & set(sys.modules)
sys.exit(f"ML libraries loaded by core imports: {sorted(loaded)}" if loaded else 0)
"""


def test_core_entry_points_never_load_ml_libraries() -> None:
    result = subprocess.run(
        [sys.executable, "-c", _PROBE], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
