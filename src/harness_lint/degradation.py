"""Degradation cost visibility for Harness-Lint.

When Harness-Lint is disabled or uninstalled, running make verify
outputs a degradation notice showing what is no longer being checked.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from harness_lint.rules.base import Rule, Violation

_STATE_FILE = Path(".harness/harness-lint-state.json")
_ENABLED_FLAG = Path(".harness/harness-lint-enabled")


def record_run_state(rules: list[Rule], violations: list[Violation]) -> None:
    """Persist the current run state for degradation detection.

    Writes rule IDs, names, agente_refs, and violation counts to
    the state file.

    Args:
        rules: List of active rules.
        violations: List of violations found in the current run.
    """
    state = {
        "rules": [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "agente_ref": r.agente_ref,
            }
            for r in rules
        ],
        "violation_count": len(violations),
        "agente_refs": sorted({r.agente_ref for r in rules}),
    }
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def is_harness_lint_enabled() -> bool:
    """Check whether Harness-Lint is currently enabled.

    Returns:
        True if the enabled flag file exists.
    """
    return _ENABLED_FLAG.exists()


def format_degradation_notice() -> str | None:
    """Format a degradation notice if Harness-Lint is disabled.

    Reads the last recorded state and outputs:
    - '当前未启用 Harness-Lint'
    - Total rules that were active
    - Last reported violation count
    - List of AGENTS.md clauses no longer being verified

    Returns:
        A formatted multi-line notice, or None if Harness-Lint is
        enabled or no state file exists.
    """
    if is_harness_lint_enabled():
        return None

    if not _STATE_FILE.exists():
        return None

    try:
        data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    rule_count = len(data.get("rules", []))
    violation_count = data.get("violation_count", 0)
    agente_refs = sorted(set(data.get("agente_refs", [])))

    lines = [
        "当前未启用 Harness-Lint",
        f"启用期间规则总数: {rule_count}",
        f"最近一次报告违规数量: {violation_count}",
    ]

    if agente_refs:
        lines.append("当前因停用而不再被验证的 AGENTS.md 条款:")
        for ref in agente_refs:
            lines.append(f"  - {ref}")

    return "\n".join(lines)
