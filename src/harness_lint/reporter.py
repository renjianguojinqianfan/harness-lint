"""Reporter output protocol for Harness-Lint.

Provides formatters that emit violations in three output styles:
terminal (human-readable with ANSI colors), JSON (machine-readable),
and summary (compact one-liner). Every output includes the full
attribution chain required by the Harness-Lint protocol:
phenomenon (what), attribution (why), and agente_ref (where).
"""

from __future__ import annotations

import json
from collections import defaultdict

from harness_lint.rules.base import Violation

# ANSI color escape codes
_RED = "\x1b[31m"
_YELLOW = "\x1b[33m"
_BLUE = "\x1b[34m"
_RESET = "\x1b[0m"

_SEVERITY_ICON = {
    "Error": "❌",
    "Warning": "⚠️",
    "Info": "ℹ️",
}

_SEVERITY_COLOR = {
    "Error": _RED,
    "Warning": _YELLOW,
    "Info": _BLUE,
}


def _count_severities(violations: list[Violation]) -> dict[str, int]:
    """Return a mapping of severity -> count."""
    counts: dict[str, int] = {"Error": 0, "Warning": 0, "Info": 0}
    for v in violations:
        if v.severity in counts:
            counts[v.severity] += 1
    return counts


def format_terminal(violations: list[Violation], files_checked: int) -> str:
    """Format violations as a human-readable terminal string.

    Violations are grouped by file path. Each violation shows its
    position, severity icon, rule ID, phenomenon, attribution, and
    AGENTS.md reference. A summary block is appended at the end.

    Args:
        violations: List of violations to format.
        files_checked: Total number of files that were examined.

    Returns:
        Multi-line string suitable for terminal output.
    """
    if not violations:
        return (
            f"\x1b[32m✅ 无违规发现{_RESET}\n"
            f"  检查文件数: {files_checked}"
        )

    # Group violations by file
    by_file: dict[str, list[Violation]] = defaultdict(list)
    for v in violations:
        by_file[v.file].append(v)

    lines: list[str] = []
    for file_path in sorted(by_file):
        lines.append(f"📄 {file_path}")
        for v in by_file[file_path]:
            color = _SEVERITY_COLOR.get(v.severity, _RESET)
            icon = _SEVERITY_ICON.get(v.severity, "•")
            lines.append(
                f"  {v.line}:{v.column}   {color}{icon}{_RESET}  "
                f"{v.rule_id} {v.phenomenon}"
            )
            lines.append(f"         ↳ 原因：{v.attribution}")
            lines.append(f"         ↳ 归属：{v.agente_ref}")
        lines.append("")

    counts = _count_severities(violations)
    files_with_violations = len(by_file)

    lines.append("📊 检查汇总")
    lines.append(f"  ❌ Error:   {counts['Error']}")
    lines.append(f"  ⚠️  Warning: {counts['Warning']}")
    lines.append(f"  ℹ️  Info:    {counts['Info']}")
    lines.append(f"  检查文件数: {files_checked}")
    lines.append(f"  违规文件数: {files_with_violations}")

    return "\n".join(lines)


def format_json(violations: list[Violation], files_checked: int) -> str:
    """Format violations as a JSON string.

    The JSON structure contains a summary object, a violations array
    (each item carrying the full attribution chain), and an empty
    pattern_warnings array for forward compatibility.

    Args:
        violations: List of violations to format.
        files_checked: Total number of files that were examined.

    Returns:
        Pretty-printed JSON string.
    """
    counts = _count_severities(violations)

    # Count unique files with violations
    files_with_violations = len({v.file for v in violations})

    violation_dicts = [
        {
            "file": v.file,
            "line": v.line,
            "column": v.column,
            "rule_id": v.rule_id,
            "severity": v.severity,
            "phenomenon": v.phenomenon,
            "attribution": v.attribution,
            "agente_ref": v.agente_ref,
        }
        for v in violations
    ]

    output = {
        "summary": {
            "errors": counts["Error"],
            "warnings": counts["Warning"],
            "info": counts["Info"],
            "files_checked": files_checked,
            "files_with_violations": files_with_violations,
        },
        "violations": violation_dicts,
        "pattern_warnings": [],
    }

    return json.dumps(output, ensure_ascii=False, indent=2)


def format_summary(violations: list[Violation], files_checked: int) -> str:
    """Format a compact one-line summary string.

    Args:
        violations: List of violations to summarise.
        files_checked: Total number of files that were examined.

    Returns:
        Single-line summary like ``harness-lint: 1 error, 1 warning, ...``.
    """
    counts = _count_severities(violations)
    return (
        f"harness-lint: {counts['Error']} error, "
        f"{counts['Warning']} warning, {counts['Info']} info "
        f"(checked {files_checked} files)"
    )
