#!/usr/bin/env python3
"""
Move root-level Markdown files into docs/reports to de-clutter the repo root.

Rules:
- Only affects files in the repo root matching *.md
- Skips allowlist: README.md, CONTRIBUTING.md, LICENSE.md
- Creates docs/reports if missing
- Prints a summary of moves (dry-run option)

Usage:
  python scripts/utilities/move_root_markdown_to_docs.py --dry-run
  python scripts/utilities/move_root_markdown_to_docs.py
"""

import argparse
from pathlib import Path
import shutil

ALLOWLIST = {"README.md", "CONTRIBUTING.md", "LICENSE.md"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="List actions without moving files")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    reports_dir = repo_root / "docs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    root_md = [p for p in repo_root.glob("*.md") if p.name not in ALLOWLIST]

    moved = []
    for p in root_md:
        dest = reports_dir / p.name
        if args.dry_run:
            print(f"DRY-RUN: would move {p} -> {dest}")
        else:
            try:
                shutil.move(str(p), str(dest))
                moved.append((p, dest))
                print(f"Moved {p.name} -> {dest}")
            except Exception as e:
                print(f"Failed to move {p}: {e}")

    if not args.dry_run:
        print(f"\nDone. Moved {len(moved)} files to {reports_dir}")


if __name__ == "__main__":
    main()

