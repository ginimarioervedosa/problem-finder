"""Enforce the file length ceilings: hard fail above 250 lines, watch list above 150.

Generated files, vendored shadcn/ui components, and Alembic migration versions are
exempt. Run from the repository root; exits non-zero when any file breaks the hard
ceiling, which is how pre-commit and CI enforce the rule mechanically.
"""

import sys
from pathlib import Path

SOFT_CEILING = 150
HARD_CEILING = 250
ROOTS = ["backend/src", "backend/tests", "frontend/src", "frontend/tests", "scripts"]
SUFFIXES = {".py", ".ts", ".tsx"}
EXEMPT_PARTS = {"migrations", "node_modules", "__pycache__"}
EXEMPT_NAMES = {"schema.d.ts", "routeTree.gen.ts"}
EXEMPT_DIRS = {("components", "ui")}


def is_exempt(path: Path) -> bool:
    parts = path.parts
    if EXEMPT_PARTS & set(parts) or path.name in EXEMPT_NAMES:
        return True
    return any(pair in zip(parts, parts[1:]) for pair in EXEMPT_DIRS)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    over_hard: list[tuple[int, Path]] = []
    over_soft: list[tuple[int, Path]] = []
    for root in ROOTS:
        for path in sorted((repo / root).rglob("*")):
            if path.suffix not in SUFFIXES or not path.is_file() or is_exempt(path):
                continue
            lines = len(path.read_text(encoding="utf-8").splitlines())
            rel = path.relative_to(repo)
            if lines > HARD_CEILING:
                over_hard.append((lines, rel))
            elif lines > SOFT_CEILING:
                over_soft.append((lines, rel))

    for lines, rel in sorted(over_soft, reverse=True):
        print(f"watch: {rel} has {lines} lines (soft ceiling {SOFT_CEILING})")
    for lines, rel in sorted(over_hard, reverse=True):
        print(f"FAIL: {rel} has {lines} lines (hard ceiling {HARD_CEILING})")
    if over_hard:
        print(f"\n{len(over_hard)} file(s) over the hard ceiling. Split them.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
