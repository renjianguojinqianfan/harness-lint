"""Tests for CLI entry point."""

import json

from typer.testing import CliRunner

from harness_lint.cli import app

runner = CliRunner()


# --- Normal execution tests ---


def test_runs_in_non_pbh_directory_without_silent_exit(monkeypatch, tmp_path) -> None:
    """Non-PBH directory (no .harness/) must run checks, not silently exit."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "test.py").write_text("eval('1+1')", encoding="utf-8")
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 1
    assert "当前未启用 Harness-Lint" not in result.output
    assert "HL001" in result.output


def test_default_path_and_format(monkeypatch, tmp_path) -> None:
    """Default path is '.' and default format is terminal."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    assert "✅" in result.output or "无违规发现" in result.output


def test_format_json(monkeypatch, tmp_path) -> None:
    """--format json outputs valid JSON."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "summary" in data
    assert "violations" in data


def test_format_summary(monkeypatch, tmp_path) -> None:
    """--format summary outputs summary format."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "--format", "summary"])
    assert result.exit_code == 0
    assert result.output.startswith("harness-lint:")


def test_strict_warning_exits_nonzero(monkeypatch, tmp_path) -> None:
    """--strict with warnings returns non-zero exit code."""
    monkeypatch.chdir(tmp_path)
    code = "\n".join(["def long_func():"] + ["    pass"] * 51)
    (tmp_path / "test.py").write_text(code, encoding="utf-8")
    result = runner.invoke(app, ["run", "--strict"])
    assert result.exit_code == 1


def test_no_strict_warning_exits_zero(monkeypatch, tmp_path) -> None:
    """Without --strict, warnings return zero exit code."""
    monkeypatch.chdir(tmp_path)
    code = "\n".join(["def long_func():"] + ["    pass"] * 51)
    (tmp_path / "test.py").write_text(code, encoding="utf-8")
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0


def test_error_exits_nonzero(monkeypatch, tmp_path) -> None:
    """Errors return non-zero exit code even without --strict."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "test.py").write_text("eval('1+1')", encoding="utf-8")
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 1


def test_no_violations_exits_zero(monkeypatch, tmp_path) -> None:
    """No violations returns zero exit code."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "test.py").write_text("x = 1", encoding="utf-8")
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0


def test_run_writes_state_file(monkeypatch, tmp_path) -> None:
    """Run should persist state to .harness/harness-lint-state.json."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "test.py").write_text("eval('1+1')", encoding="utf-8")
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 1
    state_file = tmp_path / ".harness" / "harness-lint-state.json"
    assert state_file.exists()
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert "rules" in data
    assert "violation_count" in data
    assert data["violation_count"] == 1


# --- Help and version tests ---


def test_help_contains_parameters() -> None:
    """Help text should mention path, --format, and --strict."""
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "Output format" in result.output
    assert "Treat warnings" in result.output
    assert "PATH" in result.output or "path" in result.output

def test_version_flag() -> None:
    """--version should print version and exit."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.3.0" in result.output


def test_version_short_flag() -> None:
    """-v should print version and exit."""
    result = runner.invoke(app, ["-v"])
    assert result.exit_code == 0
    assert "0.3.0" in result.output
