"""Tests for the PBH adapter module."""

from __future__ import annotations

import json
import logging

from harness_lint.checker import Context
from harness_lint.pbh_adapter import get_context


class TestGetContextFileNotFound:
    """Tests when .harness/progress.json does not exist."""

    def test_returns_none_phase_and_default_hint(self, tmp_path) -> None:
        """文件不存在 → phase=None, hint=默认提示."""
        context = get_context(str(tmp_path))
        assert isinstance(context, Context)
        assert context.phase is None
        assert context.harness_version is None
        assert context.hint == "无 PBH 上下文，启用最严格检查模式"


class TestGetContextValidPhases:
    """Tests for valid phase values in progress.json."""

    def _write_progress(self, tmp_path, **kwargs) -> None:
        """Helper to write progress.json with given data."""
        harness_dir = tmp_path / ".harness"
        harness_dir.mkdir()
        progress_file = harness_dir / "progress.json"
        progress_file.write_text(json.dumps(kwargs), encoding="utf-8")

    def test_phase_plan(self, tmp_path) -> None:
        """phase='plan' → 正确 phase 和 hint."""
        self._write_progress(tmp_path, phase="plan")
        context = get_context(str(tmp_path))
        assert context.phase == "plan"
        assert context.hint == "当前为规划阶段，建议先完善 AGENTS.md 规则定义"

    def test_phase_execute(self, tmp_path) -> None:
        """phase='execute' → 正确 phase 和 hint."""
        self._write_progress(tmp_path, phase="execute")
        context = get_context(str(tmp_path))
        assert context.phase == "execute"
        assert context.hint == "当前为执行阶段，安全类规则已激活"

    def test_phase_evaluate(self, tmp_path) -> None:
        """phase='evaluate' → 正确 phase 和 hint."""
        self._write_progress(tmp_path, phase="evaluate")
        context = get_context(str(tmp_path))
        assert context.phase == "evaluate"
        assert context.hint == "当前为评估阶段，建议严格执行风格检查"

    def test_phase_done(self, tmp_path) -> None:
        """phase='done' → 正确 phase 和 hint."""
        self._write_progress(tmp_path, phase="done")
        context = get_context(str(tmp_path))
        assert context.phase == "done"
        assert context.hint == "当前为完成阶段，所有检查项应已通过"


class TestGetContextInvalidCases:
    """Tests for invalid or malformed progress.json."""

    def test_invalid_json(self, tmp_path) -> None:
        """JSON 格式错误 → phase=None."""
        harness_dir = tmp_path / ".harness"
        harness_dir.mkdir()
        progress_file = harness_dir / "progress.json"
        progress_file.write_text("not json", encoding="utf-8")
        context = get_context(str(tmp_path))
        assert context.phase is None
        assert context.hint == "无 PBH 上下文，启用最严格检查模式"

    def test_invalid_phase_value(self, tmp_path) -> None:
        """phase 不在允许列表中 → phase=None."""
        harness_dir = tmp_path / ".harness"
        harness_dir.mkdir()
        progress_file = harness_dir / "progress.json"
        progress_file.write_text(json.dumps({"phase": "invalid"}), encoding="utf-8")
        context = get_context(str(tmp_path))
        assert context.phase is None
        assert context.hint == "无 PBH 上下文，启用最严格检查模式"

    def test_null_phase(self, tmp_path) -> None:
        """phase 为 null/None → phase=None."""
        harness_dir = tmp_path / ".harness"
        harness_dir.mkdir()
        progress_file = harness_dir / "progress.json"
        progress_file.write_text(json.dumps({"phase": None}), encoding="utf-8")
        context = get_context(str(tmp_path))
        assert context.phase is None
        assert context.hint == "无 PBH 上下文，启用最严格检查模式"

    def test_missing_phase_field(self, tmp_path) -> None:
        """缺少 phase 字段 → phase=None."""
        harness_dir = tmp_path / ".harness"
        harness_dir.mkdir()
        progress_file = harness_dir / "progress.json"
        progress_file.write_text(json.dumps({"harness_version": "0.1.0"}), encoding="utf-8")
        context = get_context(str(tmp_path))
        assert context.phase is None
        assert context.harness_version == "0.1.0"
        assert context.hint == "无 PBH 上下文，启用最严格检查模式"


class TestGetContextVersion:
    """Tests for harness_version handling."""

    def test_version_matches_current(self, tmp_path) -> None:
        """harness_version 与当前版本一致 → hint 不包含警告."""
        harness_dir = tmp_path / ".harness"
        harness_dir.mkdir()
        progress_file = harness_dir / "progress.json"
        progress_file.write_text(
            json.dumps({"phase": "execute", "harness_version": "0.1.0"}),
            encoding="utf-8",
        )
        context = get_context(str(tmp_path))
        assert context.phase == "execute"
        assert context.harness_version == "0.1.0"
        assert "警告" not in context.hint

    def test_version_mismatch(self, tmp_path) -> None:
        """harness_version 与当前版本不一致 → hint 包含警告."""
        harness_dir = tmp_path / ".harness"
        harness_dir.mkdir()
        progress_file = harness_dir / "progress.json"
        progress_file.write_text(
            json.dumps({"phase": "execute", "harness_version": "0.2.0"}),
            encoding="utf-8",
        )
        context = get_context(str(tmp_path))
        assert context.phase == "execute"
        assert context.harness_version == "0.2.0"
        assert "警告" in context.hint
        assert "0.2.0" in context.hint
        assert "0.1.0" in context.hint

    def test_harness_version_extracted(self, tmp_path) -> None:
        """文件存在且包含 harness_version 字段 → harness_version 正确."""
        harness_dir = tmp_path / ".harness"
        harness_dir.mkdir()
        progress_file = harness_dir / "progress.json"
        progress_file.write_text(
            json.dumps({"phase": "plan", "harness_version": "0.5.0"}),
            encoding="utf-8",
        )
        context = get_context(str(tmp_path))
        assert context.harness_version == "0.5.0"


def _write_progress(tmp_path, **kwargs) -> None:
    """Write progress.json with the given fields."""
    harness_dir = tmp_path / ".harness"
    harness_dir.mkdir()
    progress_file = harness_dir / "progress.json"
    progress_file.write_text(json.dumps(kwargs), encoding="utf-8")


class TestCurrentStageFallback:
    """Tests for current_stage fallback when phase is absent."""

    def test_current_stage_fallback(self, tmp_path) -> None:
        """phase 缺失、current_stage 有效 → 使用 current_stage 作为 phase."""
        _write_progress(tmp_path, current_stage="execute")
        context = get_context(str(tmp_path))
        assert context.phase == "execute"
        assert context.hint == "当前为执行阶段，安全类规则已激活"

    def test_current_stage_done(self, tmp_path) -> None:
        """current_stage='done' → phase='done'."""
        _write_progress(tmp_path, current_stage="done")
        context = get_context(str(tmp_path))
        assert context.phase == "done"
        assert context.hint == "当前为完成阶段，所有检查项应已通过"

    def test_phase_precedence_over_current_stage(self, tmp_path) -> None:
        """phase 与 current_stage 并存 → phase 胜出."""
        _write_progress(tmp_path, phase="plan", current_stage="execute")
        context = get_context(str(tmp_path))
        assert context.phase == "plan"
        assert context.hint == "当前为规划阶段，建议先完善 AGENTS.md 规则定义"

    def test_current_stage_fallback_logs_warning(self, tmp_path, caplog) -> None:
        """回退至 current_stage 时记录兼容提示日志."""
        _write_progress(tmp_path, current_stage="execute")
        with caplog.at_level(logging.WARNING, logger="harness_lint.pbh_adapter"):
            context = get_context(str(tmp_path))
        assert context.phase == "execute"
        assert any(
            "current_stage" in r.message and "phase" in r.message
            for r in caplog.records
        )

    def test_both_absent_logs_warning(self, tmp_path, caplog) -> None:
        """phase 与 current_stage 皆缺 → 降级并记录警告日志."""
        _write_progress(tmp_path, harness_version="0.1.0")
        with caplog.at_level(logging.WARNING, logger="harness_lint.pbh_adapter"):
            context = get_context(str(tmp_path))
        assert context.phase is None
        assert any("降级为默认检查模式" in r.message for r in caplog.records)
