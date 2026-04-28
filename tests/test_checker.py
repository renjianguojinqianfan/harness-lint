"""Tests for the checker engine module."""

from __future__ import annotations

import ast
from dataclasses import dataclass

from harness_lint.checker import Context, check, collect_files
from harness_lint.rules.base import Rule, Violation


@dataclass
class FakeRule(Rule):
    """A fake rule for testing that returns predefined violations."""

    violations_to_return: list[Violation] | None = None

    def check(
        self, file_path: str, file_content: str, ast_tree: ast.AST
    ) -> list[Violation] | None:
        """Return predefined violations."""
        return self.violations_to_return


class TestCollectFiles:
    """Tests for collect_files function."""

    def test_collects_py_files_recursively(self) -> None:
        """Should recursively collect all .py files."""
        files = collect_files("tests/fixtures/valid_package")
        basenames = sorted([f.replace("\\", "/").split("/")[-1] for f in files])
        assert basenames == ["__init__.py", "module.py"]

    def test_ignores_git_directory(self) -> None:
        """Should ignore .git/ directory by default."""
        files = collect_files("tests/fixtures/with_git")
        basenames = [f.replace("\\", "/").split("/")[-1] for f in files]
        assert ".git" not in list(basenames)
        assert "config" not in basenames
        assert "real.py" in basenames

    def test_ignores_pycache_directory(self, tmp_path) -> None:
        """Should ignore __pycache__/ directory by default."""
        (tmp_path / "a.py").write_text("pass")
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "b.cpython-311.pyc").write_text("")
        files = collect_files(str(tmp_path))
        basenames = [f.replace("\\", "/").split("/")[-1] for f in files]
        assert basenames == ["a.py"]

    def test_ignores_venv_directory(self, tmp_path) -> None:
        """Should ignore .venv/ directory by default."""
        (tmp_path / "a.py").write_text("pass")
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "b.py").write_text("pass")
        files = collect_files(str(tmp_path))
        basenames = [f.replace("\\", "/").split("/")[-1] for f in files]
        assert basenames == ["a.py"]

    def test_ignores_mypy_cache_directory(self, tmp_path) -> None:
        """Should ignore .mypy_cache/ directory by default."""
        (tmp_path / "a.py").write_text("pass")
        cache = tmp_path / ".mypy_cache"
        cache.mkdir()
        (cache / "b.py").write_text("pass")
        files = collect_files(str(tmp_path))
        basenames = [f.replace("\\", "/").split("/")[-1] for f in files]
        assert basenames == ["a.py"]

    def test_ignores_pytest_cache_directory(self, tmp_path) -> None:
        """Should ignore .pytest_cache/ directory by default."""
        (tmp_path / "a.py").write_text("pass")
        cache = tmp_path / ".pytest_cache"
        cache.mkdir()
        (cache / "b.py").write_text("pass")
        files = collect_files(str(tmp_path))
        basenames = [f.replace("\\", "/").split("/")[-1] for f in files]
        assert basenames == ["a.py"]

    def test_returns_empty_list_for_empty_directory(self, tmp_path) -> None:
        """Should return empty list when no Python files exist."""
        files = collect_files(str(tmp_path))
        assert files == []

    def test_returns_sorted_list_for_stable_output(self, tmp_path) -> None:
        """Should return sorted list of file paths."""
        (tmp_path / "z.py").write_text("pass")
        (tmp_path / "a.py").write_text("pass")
        (tmp_path / "m.py").write_text("pass")
        files = collect_files(str(tmp_path))
        basenames = [f.replace("\\", "/").split("/")[-1] for f in files]
        assert basenames == ["a.py", "m.py", "z.py"]


class TestPhaseFiltering:
    """Tests for rule activation based on phase."""

    def test_execute_phase_only_activates_execute_rules(self, tmp_path) -> None:
        """Execute phase should only activate rules with 'execute' in phases."""
        (tmp_path / "a.py").write_text("x = 1\n")
        execute_rule = FakeRule(
            rule_id="HL001",
            name="execute-only",
            severity="Error",
            message_template="msg",
            phases=["execute"],
            agente_ref="AGENTS.md §1",
            attribution="attr",
            violations_to_return=[
                Violation(
                    file="a.py",
                    line=1,
                    column=0,
                    rule_id="HL001",
                    severity="Error",
                    phenomenon="phen",
                    attribution="attr",
                    agente_ref="ref",
                )
            ],
        )
        evaluate_rule = FakeRule(
            rule_id="HL301",
            name="evaluate-only",
            severity="Info",
            message_template="msg",
            phases=["evaluate"],
            agente_ref="AGENTS.md §2",
            attribution="attr",
            violations_to_return=[
                Violation(
                    file="a.py",
                    line=1,
                    column=0,
                    rule_id="HL301",
                    severity="Info",
                    phenomenon="phen",
                    attribution="attr",
                    agente_ref="ref",
                )
            ],
        )
        context = Context(phase="execute")
        result, _ = check(str(tmp_path), context, [execute_rule, evaluate_rule])
        assert len(result) == 1
        assert result[0].rule_id == "HL001"

    def test_evaluate_phase_activates_evaluate_rules(self, tmp_path) -> None:
        """Evaluate phase should activate rules with 'evaluate' in phases."""
        (tmp_path / "a.py").write_text("x = 1\n")
        execute_rule = FakeRule(
            rule_id="HL001",
            name="execute-only",
            severity="Error",
            message_template="msg",
            phases=["execute"],
            agente_ref="AGENTS.md §1",
            attribution="attr",
            violations_to_return=[
                Violation(
                    file="a.py",
                    line=1,
                    column=0,
                    rule_id="HL001",
                    severity="Error",
                    phenomenon="phen",
                    attribution="attr",
                    agente_ref="ref",
                )
            ],
        )
        evaluate_rule = FakeRule(
            rule_id="HL301",
            name="evaluate-only",
            severity="Info",
            message_template="msg",
            phases=["evaluate"],
            agente_ref="AGENTS.md §2",
            attribution="attr",
            violations_to_return=[
                Violation(
                    file="a.py",
                    line=1,
                    column=0,
                    rule_id="HL301",
                    severity="Info",
                    phenomenon="phen",
                    attribution="attr",
                    agente_ref="ref",
                )
            ],
        )
        context = Context(phase="evaluate")
        result, _ = check(str(tmp_path), context, [execute_rule, evaluate_rule])
        assert len(result) == 1
        assert result[0].rule_id == "HL301"

    def test_none_phase_activates_all_rules(self, tmp_path) -> None:
        """None phase should activate all rules."""
        (tmp_path / "a.py").write_text("x = 1\n")
        execute_rule = FakeRule(
            rule_id="HL001",
            name="execute-only",
            severity="Error",
            message_template="msg",
            phases=["execute"],
            agente_ref="AGENTS.md §1",
            attribution="attr",
            violations_to_return=[
                Violation(
                    file="a.py",
                    line=1,
                    column=0,
                    rule_id="HL001",
                    severity="Error",
                    phenomenon="phen",
                    attribution="attr",
                    agente_ref="ref",
                )
            ],
        )
        evaluate_rule = FakeRule(
            rule_id="HL301",
            name="evaluate-only",
            severity="Info",
            message_template="msg",
            phases=["evaluate"],
            agente_ref="AGENTS.md §2",
            attribution="attr",
            violations_to_return=[
                Violation(
                    file="a.py",
                    line=1,
                    column=0,
                    rule_id="HL301",
                    severity="Info",
                    phenomenon="phen",
                    attribution="attr",
                    agente_ref="ref",
                )
            ],
        )
        context = Context(phase=None)
        result, _ = check(str(tmp_path), context, [execute_rule, evaluate_rule])
        assert len(result) == 2
        rule_ids = {v.rule_id for v in result}
        assert rule_ids == {"HL001", "HL301"}

    def test_both_phases_rule_activated_in_execute(self, tmp_path) -> None:
        """Rules with both phases should be active in execute phase."""
        (tmp_path / "a.py").write_text("x = 1\n")
        both_rule = FakeRule(
            rule_id="HL201",
            name="both",
            severity="Warning",
            message_template="msg",
            phases=["execute", "evaluate"],
            agente_ref="AGENTS.md §3",
            attribution="attr",
            violations_to_return=[
                Violation(
                    file="a.py",
                    line=1,
                    column=0,
                    rule_id="HL201",
                    severity="Warning",
                    phenomenon="phen",
                    attribution="attr",
                    agente_ref="ref",
                )
            ],
        )
        context = Context(phase="execute")
        result, _ = check(str(tmp_path), context, [both_rule])
        assert len(result) == 1
        assert result[0].rule_id == "HL201"

    def test_both_phases_rule_activated_in_evaluate(self, tmp_path) -> None:
        """Rules with both phases should be active in evaluate phase."""
        (tmp_path / "a.py").write_text("x = 1\n")
        both_rule = FakeRule(
            rule_id="HL201",
            name="both",
            severity="Warning",
            message_template="msg",
            phases=["execute", "evaluate"],
            agente_ref="AGENTS.md §3",
            attribution="attr",
            violations_to_return=[
                Violation(
                    file="a.py",
                    line=1,
                    column=0,
                    rule_id="HL201",
                    severity="Warning",
                    phenomenon="phen",
                    attribution="attr",
                    agente_ref="ref",
                )
            ],
        )
        context = Context(phase="evaluate")
        result, _ = check(str(tmp_path), context, [both_rule])
        assert len(result) == 1
        assert result[0].rule_id == "HL201"


class TestCheckFunction:
    """Tests for check function behavior."""

    def test_calls_rule_check_with_correct_args(self, tmp_path) -> None:
        """Should call rule.check with file_path, content, and ast_tree."""
        (tmp_path / "a.py").write_text("x = 1\n")

        class RecordingRule(FakeRule):
            """Records the arguments passed to check."""

            def __init__(self, **kwargs) -> None:
                super().__init__(**kwargs)
                self.calls: list[tuple] = []

            def check(
                self, file_path: str, file_content: str, ast_tree: ast.AST
            ) -> list[Violation] | None:
                self.calls.append((file_path, file_content, ast_tree))
                return None

        rule = RecordingRule(
            rule_id="HL001",
            name="recorder",
            severity="Error",
            message_template="msg",
            agente_ref="AGENTS.md §1",
            attribution="attr",
        )
        context = Context(phase=None)
        check(str(tmp_path), context, [rule])
        assert len(rule.calls) == 1
        path, content, tree = rule.calls[0]
        assert path.endswith("a.py")
        assert content == "x = 1\n"
        assert isinstance(tree, ast.AST)

    def test_returns_violations_sorted_by_file(self, tmp_path) -> None:
        """Should return violations sorted by file path."""
        (tmp_path / "b.py").write_text("y = 2\n")
        (tmp_path / "a.py").write_text("x = 1\n")

        class FileNamingRule(FakeRule):
            """Returns violation with file_path as phenomenon for sorting check."""

            def check(
                self, file_path: str, file_content: str, ast_tree: ast.AST
            ) -> list[Violation] | None:
                return [
                    Violation(
                        file=file_path,
                        line=1,
                        column=0,
                        rule_id="HL001",
                        severity="Error",
                        phenomenon="found",
                        attribution="attr",
                        agente_ref="ref",
                    )
                ]

        naming_rule = FileNamingRule(
            rule_id="HL001",
            name="namer",
            severity="Error",
            message_template="msg",
            agente_ref="AGENTS.md §1",
            attribution="attr",
        )
        context = Context(phase=None)
        result, _ = check(str(tmp_path), context, [naming_rule])
        assert len(result) == 2
        files = [v.file for v in result]
        assert files == sorted(files)

    def test_aggregates_violations_from_multiple_rules(self, tmp_path) -> None:
        """Should collect violations from all activated rules."""
        (tmp_path / "a.py").write_text("x = 1\n")
        rule1 = FakeRule(
            rule_id="HL001",
            name="r1",
            severity="Error",
            message_template="msg",
            agente_ref="AGENTS.md §1",
            attribution="a1",
            violations_to_return=[
                Violation(
                    file="a.py",
                    line=1,
                    column=0,
                    rule_id="HL001",
                    severity="Error",
                    phenomenon="p1",
                    attribution="a1",
                    agente_ref="ref1",
                )
            ],
        )
        rule2 = FakeRule(
            rule_id="HL002",
            name="r2",
            severity="Error",
            message_template="msg",
            agente_ref="AGENTS.md §2",
            attribution="a2",
            violations_to_return=[
                Violation(
                    file="a.py",
                    line=2,
                    column=0,
                    rule_id="HL002",
                    severity="Error",
                    phenomenon="p2",
                    attribution="a2",
                    agente_ref="ref2",
                )
            ],
        )
        context = Context(phase=None)
        result, _ = check(str(tmp_path), context, [rule1, rule2])
        assert len(result) == 2
        rule_ids = {v.rule_id for v in result}
        assert rule_ids == {"HL001", "HL002"}

    def test_handles_none_return_from_rule(self, tmp_path) -> None:
        """Should handle rule.check returning None."""
        (tmp_path / "a.py").write_text("x = 1\n")
        rule = FakeRule(
            rule_id="HL001",
            name="none-returner",
            severity="Error",
            message_template="msg",
            agente_ref="AGENTS.md §1",
            attribution="attr",
            violations_to_return=None,
        )
        context = Context(phase=None)
        result, _ = check(str(tmp_path), context, [rule])
        assert result == []

    def test_handles_empty_violations_list(self, tmp_path) -> None:
        """Should handle rule.check returning empty list."""
        (tmp_path / "a.py").write_text("x = 1\n")
        rule = FakeRule(
            rule_id="HL001",
            name="empty-returner",
            severity="Error",
            message_template="msg",
            agente_ref="AGENTS.md §1",
            attribution="attr",
            violations_to_return=[],
        )
        context = Context(phase=None)
        result, _ = check(str(tmp_path), context, [rule])
        assert result == []

    def test_skips_files_with_invalid_syntax(self, tmp_path) -> None:
        """Should skip files with invalid Python syntax without crashing."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def broken(\n")
        good_file = tmp_path / "good.py"
        good_file.write_text("x = 1\n")

        class CountingRule(FakeRule):
            """Counts how many times check is called."""

            def __init__(self, **kwargs) -> None:
                super().__init__(**kwargs)
                self.call_count = 0

            def check(
                self, file_path: str, file_content: str, ast_tree: ast.AST
            ) -> list[Violation] | None:
                self.call_count += 1
                return None

        counter = CountingRule(
            rule_id="HL002",
            name="counter",
            severity="Error",
            message_template="msg",
            agente_ref="AGENTS.md §1",
            attribution="attr",
        )
        context = Context(phase=None)
        result, _ = check(str(tmp_path), context, [counter])
        assert counter.call_count == 1  # Only good.py
        assert result == []

    def test_no_rules_returns_empty_list(self, tmp_path) -> None:
        """Should return empty list when no rules provided."""
        (tmp_path / "a.py").write_text("x = 1\n")
        context = Context(phase=None)
        result, _ = check(str(tmp_path), context, [])
        assert result == []

    def test_no_py_files_returns_empty_list(self, tmp_path) -> None:
        """Should return empty list when no Python files found."""
        (tmp_path / "readme.txt").write_text("hello")
        context = Context(phase=None)
        result, _ = check(str(tmp_path), context, [])
        assert result == []

    def test_returns_pattern_warnings_for_repeated_violations(self, tmp_path) -> None:
        """Should return pattern warnings when a rule exceeds threshold."""
        (tmp_path / "a.py").write_text("x = 1\n")
        rule = FakeRule(
            rule_id="HL201",
            name="repeat",
            severity="Warning",
            message_template="msg",
            agente_ref="AGENTS.md §1",
            attribution="attr",
            violations_to_return=[
                Violation(
                    file=str(tmp_path / "a.py"),
                    line=1,
                    column=0,
                    rule_id="HL201",
                    severity="Warning",
                    phenomenon="phen",
                    attribution="attr",
                    agente_ref="AGENTS.md §1",
                )
                for _ in range(4)
            ],
        )
        context = Context(phase=None)
        violations, pattern_warnings = check(str(tmp_path), context, [rule])
        assert len(violations) == 4
        assert len(pattern_warnings) == 1
        assert pattern_warnings[0].rule_id == "HL201"
        assert pattern_warnings[0].count == 4
        assert "建议在 AGENTS.md §1 中明确相关规范" in pattern_warnings[0].suggestion
