#!/usr/bin/env python3
"""
Safe output path helpers for reports and generated artifacts.

Goals:
- Centralize where scripts write Markdown/CSV reports.
- Prevent accidental writes to external drives by default.

Env vars:
- CBI_DOCS_DIR: absolute or repo‑relative path for report outputs
- CBI_ALLOW_EXTERNAL_WRITES: set "1" to allow writing outside the repo (default: disallow)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def _repo_root_from_file(file_in_repo: Optional[str] = None) -> Path:
    """Resolve repo root from a file path inside the repo (defaults to this file)."""
    base = Path(file_in_repo or __file__).resolve()
    # Traverse upwards until we find .git or stop
    for parent in [base] + list(base.parents):
        if (parent / ".git").exists():
            return parent
    # Fallback to cwd
    return Path.cwd().resolve()


def get_docs_output_dir(default_subdir: str = "docs") -> Path:
    """Return the directory to write reports to, respecting env overrides.

    Defaults to the repo's `docs/` directory unless CBI_DOCS_DIR is set.
    Ensures the resolved path is inside the repo unless CBI_ALLOW_EXTERNAL_WRITES=1.
    """
    repo_root = _repo_root_from_file()

    cfg = os.getenv("CBI_DOCS_DIR")
    if cfg:
        out_dir = Path(cfg)
        out_dir = (repo_root / out_dir).resolve() if not out_dir.is_absolute() else out_dir.resolve()
    else:
        out_dir = (repo_root / default_subdir).resolve()

    allow_external = os.getenv("CBI_ALLOW_EXTERNAL_WRITES", "0") == "1"
    if not allow_external:
        # Enforce writes within repo
        try:
            out_dir.relative_to(repo_root)
        except ValueError:
            # If outside repo, fallback to repo/docs
            out_dir = (repo_root / default_subdir).resolve()

    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def safe_report_path(filename: str, subdir: Optional[str] = None) -> Path:
    """Get a safe, repo‑bounded path for a report filename.

    If `subdir` is provided, the file is placed under `docs/subdir` by default.
    """
    base = get_docs_output_dir("docs" if subdir is None else f"docs/{subdir}")
    return (base / filename).resolve()


def safe_write_text(filename: str, content: str, subdir: Optional[str] = None) -> Path:
    """Write text content to a safe report file path and return the path."""
    path = safe_report_path(filename, subdir=subdir)
    path.write_text(content, encoding="utf-8")
    return path

