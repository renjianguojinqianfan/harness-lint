"""Simplified PBH adapter for phase context retrieval."""

from __future__ import annotations

import json
from pathlib import Path

from harness_lint.checker import Context


def get_context(path: str = ".") -> Context:
    """Read .harness/progress.json and return phase-aware context.

    Args:
        path: Project root to look for .harness/progress.json.

    Returns:
        Context with phase field set ("execute", "evaluate", or None).
    """
    progress_file = Path(path) / ".harness" / "progress.json"
    if not progress_file.exists():
        return Context(phase=None)

    try:
        data = json.loads(progress_file.read_text(encoding="utf-8"))
        phase = data.get("phase")
        if phase in ("execute", "evaluate"):
            return Context(phase=phase)
    except (OSError, json.JSONDecodeError):
        pass

    return Context(phase=None)
