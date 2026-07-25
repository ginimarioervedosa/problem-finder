"""Export the FastAPI OpenAPI schema to backend/openapi.json.

Run from backend/ (as `make openapi` does) so the problemfinder package resolves.
The committed openapi.json is the bridge between the Pydantic domain models and
the generated frontend types; CI fails when a regeneration produces a diff.
"""

import json
from pathlib import Path

from problemfinder.api.app import create_app


def main() -> None:
    schema = create_app().openapi()
    target = Path(__file__).resolve().parent.parent / "backend" / "openapi.json"
    target.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
