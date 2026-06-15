# harness-lint

> PBH ecosystem's first fruit — a static checker that catches typical bad habits in AI-generated code.

harness-lint is **not a replacement** for Ruff / Pylint / Flake8. Those tools answer "is the code well-formatted?"; harness-lint answers **"is the AI faking completion?"**.

## Quick Start

```bash
pip install -e ".[dev]"
make verify
```

Lint any directory:

```bash
harness-lint                       # Lint current directory, terminal format
harness-lint src/                  # Lint a specific path
harness-lint --format json         # JSON output
harness-lint --format summary      # One-line summary
harness-lint --strict              # Treat warnings as exit code 1
harness-lint --version
```

Exit codes:
- `0` — no Errors; without `--strict`, Warning/Info also return 0
- `1` — Error present; or `--strict` enabled with any Warning

## Built-in Rules

9 rules ship by default, all enabled.

| ID | Name | Severity | Description |
|----|------|----------|-------------|
| HL001 | No eval() | Error | Detects direct `eval(...)` / `builtins.eval(...)` calls |
| HL002 | No exec() | Error | Detects direct `exec(...)` calls |
| HL003 | No os.system() | Error | Steers you toward `subprocess.run()` |
| HL004 | Hardcoded secrets | Error | Detects `password = "xxx"` and annotated forms like `password: str = "xxx"` |
| HL201 | Function length | Warning | Default threshold 50 lines; covers sync and async |
| HL202 | Fake exception handling | Warning | Catches `except: pass`, `except Exception: pass` and similar no-ops |
| HL301 | Missing docstring | Info | Public APIs without a docstring |
| HL401 | Repeated pattern | Warning | Same anti-pattern occurring 3+ times in one file is escalated as a systemic deviation |
| HL402 | Protocol consistency | Warning | Public functions missing parameter / return-type annotations |

Every violation report carries the full **attribution-anchor triple**:

- **phenomenon** — what's wrong concretely
- **attribution** — why this is an AI defect
- **agente_ref** — which AGENTS.md clause was violated

## Commands

| Command | Description |
|---------|-------------|
| `make verify` | lint + tests + coverage (must pass before commit) |
| `make test` | run tests |
| `make lint` | code style check |
| `make fix` | auto-fix style issues |

## Project Structure

```
harness-lint/
├── src/harness_lint/
│   ├── cli.py                # CLI entry (typer)
│   ├── checker.py            # File walker + rule dispatcher
│   ├── reporter.py           # terminal / json / summary outputs
│   ├── accumulator.py        # Pattern-deviation cost accumulator
│   ├── attribution.py        # Runtime attribution-chain validation
│   ├── pbh_adapter.py        # Reads .harness/progress.json
│   ├── degradation.py        # Degradation-cost visibility
│   └── rules/
│       ├── base.py           # Rule / Violation abstract base
│       └── hl0*.py / hl2*.py / hl3*.py / hl4*.py
├── tests/                    # Unit + integration + bootstrap tests
├── docs/                     # Design / project map / ADRs
├── tasks/                    # Spec Coding container
├── .harness/                 # PBH phase state tracking
├── AGENTS.md                 # AI collaboration protocol
├── Makefile
└── pyproject.toml
```

## AI Collaboration

This project follows the PBH protocol. AI assistants should read `AGENTS.md` for project rules and working guidelines. See `docs/context.md` for deep architecture and `docs/design.md` for rule design principles.

## Ecosystem

| Project | Description |
|---------|-------------|
| [Project Bootstrap Harness (PBH)](https://github.com/renjianguojinqianfan/Project-Bootstrap-Harness) | AI-assisted project bootstrap framework defining phase-awareness, attribution anchoring, and core protocols |
| [Harness Agent](https://github.com/renjianguojinqianfan/harness-agent) | AI Agent runtime for the PBH protocol, responsible for plan execution and session lifecycle management |

harness-lint is the quality guardian in the PBH ecosystem, performing static analysis on AI-generated code during agent execution.

## License

MIT
