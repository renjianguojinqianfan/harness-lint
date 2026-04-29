"""Tests for the reporter output protocol module."""

from __future__ import annotations

import json

import pytest

from harness_lint.accumulator import PatternWarning
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

    def test_evaluate_phase_shows_hint_line(self) -> None:
        """phase='evaluate' should show the evaluate hint line after summary."""
        result = format_terminal([], files_checked=3, phase="evaluate")
        assert "💡 当前处于 Evaluate 阶段，建议优先完成所有规则固化。" in result

    def test_none_phase_omits_hint_line(self) -> None:
        """phase=None should not show the evaluate hint line."""
        result = format_terminal([], files_checked=3, phase=None)
        assert "Evaluate 阶段" not in result

    def test_execute_phase_omits_hint_line(self) -> None:
        """phase='execute' should not show the evaluate hint line."""
        result = format_terminal([], files_checked=3, phase="execute")
        assert "Evaluate 阶段" not in result


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

    def test_accepts_phase_parameter(self, sample_violations: list[Violation]) -> None:
        """format_json should accept phase parameter without error."""
        result = format_json(sample_violations, files_checked=5, phase="evaluate")
        parsed = json.loads(result)
        assert parsed["summary"]["errors"] == 1


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
                file="a.py",
                line=1,
                column=0,
                rule_id="HL001",
                severity="Error",
                phenomenon="e1",
                attribution="a1",
                agente_ref="r1",
            ),
            Violation(
                file="a.py",
                line=2,
                column=0,
                rule_id="HL002",
                severity="Error",
                phenomenon="e2",
                attribution="a2",
                agente_ref="r2",
            ),
            Violation(
                file="b.py",
                line=1,
                column=0,
                rule_id="HL003",
                severity="Warning",
                phenomenon="w1",
                attribution="a3",
                agente_ref="r3",
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

    def test_accepts_phase_parameter(self) -> None:
        """format_summary should accept phase parameter without error."""
        result = format_summary([], files_checked=1, phase="evaluate")
        assert result.startswith("harness-lint:")


class TestPatternWarningsTerminal:
    """Tests for pattern_warnings in terminal output."""

    def test_shows_pattern_warnings_block(self, sample_violations: list[Violation]) -> None:
        """Terminal output should include pattern_warnings section."""
        pws = [
            PatternWarning(
                rule_id="HL202",
                count=8,
                suggestion="建议在 AGENTS.md §5 中明确异常处理规范",
                description="假异常处理",
            ),
        ]
        result = format_terminal(sample_violations, files_checked=5, pattern_warnings=pws)
        assert "模式性偏差" in result
        assert "HL202" in result
        assert "8 次" in result
        assert "假异常处理" in result
        assert "建议在 AGENTS.md §5 中明确异常处理规范" in result

    def test_no_pattern_warnings_omits_block(self, sample_violations: list[Violation]) -> None:
        """When pattern_warnings is None, no block should appear."""
        result = format_terminal(sample_violations, files_checked=5, pattern_warnings=None)
        assert "模式性偏差" not in result

    def test_empty_pattern_warnings_omits_block(self, sample_violations: list[Violation]) -> None:
        """When pattern_warnings is empty, no block should appear."""
        result = format_terminal(sample_violations, files_checked=5, pattern_warnings=[])
        assert "模式性偏差" not in result


class TestPatternWarningsJson:
    """Tests for pattern_warnings in JSON output."""

    def test_populates_pattern_warnings_array(self, sample_violations: list[Violation]) -> None:
        """JSON should populate pattern_warnings with actual data."""
        pws = [
            PatternWarning(
                rule_id="HL201",
                count=8,
                suggestion="建议在 AGENTS.md §5 中明确异常处理规范",
                description="假异常处理",
            ),
        ]
        result = format_json(sample_violations, files_checked=5, pattern_warnings=pws)
        parsed = json.loads(result)
        assert len(parsed["pattern_warnings"]) == 1
        assert parsed["pattern_warnings"][0]["rule_id"] == "HL201"
        assert parsed["pattern_warnings"][0]["count"] == 8
        expected_suggestion = "建议在 AGENTS.md §5 中明确异常处理规范"
        assert parsed["pattern_warnings"][0]["suggestion"] == expected_suggestion
        assert parsed["pattern_warnings"][0]["description"] == "假异常处理"

    def test_no_pattern_warnings_defaults_to_empty(
        self, sample_violations: list[Violation]
    ) -> None:
        """When pattern_warnings is None, JSON should have empty array."""
        result = format_json(sample_violations, files_checked=5, pattern_warnings=None)
        parsed = json.loads(result)
        assert parsed["pattern_warnings"] == []


class TestPatternWarningsSummary:
    """Tests for pattern_warnings in summary output."""

    def test_appends_pattern_warnings_to_summary(self, sample_violations: list[Violation]) -> None:
        """Summary should append pattern warning info when provided."""
        pws = [
            PatternWarning(
                rule_id="HL202",
                count=8,
                suggestion="建议在 AGENTS.md §5 中明确异常处理规范",
                description="假异常处理",
            ),
        ]
        result = format_summary(sample_violations, files_checked=5, pattern_warnings=pws)
        assert "HL202" in result
        assert "8 次" in result
        assert "假异常处理" in result
        assert "\n" in result  # newline separated, not pipe
        assert " | " not in result

    def test_no_pattern_warnings_no_extra_text(self, sample_violations: list[Violation]) -> None:
        """When pattern_warnings is None, summary should not mention them."""
        result = format_summary(sample_violations, files_checked=5, pattern_warnings=None)
        assert "HL202" not in result
        assert "次" not in result

    def test_empty_pattern_warnings_no_extra_text(self, sample_violations: list[Violation]) -> None:
        """When pattern_warnings is empty, summary should not mention them."""
        result = format_summary(sample_violations, files_checked=5, pattern_warnings=[])
        assert "HL202" not in result
        assert "次" not in result

    def test_multiple_pattern_warnings_newline_separated(
        self, sample_violations: list[Violation]
    ) -> None:
        """Multiple pattern warnings should be separated by newlines."""
        pws = [
            PatternWarning(
                rule_id="HL201",
                count=3,
                suggestion="s1",
                description="函数过长",
            ),
            PatternWarning(
                rule_id="HL202",
                count=8,
                suggestion="s2",
                description="假异常处理",
            ),
        ]
        result = format_summary(sample_violations, files_checked=5, pattern_warnings=pws)
        lines = result.split("\n")
        # First line is the harness-lint summary
        assert lines[0].startswith("harness-lint:")
        # Pattern warnings on separate lines
        assert any("HL201" in line for line in lines)
        assert any("HL202" in line for line in lines)
        assert " | " not in result
