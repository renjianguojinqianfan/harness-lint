"""Simplified PBH adapter for phase context retrieval."""

from __future__ import annotations

import json
from pathlib import Path

from harness_lint.checker import Context

_CURRENT_VERSION = "0.1.0"

_VALID_PHASES = {"plan", "execute", "evaluate", "done"}

_HINTS = {
    "plan": "当前为规划阶段，建议先完善 AGENTS.md 规则定义",
    "execute": "当前为执行阶段，安全类规则已激活",
    "evaluate": "当前为评估阶段，建议严格执行风格检查",
    "done": "当前为完成阶段，所有检查项应已通过",
}


def get_context(path: str = ".") -> Context:
    """Read .harness/progress.json and return phase-aware context.

    Args:
        path: Project root to look for .harness/progress.json.

    Returns:
        Context with phase, harness_version, and hint fields populated.
    """
    progress_file = Path(path) / ".harness" / "progress.json"
    if not progress_file.exists():
        return Context(
            phase=None,
            harness_version=None,
            hint="无 PBH 上下文，启用最严格检查模式",
        )

    try:
        data = json.loads(progress_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return Context(
            phase=None,
            harness_version=None,
            hint="无 PBH 上下文，启用最严格检查模式",
        )

    phase = data.get("phase")
    if phase not in _VALID_PHASES:
        phase = None

    harness_version = data.get("harness_version")

    hint = _HINTS.get(phase, "无 PBH 上下文，启用最严格检查模式")

    if harness_version and harness_version != _CURRENT_VERSION:
        hint += f" [警告：harness_version {harness_version} 与当前版本 {_CURRENT_VERSION} 不兼容]"

    return Context(
        phase=phase,
        harness_version=harness_version,
        hint=hint,
    )
