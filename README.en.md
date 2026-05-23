# harness-lint

> PBH ecosystem's first fruit — a static checker that catches typical bad habits in AI-generated code.


## Quick Start

```bash
pip install -e ".[dev]"
make verify
```

## Commands

| Command | Description |
|---------|-------------|
| `make verify` | lint + tests + coverage |
| `make test` | run tests |
| `make lint` | code style check |
| `make fix` | auto-fix style issues |

## Project Structure

```
harness-lint/
├── src/harness_lint/   # Main code
├── tests/                # Tests
├── tasks/                # Task breakdown
├── docs/                 # Documentation
├── AGENTS.md             # AI collaboration protocol
├── Makefile
└── pyproject.toml
```

## AI Collaboration

This project follows the PBH protocol. AI assistants should read `AGENTS.md` for project rules and working guidelines.

## Ecosystem

| Project | Description |
|---------|-------------|
| [Project Bootstrap Harness (PBH)](https://github.com/renjianguojinqianfan/Project-Bootstrap-Harness) | AI-assisted project bootstrap framework defining phase-awareness, attribution anchoring, and core protocols |
| [Harness Agent](https://github.com/renjianguojinqianfan/harness-agent) | AI Agent runtime for the PBH protocol, responsible for plan execution and session lifecycle management |

harness-lint is the quality guardian in the PBH ecosystem, performing static analysis on AI-generated code during agent execution.

## License

MIT