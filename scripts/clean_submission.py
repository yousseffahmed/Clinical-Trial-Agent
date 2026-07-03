#!/usr/bin/env python3
"""Remove generated development/runtime artifacts before submission."""

from pathlib import Path
import shutil


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
        print(f"removed directory: {path.relative_to(PROJECT_ROOT)}")
    elif path.exists():
        path.unlink()
        print(f"removed file: {path.relative_to(PROJECT_ROOT)}")


def main() -> None:
    # These directory names are generated only; source folders are never
    # selected. Resolving from this script avoids hidden user-specific paths.
    for name in ("venv", ".venv", ".pytest_cache"):
        remove_path(PROJECT_ROOT / name)
    for path in list(PROJECT_ROOT.rglob("__pycache__")):
        remove_path(path)
    for path in list(PROJECT_ROOT.rglob("*.pyc")):
        remove_path(path)
    for path in list(PROJECT_ROOT.rglob(".DS_Store")):
        remove_path(path)

    memory_dir = PROJECT_ROOT / "memory"
    for path in memory_dir.glob("*.db"):
        remove_path(path)

    vector_dir = PROJECT_ROOT / "vector_store"
    if vector_dir.exists():
        for path in vector_dir.iterdir():
            if path.name != ".gitkeep":
                remove_path(path)

    print("submission tree is clean; .env and .env.example were preserved")


if __name__ == "__main__":
    main()
