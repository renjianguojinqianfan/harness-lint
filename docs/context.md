# docs/context.md - harness-lint

## 1. Project Metadata

```yaml
name: harness-lint
version: 0.3.0
type: cli
tech_stack:
  language: Python 3.11+
  cli_framework: typer
  testing: pytest + pytest-cov
  linting: ruff
purpose: Static checker for typical bad habits in AI-generated code (PBH ecosystem)
```

## 2. Architecture Overview

harness-lint is **not** a general-purpose linter. It exists to detect patterns that AI agents typically produce when faking task completion. Every rule must answer: "Why is this an AI defect, not a style violation?"

### 2.1 Layered Design

```
┌─────────────────────────────────────────────────────┐
│  cli.py (typer)                                     │
│  - argument parsing, rule registration, exit codes  │
└────────────────────┬────────────────────────────────┘
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
┌────────────┐ ┌────────────┐ ┌────────────┐
│ checker.py │ │pbh_adapter │ │degradation │
│ - walk     │ │ - phase    │ │ - notice   │
│ - dispatch │ │ - context  │ │            │
└─────┬──────┘ └────────────┘ └────────────┘
      │
      ▼
┌─────────────────────────────────────────────┐
│  rules/                                     │
│  - base.py: Rule (ABC) + Violation          │
│  - hl00X / hl20X / hl30X / hl40X            │
└─────┬───────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────┐
│  accumulator.py    attribution.py           │
│  - PatternWarning  - chain validation       │
└─────┬───────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────┐
│  reporter.py: terminal | json | summary     │
└─────────────────────────────────────────────┘
```

### 2.2 Source Tree

```
src/harness_lint/
├── __main__.py        # `python -m harness_lint` entry; delegates to app()
├── cli.py             # CLI entry; orchestrates the pipeline
├── checker.py         # File walker + AST parsing + rule dispatch
├── reporter.py        # Three output formatters (terminal/json/summary)
├── accumulator.py     # Cost accumulation: 3+ same violations → PatternWarning
├── attribution.py     # Runtime validation of attribution chain integrity
├── pbh_adapter.py     # Loads phase context (phase → current_stage fallback)
├── degradation.py     # Persists run state; renders degradation notice
└── rules/
    ├── base.py        # Rule (ABC) + Violation (frozen dataclass)
    └── hl*.py         # 9 rule implementations
```

## 3. Core Concepts

### 3.1 Attribution Anchoring (归因锚定)

Every `Violation` carries three pieces of evidence:

- **phenomenon** — what's wrong concretely (e.g. "禁止使用 eval()")
- **attribution** — why this is an AI defect (e.g. "AI 倾向于用 eval 完成动态调度，但牺牲安全性")
- **agente_ref** — which AGENTS.md clause was violated (e.g. "AGENTS.md §5 Critical Rules")

Three layers of enforcement guarantee no rule slips without attribution:

1. **Construction time** — `Rule.__post_init__` raises if `agente_ref` or `attribution` is empty.
2. **Build time** — `Rule._create_violation()` auto-injects rule metadata into every `Violation`.
3. **Runtime** — `attribution.py` exposes `validate_rule_attribution`, `validate_violation`, `validate_ruleset` for defensive checks.

### 3.2 Phase Awareness (阶段感知)

`pbh_adapter.get_context(path)` reads `.harness/progress.json` and returns a `Context(phase, hint)`. Each rule declares which phases it activates in (`plan` / `execute` / `evaluate` / `None`). The checker only invokes a rule when the current phase intersects the rule's `phases`.

Phase resolution (in `_resolve_phase`): the `phase` field is read first; if absent, falls back to `current_stage`. If both are missing or invalid, a warning is logged and `phase=None` is returned. If `progress.json` itself is missing or malformed, `Context(phase=None)` is returned. In all default-mode cases checks proceed, but phase-specific behaviour (such as Elevated Warning → Error escalation) is skipped.

PBH awareness is an auto-detect enhancement, not a prerequisite: harness-lint runs normally in non-PBH projects without `.harness/`.

### 3.3 Cost Accumulation (代价累积)

`accumulator.py` counts violations by `rule_id`. Once any rule fires `THRESHOLD` times (default 3) within a single run, the accumulator emits a `PatternWarning` describing a systemic deviation rather than three isolated issues. In the `evaluate` phase, an Elevated Warning is auto-promoted to Error severity to block CI.

### 3.4 Degradation Visibility (退化可见化)

`degradation.py` provides two capabilities:

- **`record_run_state(rules, violations)`** — called by `cli.run()` after every check; persists rule metadata, violation count, and de-duplicated `agente_refs` to `.harness/harness-lint-state.json`. This snapshot feeds the degradation notice below.
- **`format_degradation_notice()`** — renders the cost of the tool being disabled (rule count, last violation count, AGENTS.md clauses no longer verified) from the recorded state.

The previous behaviour of gating execution on a `.harness/harness-lint-enabled` flag file (silently `exit(0)` when absent) has been **removed**. harness-lint now always runs its checks regardless of `.harness/` presence; the degradation notice is an informational capability, not a precondition.

### 3.5 Output Formats (Reporter)

`reporter.py` provides three formatters with the same signature `(violations, files_checked, pattern_warnings, *, phase) -> str`:

- `format_terminal` — file-grouped, ANSI-coloured, summary block + pattern warnings, evaluate-phase hint line
- `format_json` — structured `{summary, violations, pattern_warnings}` envelope
- `format_summary` — single-line digest suitable for CI logs

CLI tests turn off ANSI colours via env var to keep snapshots stable.

## 4. Rule Catalog

| ID | Severity | Phase | What it catches |
|----|----------|-------|-----------------|
| HL001 | Error | execute, evaluate | `eval(...)`, `builtins.eval(...)`, `__builtins__.eval(...)` |
| HL002 | Error | execute, evaluate | `exec(...)` |
| HL003 | Error | execute, evaluate | `os.system(...)` |
| HL004 | Error | execute, evaluate | Hardcoded secrets in `Assign` and `AnnAssign` (string + bytes literals) |
| HL201 | Warning | execute, evaluate | Function body > 50 lines (sync + async) |
| HL202 | Warning | execute, evaluate | `except: pass`, `except Exception: pass` and similar no-ops |
| HL301 | Info | execute, evaluate | Public functions missing docstring |
| HL401 | Warning | execute, evaluate | Same anti-pattern occurring 3+ times in one file |
| HL402 | Warning | execute, evaluate | Public functions missing parameter or return-type annotations |

Adding a new rule requires:

1. Subclass `Rule` in `src/harness_lint/rules/hlXXX_*.py` with `rule_id`, `name`, `severity`, `message_template`, `phases`, `agente_ref`, `attribution`.
2. Implement `check(file_path, file_content, ast_tree) -> list[Violation] | None`.
3. Re-export from `src/harness_lint/rules/__init__.py`.
4. Register in `_get_default_rules()` in `cli.py`.
5. Add `tests/rules/test_hlXXX_*.py` with positive + negative cases.
6. Run `make verify`. The bootstrap test will run harness-lint against itself.

## 5. Key Conventions

### 5.1 Code Organization
- All tests mirror the `src/` structure under `tests/`. Rule tests live under `tests/rules/`.
- Public APIs need type hints and docstrings (HL402 + HL301 will check it).
- No abstractions for single-use cases (AGENTS.md §4) — extracted helpers must have ≥ 2 call sites.

### 5.2 Naming Conventions
- Module names: `snake_case` (e.g. `hl004_hardcoded_secrets.py`)
- Class names: `PascalCase` (e.g. `HL004HardcodedSecretsRule`)
- Function and variable names: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### 5.3 Commit Format

```
<type>: <subject>

<body>

types: feat, fix, docs, test, refactor, chore, style
```

### 5.4 Plan File Format

Plans are JSON files following the schema at `.harness/templates/plan_template.json`.

## 6. Development Workflow

1. Read `AGENTS.md` for the quick project map.
2. Consult this file (`docs/context.md`) for architecture details.
3. Check `docs/design.md` if rule intent is unclear.
4. Run `make verify` before every commit. It must pass.

### 6.1 Adding a Feature

```bash
# 1. Write or update code in src/harness_lint/
# 2. Add tests in tests/ (mirror the src layout)
# 3. Verify before committing
make verify
```

### 6.2 Fixing a Bug

```bash
# 1. Reproduce the bug with a failing test
# 2. Fix the code in src/harness_lint/
# 3. Run tests to confirm the fix
make test
# 4. Full verification
make verify
```

### 6.3 Debugging Auto-fix Loops

AGENTS.md §5 enforces an **auto-fix circuit breaker**: max 2 attempts per error, then step back. If `make verify` fails after 2 fix attempts, document what was tried in `.harness/known_pitfalls.md` and ask before continuing.

## 7. Important Files

| File | Purpose |
|------|---------|
| `AGENTS.md` | Agent quick-reference (≤80 lines) |
| `docs/context.md` | Deep project context (this file) |
| `docs/design.md` | Frozen v0.1.0 design contract |
| `docs/PROJECT_MAP.md` | Machine-readable structure map |
| `docs/decisions/` | Architecture Decision Records |
| `src/harness_lint/` | Application source code |
| `.harness/progress.json` | Session state source of truth |
| `.harness/known_pitfalls.md` | Append-only debugging knowledge log |
| `tests/` | Test suites |
| `Makefile` | `make verify`, `make test`, `make lint`, `make format-check` |
| `docs/LINT-REPORT-SCHEMA-v1.md` | `--format=json` output schema spec |
| `CHANGELOG.md` | Keep a Changelog release notes |
