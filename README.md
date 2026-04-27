# harness-lint

> PBH 生态的第一个果实工具 — 专门检测 AI 生成代码中典型坏习惯的静态检查器。

## 快速开始

```bash
pip install -e ".[dev]"
make verify
```

## 开发命令

| 命令 | 说明 |
|------|------|
| `make verify` | lint + 测试 + 覆盖率 |
| `make test` | 运行测试 |
| `make lint` | 代码风格检查 |
| `make fix` | 自动修复风格问题 |

## 项目结构

```
harness-lint/
├── src/harness_lint/   # 主代码
├── tests/                # 测试
├── tasks/                # 任务拆解
├── docs/                 # 文档
├── AGENTS.md             # AI 协作协议
├── Makefile
└── pyproject.toml
```

## AI 协作

本项目遵循 PBH 协议。AI 助手请阅读 `AGENTS.md` 了解项目规则和工作准则。

## 许可证

MIT