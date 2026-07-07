"""Simplified PBH adapter for phase context retrieval."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from harness_lint.checker import Context

logger = logging.getLogger(__name__)

_CURRENT_VERSION = "0.1.0"

_VALID_PHASES = {"plan", "execute", "evaluate", "done"}

_HINTS = {
    "plan": "当前为规划阶段，建议先完善 AGENTS.md 规则定义",
    "execute": "当前为执行阶段，安全类规则已激活",
    "evaluate": "当前为评估阶段，建议严格执行风格检查",
    "done": "当前为完成阶段，所有检查项应已通过",
}


def _resolve_phase(data: dict) -> str | None:
    """Resolve the PBH phase from parsed progress.json data.

    Reads ``phase`` first; if absent, falls back to ``current_stage``.
    If both are missing or invalid, logs a warning and returns None
    (default / most-strict mode).

    Args:
        data: Parsed progress.json content.

    Returns:
        A valid phase ("plan", "execute", "evaluate", "done") or None.
    """
    phase = data.get("phase")
    if phase is None:
        phase = data.get("current_stage")
        if phase is not None:
            logger.warning(
                "phase 字段缺失，已回退至 current_stage='%s'（兼容提示：建议统一使用 phase 字段）",
                phase,
            )
    if phase not in _VALID_PHASES:
        if phase is None:
            logger.warning(
                "progress.json 缺少 phase 与 current_stage 字段，降级为默认检查模式"
            )
        else:
            logger.warning("阶段值 '%s' 无效，降级为默认检查模式", phase)
        return None
    return phase


def get_context(path: str = ".") -> Context:
    """Read .harness/progress.json and return phase-aware context.

    The phase is read from the ``phase`` field; if absent, falls back to
    ``current_stage``. If both are missing or invalid, logs a warning and
    degrades to default mode (phase=None).

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

    phase = _resolve_phase(data)

    harness_version = data.get("harness_version")

    hint = _HINTS.get(phase, "无 PBH 上下文，启用最严格检查模式")

    if harness_version and harness_version != _CURRENT_VERSION:
        hint += f" [警告：harness_version {harness_version} 与当前版本 {_CURRENT_VERSION} 不兼容]"

    return Context(
        phase=phase,
        harness_version=harness_version,
        hint=hint,
    )
