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

## 生态关联

| 项目 | 说明 |
|------|------|
| [Project Bootstrap Harness (PBH)](https://github.com/renjianguojinqianfan/Project-Bootstrap-Harness) | AI 辅助项目启动框架，定义了阶段感知、归因锚定等核心协议 |
| [Harness Agent](https://github.com/renjianguojinqianfan/harness-agent) | PBH 协议的 AI Agent 运行时，负责执行计划、管理会话生命周期 |

harness-lint 是 PBH 生态中的质量守护工具，在 Agent 执行过程中对生成的代码进行静态检查。

## 许可证

MIT