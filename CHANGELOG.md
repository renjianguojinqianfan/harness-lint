# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`python -m harness_lint` 支持** (`src/harness_lint/__main__.py`) — 通过 Typer `app()` 派发，等价于 `harness-lint` 控制台脚本
- **PBH 阶段字段兼容** (`src/harness_lint/pbh_adapter.py`) — `get_context` 优先读 `phase`，缺失时回退 `current_stage`，皆无则记 warning 日志降级默认模式；抽取 `_resolve_phase` 辅助函数
- **运行状态持久化** (`src/harness_lint/cli.py`) — `run` 在检查完成后调用 `degradation.record_run_state`，将规则元数据、违规计数与去重 agente_refs 写入 `.harness/harness-lint-state.json`
- **JSON 报告格式规范** (`docs/LINT-REPORT-SCHEMA-v1.md`) — 定义 `--format=json` 输出契约（顶层字段、Violation 对象、版本策略）

### Changed

- **移除退化短路退出** (`src/harness_lint/cli.py`) — 删除 `_handle_degradation` 中检查 `.harness/harness-lint-enabled` 不存在即 `exit(0)` 的门控；非 PBH 项目不再静默退出，检查始终执行。PBH 感知保留为 `pbh_adapter.get_context` 的自动检测增强特性，不作前置条件；`degradation.py` 模块作为可用能力保留
- **自检与项目阶段解耦** (`tests/test_bootstrap.py`) — `test_self_check_passes` 改用 `Context(phase=None)` 显式构造，始终跑全部规则，不受项目当前 `current_stage` 影响
- **`make verify` 增加格式检查** (`Makefile`) — 新增 `format-check` 目标（`ruff format --check src/`），`verify` 现按 `lint → format-check → test` 三阶段执行，本地与 CI 一致

## [0.2.0] - 2026-06-15

### Added

- **HL002：禁止 exec()** (`src/harness_lint/rules/hl002_exec.py`) — 安全类规则（Error），AST 检测 `exec(...)` 直接调用
- **HL003：禁止 os.system()** (`src/harness_lint/rules/hl003_os_system.py`) — 安全类规则（Error），引导改用 `subprocess.run()`
- **HL004：硬编码密钥检测** (`src/harness_lint/rules/hl004_hardcoded_secrets.py`) — 安全类规则（Error）
  - 覆盖 `Assign`：`password = "xxx"`、`API_KEY = b"..."` 等裸赋值
  - 覆盖 `AnnAssign`：`password: str = "xxx"` 等带类型标注的赋值
  - 通过 `_check_value` 统一字符串与字节串字面量的密钥模式检测
- **HL202：假异常处理** (`src/harness_lint/rules/hl202_fake_exception.py`) — AI 代码质量类规则（Warning）
  - 检测 `except: pass`、`except Exception: pass` 等无效异常处理
- **HL301：公共函数无 docstring** (`src/harness_lint/rules/hl301_no_docstring.py`) — AI 代码质量类规则（Info）
- **HL401：重复违规模式检测** (`src/harness_lint/rules/hl401_repeated_pattern.py`) — 模式性偏差规则（Warning）
  - 单文件内同一反模式出现 3+ 次时报告，覆盖 bare except、`except Exception`、specific-except-with-pass 三类
- **HL402：协议一致性检查** (`src/harness_lint/rules/hl402_protocol_consistency.py`) — 模式性偏差规则（Warning）
  - 检测公共函数的参数（除 `self`/`cls`）与返回值缺失类型标注，对应 AGENTS.md §4
- 项目元数据：`LICENSE` (MIT)、`pyproject.toml` 增加 `license`、`classifiers`、`project.urls` 字段

### Changed

- HL004：删除 `_check_assign` / `_check_ann_assign` 中的 `_is_env_call` 死分支，并移除已无调用点的 `_is_env_call` 方法（遵循 AGENTS.md §4 "no abstractions for single-use cases"）
- 默认规则集由 2 条扩展到 9 条（`src/harness_lint/cli.py`）

### Fixed

- 修复 `hl401_repeated_pattern.py` 与 `hl402_protocol_consistency.py` 在 `ruff format --check src/` 下不通过的格式问题（折叠多行函数签名与 format 调用为单行），解除 CI lint job 红灯

## [0.1.0] - 2026-04-28

### Added

#### Core Engine

- **Violation 和 Rule 数据类** (`src/harness_lint/rules/base.py`)
  - `Violation`（frozen dataclass）：承载完整的归因链三要素——现象 (phenomenon)、归因 (attribution)、归属 (agente_ref)
  - `Rule`（abstract dataclass）：所有规则的抽象基类，定义 `rule_id`、`name`、`severity`、`message_template`、`phases`、`agente_ref`、`attribution` 等元数据字段
- **文件遍历器** (`src/harness_lint/checker.py`)
  - 递归扫描 `.py` 文件，默认忽略 `.git/`、`__pycache__/`、`.venv/`、`.mypy_cache/`、`.pytest_cache/`
  - 阶段感知规则激活（execute / evaluate / None）
- **Reporter 输出协议** (`src/harness_lint/reporter.py`)
  - Terminal 格式：带 ANSI 颜色的文件分组输出，含汇总统计和模式性偏差块
  - JSON 格式：结构化输出（summary + violations + pattern_warnings）
  - Summary 格式：单行紧凑摘要

#### Pre-defined Rules

- **HL001：禁止 eval()** (`src/harness_lint/rules/hl001_eval.py`)
  - 安全类规则（Error），通过 AST 遍历检测 `eval()` 直接调用
  - 支持 `eval(...)`、`builtins.eval(...)`、`__builtins__.eval(...)` 三种形式
  - 归属：AGENTS.md §5 Critical Rules
- **HL201：函数体长度超限** (`src/harness_lint/rules/hl201_function_length.py`)
  - AI 代码质量类规则（Warning），默认阈值 50 行
  - 支持普通函数和 async 函数，阈值可配置
  - 归属：AGENTS.md §5 Critical Rules

#### Attribution Anchoring Mechanism

- **三层防护归因锚定** (`src/harness_lint/rules/base.py` + `src/harness_lint/attribution.py`)
  - 构造时强制：`Rule.__post_init__` 验证 `agente_ref` 和 `attribution` 非空
  - 构建时自动：`Rule._create_violation()` 自动填充规则元数据到 Violation
  - 运行时验证：`validate_rule_attribution()`、`validate_violation()`、`validate_ruleset()` 独立检查归因链完整性

#### Cost Accumulation

- **偏差代价累积机制** (`src/harness_lint/accumulator.py`)
  - 按 `rule_id` 统计违规次数，达到阈值（默认 3）时升级为 Elevated Warning
  - phenomenon 变更为"该冲突已持续出现 N 次，尚未解决"
  - Evaluate 阶段 Elevated Warning 自动升级为 Error（CI 阻断）
  - `PatternWarning` 数据类：记录规则描述、出现次数和改进建议
- **退化代价可见化** (`src/harness_lint/degradation.py`)
  - 停用/卸载时输出"当前未启用 Harness-Lint"
  - 展示启用期间的规则总数、最近一次违规数量、不再被验证的 AGENTS.md 条款列表

#### CLI & PBH Adapter

- **CLI 入口** (`src/harness_lint/cli.py`)
  - 命令格式：`harness-lint [PATH] [--format terminal|json|summary] [--strict]`
  - 默认 PATH = 当前目录，默认 format = terminal
  - 退出码约定：Error → 1；Warning/Info → 0；`--strict` + Warning → 1
  - 退化检测：未启用时输出退化提示并退出
- **PBH 适配器** (`src/harness_lint/pbh_adapter.py`)
  - 读取 `.harness/progress.json` 获取阶段上下文
  - 支持 `plan` / `execute` / `evaluate` / `done` 四个 phase
  - 版本兼容性检查（harness_version 不匹配时在 hint 中追加警告）
  - 文件不存在或格式错误时返回 `Context(phase=None)`，不阻塞检查流程

#### Bootstrap

- **自举测试** (`tests/test_bootstrap.py`)
  - harness-lint 检查自身代码，验证返回 0 违规
  - 验证所有规则的归因链完整性（agente_ref + attribution）

### Fixed

- HL201 的 `agente_ref` 从 "AGENTS.md §4 Working Guidelines" 修正为 "AGENTS.md §5 Critical Rules"
- Terminal 输出增加 evaluate 阶段提示行（"💡 当前处于 Evaluate 阶段..."）
- `PatternWarning` 增加 `description` 字段，支持输出规则名称（如"HL201 函数体长度超限已出现 3 次"）
- Summary 格式中 pattern_warnings 使用换行符拼接，替代管道符 `|` 拼接
- 退化提示中 AGENTS.md 条款列表增加防御性去重

[Unreleased]: https://github.com/renjianguojinqianfan/harness-lint/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/renjianguojinqianfan/harness-lint/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/renjianguojinqianfan/harness-lint/releases/tag/v0.1.0
