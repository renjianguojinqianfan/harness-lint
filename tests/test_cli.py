"""Tests for CLI entry point."""

import json

from typer.testing import CliRunner

from harness_lint.cli import app

runner = CliRunner()


# --- Degradation tests ---


def test_degradation_disabled_shows_notice(monkeypatch) -> None:
    """When disabled, CLI outputs degradation notice and exits 0."""
    monkeypatch.setattr("harness_lint.cli.is_harness_lint_enabled", lambda: False)
    monkeypatch.setattr(
        "harness_lint.cli.format_degradation_notice",
        lambda: "test degradation notice",
    )
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    assert "test degradation notice" in result.output


def test_degradation_disabled_no_notice(monkeypatch) -> None:
    """When disabled and no notice, outputs default message."""
    monkeypatch.setattr("harness_lint.cli.is_harness_lint_enabled", lambda: False)
    monkeypatch.setattr("harness_lint.cli.format_degradation_notice", lambda: None)
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    assert "当前未启用 Harness-Lint" in result.output


# --- Normal execution tests ---


def _enable_lint(monkeypatch) -> None:
    """Helper to monkeypatch harness-lint as enabled."""
    monkeypatch.setattr("harness_lint.cli.is_harness_lint_enabled", lambda: True)


def test_default_path_and_format(monkeypatch, tmp_path) -> None:
    """Default path is '.' and default format is terminal."""
    _enable_lint(monkeypatch)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    assert "✅" in result.output or "无违规发现" in result.output


def test_format_json(monkeypatch, tmp_path) -> None:
    """--format json outputs valid JSON."""
    _enable_lint(monkeypatch)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "summary" in data
    assert "violations" in data


def test_format_summary(monkeypatch, tmp_path) -> None:
    """--format summary outputs summary format."""
    _enable_lint(monkeypatch)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "--format", "summary"])
    assert result.exit_code == 0
    assert result.output.startswith("harness-lint:")


def test_strict_warning_exits_nonzero(monkeypatch, tmp_path) -> None:
    """--strict with warnings returns non-zero exit code."""
    _enable_lint(monkeypatch)
    monkeypatch.chdir(tmp_path)
    code = "\n".join(["def long_func():"] + ["    pass"] * 51)
    (tmp_path / "test.py").write_text(code, encoding="utf-8")
    result = runner.invoke(app, ["run", "--strict"])
    assert result.exit_code == 1


def test_no_strict_warning_exits_zero(monkeypatch, tmp_path) -> None:
    """Without --strict, warnings return zero exit code."""
    _enable_lint(monkeypatch)
    monkeypatch.chdir(tmp_path)
    code = "\n".join(["def long_func():"] + ["    pass"] * 51)
    (tmp_path / "test.py").write_text(code, encoding="utf-8")
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0


def test_error_exits_nonzero(monkeypatch, tmp_path) -> None:
    """Errors return non-zero exit code even without --strict."""
    _enable_lint(monkeypatch)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "test.py").write_text("eval('1+1')", encoding="utf-8")
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 1


def test_no_violations_exits_zero(monkeypatch, tmp_path) -> None:
    """No violations returns zero exit code."""
    _enable_lint(monkeypatch)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "test.py").write_text("x = 1", encoding="utf-8")
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0


# --- Help and version tests ---


def test_help_contains_parameters() -> None:
    """Help text should mention path, --format, and --strict."""
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "Output format" in result.output
    assert "--strict" in result.output
    assert "PATH" in result.output or "path" in result.output


def test_version_flag() -> None:
    """--version should print version and exit."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_version_short_flag() -> None:
    """-v should print version and exit."""
    result = runner.invoke(app, ["-v"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
