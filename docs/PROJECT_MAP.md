---
project: harness-lint
package: harness_lint
version: "0.1.0"
map_type: static
audience: agent
last_updated: "2026-06-15"
---

# PROJECT_MAP — harness-lint

> Machine-readable project structure map.
> For the human-readable quick reference, see `AGENTS.md` §6 File Mapping.
> For deep architecture context, see `docs/context.md`.

## 1. Project Overview

| Attribute | Value |
|-----------|-------|
| Name | harness-lint |
| Package | harness_lint |
| Type | cli |
| Language | Python 3.11+ |
| CLI framework | typer |

**Design philosophy**: Protocol-first scaffolding. The project ships with a universal agent collaboration protocol (AGENTS.md) and quality gates (`make verify`). `make verify` is the ground truth for correctness.

## 2. Directory Structure

```
harness-lint/
├── .harness/                    # Project state tracking
│   ├── templates/               # Plan templates and boilerplate
│   ├── progress.json            # Session state source of truth
│   └── known_pitfalls.md        # Recurring issues log
├── docs/                        # Project documentation
│   ├── PROJECT_MAP.md           # This file — machine-readable structure map
│   ├── context.md               # Deep context: architecture, conventions
│   ├── design.md                # Frozen design contract for v0.1.0
│   └── decisions/               # Architecture Decision Records (ADR)
│       └── ADR_TEMPLATE.md
├── src/harness_lint/            # Main application source
│   ├── __init__.py              # Package marker
│   ├── cli.py                   # CLI entry (typer); orchestrates checker + reporter
│   ├── checker.py               # File walker + rule dispatcher
│   ├── reporter.py              # terminal / json / summary output formatters
│   ├── accumulator.py           # Pattern-deviation cost accumulator
│   ├── attribution.py           # Runtime attribution-chain validation
│   ├── degradation.py           # Degradation-cost visibility
│   ├── pbh_adapter.py           # Reads .harness/progress.json for phase context
│   └── rules/                   # Rule implementations
│       ├── __init__.py          # Re-exports rule classes
│       ├── base.py              # Rule (ABC) + Violation (frozen dataclass)
│       ├── hl001_eval.py        # HL001 — no eval() (Error)
│       ├── hl002_exec.py        # HL002 — no exec() (Error)
│       ├── hl003_os_system.py   # HL003 — no os.system() (Error)
│       ├── hl004_hardcoded_secrets.py  # HL004 — hardcoded secrets, Assign + AnnAssign (Error)
│       ├── hl201_function_length.py    # HL201 — function length > 50 (Warning)
│       ├── hl202_fake_exception.py     # HL202 — fake exception handling (Warning)
│       ├── hl301_no_docstring.py       # HL301 — public function missing docstring (Info)
│       ├── hl401_repeated_pattern.py   # HL401 — repeated anti-pattern detection (Warning)
│       └── hl402_protocol_consistency.py  # HL402 — public APIs missing type hints (Warning)
├── tests/                       # Test suites (mirrors src/ layout)
│   ├── __init__.py
│   ├── test_bootstrap.py        # Self-lint test: harness-lint passes its own checks
│   ├── test_checker.py          # File walker + rule dispatcher tests
│   ├── test_cli.py              # CLI tests (exit codes, formats, --strict)
│   ├── test_attribution.py      # Attribution chain validation tests
│   ├── test_accumulator.py      # Cost accumulation + PatternWarning tests
│   ├── test_degradation.py      # Degradation notice tests
│   ├── test_pbh_adapter.py      # progress.json loading tests
│   ├── test_reporter.py         # terminal/json/summary formatter tests
│   ├── rules/                   # Per-rule tests
│   │   ├── test_base.py
│   │   ├── test_hl001_eval.py
│   │   ├── test_hl002_exec.py
│   │   ├── test_hl003_os_system.py
│   │   ├── test_hl004_hardcoded_secrets.py
│   │   ├── test_hl201_function_length.py
│   │   ├── test_hl202_fake_exception.py
│   │   ├── test_hl301_no_docstring.py
│   │   ├── test_hl401_repeated_pattern.py
│   │   └── test_hl402_protocol_consistency.py
│   └── fixtures/                # Test fixtures
├── tasks/                       # Task breakdown (Spec Coding container)
├── AGENTS.md                    # Agent quick-reference (≤80 lines)
├── CHANGELOG.md                 # Keep-a-Changelog format release notes
├── Makefile                     # verify, test, lint, fix targets
├── pyproject.toml               # Project metadata and dependencies
├── README.md                    # User-facing documentation (中文)
├── README.en.md                 # User-facing documentation (English)
├── SECURITY.md                  # Security policy
└── .gitignore
```

## 3. Key Files

### 3.1 Core Source

| File | Purpose | Agent Notes |
|------|---------|-------------|
| `src/harness_lint/cli.py` | CLI parsing, rule registration, output dispatch | Keep thin; new logic goes elsewhere |
| `src/harness_lint/checker.py` | Recursive `.py` walk + per-file AST dispatch to active rules | Phase-awareness gates rule activation |
| `src/harness_lint/reporter.py` | Three output formats: terminal/json/summary | Add new format = new function with same signature |
| `src/harness_lint/accumulator.py` | Counts violations by `rule_id`; emits `PatternWarning` once threshold hit | Threshold default 3; configurable |
| `src/harness_lint/attribution.py` | `validate_rule_attribution`, `validate_violation`, `validate_ruleset` | Runtime safety net for the attribution chain |
| `src/harness_lint/pbh_adapter.py` | Loads phase from `.harness/progress.json`; returns `Context(phase, hint)` | Missing/malformed file → `Context(phase=None)` (non-fatal) |
| `src/harness_lint/degradation.py` | Renders the "Harness-Lint not enabled" notice with cost data | Triggers when CLI cannot detect itself in the project |
| `src/harness_lint/rules/base.py` | `Rule` ABC + `Violation` frozen dataclass | All rules subclass `Rule`; `_create_violation()` auto-fills metadata |

### 3.2 Rules

All 9 rules live in `src/harness_lint/rules/` and are registered in `_get_default_rules()` in `cli.py`.

| Rule | Severity | Category |
|------|----------|----------|
| HL001 — no eval() | Error | Security |
| HL002 — no exec() | Error | Security |
| HL003 — no os.system() | Error | Security |
| HL004 — hardcoded secrets | Error | Security |
| HL201 — function length | Warning | AI code quality |
| HL202 — fake exception | Warning | AI code quality |
| HL301 — no docstring | Info | AI code quality |
| HL401 — repeated pattern | Warning | Pattern deviation |
| HL402 — protocol consistency | Warning | Pattern deviation |

### 3.3 Configuration & Build

| File | Purpose | Agent Notes |
|------|---------|-------------|
| `pyproject.toml` | Dependencies, build config, ruff settings | Add new deps in `[project.dependencies]` |
| `Makefile` | `make verify`, `make test`, `make lint`, `make fix` | Always run `make verify` before commit |

### 3.4 Documentation

| File | Purpose | Agent Notes |
|------|---------|-------------|
| `AGENTS.md` | Quick agent map and rules | Read first on every new session |
| `docs/context.md` | Deep architecture and conventions | Read before architectural decisions |
| `docs/design.md` | Frozen v0.1.0 design contract (Chinese) | Source of truth for rule design intent |
| `docs/decisions/` | ADR records | One file per major decision |
| `docs/PROJECT_MAP.md` | This file — structure reference | Use for file location lookups |
| `CHANGELOG.md` | Release notes (Keep a Changelog) | Update `[Unreleased]` on every user-visible change |

### 3.5 Runtime Artifacts

| File / Dir | Purpose | Agent Notes |
|------------|---------|-------------|
| `.harness/progress.json` | Session state source of truth | Atomic write-then-rename only |
| `.harness/known_pitfalls.md` | Recurring issues log | Append discoveries that cost >15 min to debug |

## 4. Dependencies

Declared in `pyproject.toml`:

- **Runtime**: `typer`
- **Dev**: `pytest`, `pytest-cov`, `ruff`

Install all: `pip install -e ".[dev]"`

## 5. Entry Points

| Entry Point | File | Description |
|-------------|------|-------------|
| CLI command `harness-lint` | `src/harness_lint/cli.py:cli` | Main user-facing interface |
| Python module | `python -m harness_lint` | Programmatic entry |
| Verification | `make verify` | Run lint + tests + coverage |

## 6. Conventions for Agents

- **File length**: ≤ 200 lines; refactor early
- **Function length**: ≤ 30 lines (HL201 will catch you above 50)
- **Test mirroring**: Every module in `src/` has a matching test in `tests/`; rules test under `tests/rules/`
- **Naming**: `snake_case` modules, `PascalCase` classes, `snake_case` functions, `UPPER_SNAKE_CASE` constants
- **State safety**: Use atomic write-then-rename for JSON files
- **Ground truth**: `make verify` output is the only valid correctness signal — see AGENTS.md §5
- **Attribution chain**: Every new rule must populate `agente_ref` and `attribution` (enforced at construction time by `Rule.__post_init__`)
- **No abstractions for single-use cases**: AGENTS.md §4 — extracted helpers must have ≥ 2 call sites

---

*This map is static. For current runtime state, see `.harness/progress.json`.*
