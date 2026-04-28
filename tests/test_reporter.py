"""Tests for the reporter output protocol module."""

from __future__ import annotations

import json

import pytest

from harness_lint.reporter import (
    format_json,
    format_summary,
    format_terminal,
)
from harness_lint.rules.base import Violation


@pytest.fixture
def sample_violations() -> list[Violation]:
    """Return a list of sample violations with mixed severity."""
    return [
        Violation(
            file="src/myproject/core.py",
            line=12,
            column=5,
            rule_id="HL003",
            severity="Error",
            phenomenon="禁止使用 os.system()",
            attribution="使用了不安全的系统调用",
            agente_ref="AGENTS.md §5 Critical Rules",
        ),
        Violation(
            file="src/myproject/core.py",
            line=45,
            column=1,
            rule_id="HL201",
            severity="Warning",
            phenomenon="函数 process_data 长度 67 行（阈值 50 行）",
            attribution="AGENTS.md 未定义函数长度上限",
            agente_ref="AGENTS.md §4 Working Guidelines",
        ),
        Violation(
            file="src/myproject/utils.py",
            line=3,
            column=0,
            rule_id="HL301",
            severity="Info",
            phenomenon="缺少模块文档字符串",
            attribution="AGENTS.md 要求所有公共模块有文档字符串",
            agente_ref="AGENTS.md §4 Working Guidelines",
        ),
    ]


class TestFormatTerminal:
    """Tests for terminal output formatter."""

    def test_contains_all_three_elements(self, sample_violations: list[Violation]) -> None:
        """Each violation must show phenomenon, attribution, and agente_ref."""
        result = format_terminal(sample_violations, files_checked=5)
        assert "禁止使用 os.system()" in result
        assert "使用了不安全的系统调用" in result
        assert "AGENTS.md §5 Critical Rules" in result
        assert "函数 process_data 长度 67 行" in result
        assert "AGENTS.md 未定义函数长度上限" in result
        assert "AGENTS.md §4 Working Guidelines" in result

    def test_groups_violations_by_file(self, sample_violations: list[Violation]) -> None:
        """Violations for the same file should be grouped together."""
        result = format_terminal(sample_violations, files_checked=5)
        core_idx = result.find("src/myproject/core.py")
        utils_idx = result.find("src/myproject/utils.py")
        # Both files should appear
        assert core_idx != -1
        assert utils_idx != -1
        # core.py should appear before utils.py
        assert core_idx < utils_idx

    def test_shows_position_as_line_col(self, sample_violations: list[Violation]) -> None:
        """Violation positions should use line:column format."""
        result = format_terminal(sample_violations, files_checked=5)
        assert "12:5" in result
        assert "45:1" in result
        assert "3:0" in result

    def test_includes_ansi_color_codes(self, sample_violations: list[Violation]) -> None:
        """Terminal output should include ANSI color escape codes."""
        result = format_terminal(sample_violations, files_checked=5)
        # Check for ANSI escape sequences (\x1b[ or \033[)
        assert "\x1b[" in result

    def test_includes_summary_stats(self, sample_violations: list[Violation]) -> None:
        """Terminal output should include summary statistics."""
        result = format_terminal(sample_violations, files_checked=5)
        assert "Error" in result or "错误" in result or "❌" in result
        assert "Warning" in result or "警告" in result or "⚠️" in result
        assert "5" in result  # files_checked

    def test_empty_violations_shows_no_violations_message(self) -> None:
        """Empty violations list should show a friendly no-violations message."""
        result = format_terminal([], files_checked=3)
        assert "无违规" in result or "No violations" in result or "通过" in result


class TestFormatJson:
    """Tests for JSON output formatter."""

    def test_is_valid_json(self, sample_violations: list[Violation]) -> None:
        """Output must be valid JSON."""
        result = format_json(sample_violations, files_checked=5)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_contains_summary(self, sample_violations: list[Violation]) -> None:
        """JSON must contain a summary object with correct counts."""
        result = format_json(sample_violations, files_checked=5)
        parsed = json.loads(result)
        assert "summary" in parsed
        summary = parsed["summary"]
        assert summary["errors"] == 1
        assert summary["warnings"] == 1
        assert summary["info"] == 1
        assert summary["files_checked"] == 5
        assert summary["files_with_violations"] == 2

    def test_contains_violations_array(self, sample_violations: list[Violation]) -> None:
        """JSON must contain a violations array with all entries."""
        result = format_json(sample_violations, files_checked=5)
        parsed = json.loads(result)
        assert "violations" in parsed
        assert len(parsed["violations"]) == 3

    def test_violation_has_all_three_elements(self, sample_violations: list[Violation]) -> None:
        """Each violation in JSON must have phenomenon, attribution, agente_ref."""
        result = format_json(sample_violations, files_checked=5)
        parsed = json.loads(result)
        v = parsed["violations"][0]
        assert "phenomenon" in v
        assert "attribution" in v
        assert "agente_ref" in v
        assert v["phenomenon"] == "禁止使用 os.system()"
        assert v["attribution"] == "使用了不安全的系统调用"
        assert v["agente_ref"] == "AGENTS.md §5 Critical Rules"

    def test_violation_has_required_fields(self, sample_violations: list[Violation]) -> None:
        """Each violation must have file, line, column, rule_id, severity."""
        result = format_json(sample_violations, files_checked=5)
        parsed = json.loads(result)
        v = parsed["violations"][0]
        assert v["file"] == "src/myproject/core.py"
        assert v["line"] == 12
        assert v["column"] == 5
        assert v["rule_id"] == "HL003"
        assert v["severity"] == "Error"

    def test_empty_violations_has_empty_array(self) -> None:
        """Empty violations should produce empty array and zero counts."""
        result = format_json([], files_checked=3)
        parsed = json.loads(result)
        assert parsed["violations"] == []
        assert parsed["summary"]["errors"] == 0
        assert parsed["summary"]["warnings"] == 0
        assert parsed["summary"]["info"] == 0
        assert parsed["summary"]["files_with_violations"] == 0

    def test_includes_pattern_warnings(self, sample_violations: list[Violation]) -> None:
        """JSON output should include pattern_warnings key."""
        result = format_json(sample_violations, files_checked=5)
        parsed = json.loads(result)
        assert "pattern_warnings" in parsed
        assert isinstance(parsed["pattern_warnings"], list)


class TestFormatSummary:
    """Tests for summary output formatter."""

    def test_shows_error_warning_info_counts(self, sample_violations: list[Violation]) -> None:
        """Summary should show counts for each severity level."""
        result = format_summary(sample_violations, files_checked=5)
        assert "1 error" in result
        assert "1 warning" in result
        assert "1 info" in result
        assert "5 files" in result or "checked 5" in result

    def test_shows_only_errors(self) -> None:
        """Summary with only errors should format correctly."""
        violations = [
            Violation(
                file="a.py",
                line=1,
                column=0,
                rule_id="HL001",
                severity="Error",
                phenomenon="x",
                attribution="y",
                agente_ref="z",
            ),
        ]
        result = format_summary(violations, files_checked=2)
        assert "1 error" in result
        assert "0 warning" in result
        assert "0 info" in result

    def test_empty_violations_shows_zero_counts(self) -> None:
        """Summary with no violations should show all zeros."""
        result = format_summary([], files_checked=3)
        assert "0 error" in result
        assert "0 warning" in result
        assert "0 info" in result
        assert "3 files" in result or "checked 3" in result

    def test_multiple_severities(self) -> None:
        """Summary should correctly count multiple violations per severity."""
        violations = [
            Violation(
                file="a.py", line=1, column=0, rule_id="HL001",
                severity="Error", phenomenon="e1", attribution="a1", agente_ref="r1",
            ),
            Violation(
                file="a.py", line=2, column=0, rule_id="HL002",
                severity="Error", phenomenon="e2", attribution="a2", agente_ref="r2",
            ),
            Violation(
                file="b.py", line=1, column=0, rule_id="HL003",
                severity="Warning", phenomenon="w1", attribution="a3", agente_ref="r3",
            ),
        ]
        result = format_summary(violations, files_checked=4)
        assert "2 error" in result
        assert "1 warning" in result
        assert "0 info" in result

    def test_starts_with_harness_lint(self) -> None:
        """Summary should start with 'harness-lint:'."""
        result = format_summary([], files_checked=1)
        assert result.startswith("harness-lint:")
