# harness-lint

> PBH 生态的第一个果实工具 — 专门检测 AI 生成代码中典型坏习惯的静态检查器。

harness-lint **不替代** Ruff / Pylint / Flake8。那些工具关心"代码是否规范"；harness-lint 关心**"AI 是否在假装完成了任务"**。

## 快速开始

```bash
pip install -e ".[dev]"
make verify
```

检查任意目录：

```bash
harness-lint                       # 检查当前目录，terminal 格式
harness-lint src/                  # 检查指定路径
harness-lint --format json         # 输出 JSON
harness-lint --format summary      # 输出单行摘要
harness-lint --strict              # 把 Warning 也视为退出码 1
harness-lint --version
```

退出码：
- `0` — 无 Error；`--strict` 关闭时 Warning/Info 也返回 0
- `1` — 有 Error；或 `--strict` 启用且有 Warning

## 内置规则

当前共 9 条规则，全部默认启用。

| ID | 名称 | 严重级别 | 说明 |
|----|------|----------|------|
| HL001 | 禁止使用 eval() | Error | 检测 `eval(...)` / `builtins.eval(...)` 直接调用 |
| HL002 | 禁止使用 exec() | Error | 检测 `exec(...)` 直接调用 |
| HL003 | 禁止使用 os.system() | Error | 引导改用 `subprocess.run()` |
| HL004 | 硬编码密钥检测 | Error | 检测 `password = "xxx"` / `password: str = "xxx"` 等带类型标注或裸赋值的硬编码密钥 |
| HL201 | 函数体长度超限 | Warning | 默认阈值 50 行，支持普通和 async 函数 |
| HL202 | 假异常处理 | Warning | 检测 `except: pass`、`except Exception: pass` 等无效异常处理 |
| HL301 | 公共函数无 docstring | Info | 公共 API 缺少 docstring |
| HL401 | 重复违规模式检测 | Warning | 同一文件出现 3+ 次相同反模式时升级为模式性偏差 |
| HL402 | 协议一致性检查 | Warning | 公共函数参数/返回值缺少类型标注 |

每条规则的违规报告都包含完整的**归因链三要素**：

- **现象 (phenomenon)**：违规的具体表现
- **归因 (attribution)**：为什么这是 AI 缺陷
- **归属 (agente_ref)**：违反了 AGENTS.md 的哪一条款

## 开发命令

| 命令 | 说明 |
|------|------|
| `make verify` | lint + 测试 + 覆盖率（提交前必须通过） |
| `make test` | 仅运行测试 |
| `make lint` | 仅运行代码风格检查 |
| `make fix` | 自动修复风格问题 |

## 项目结构

```
harness-lint/
├── src/harness_lint/
│   ├── cli.py                # CLI 入口（typer）
│   ├── checker.py            # 文件遍历 + 规则调度
│   ├── reporter.py           # terminal / json / summary 三种输出
│   ├── accumulator.py        # 模式性偏差累积（重复违规升级）
│   ├── attribution.py        # 归因链运行时校验
│   ├── pbh_adapter.py        # 读取 .harness/progress.json
│   ├── degradation.py        # 退化代价可见化
│   └── rules/
│       ├── base.py           # Rule / Violation 抽象基类
│       └── hl0*.py / hl2*.py / hl3*.py / hl4*.py
├── tests/                    # 单元测试 + 集成测试 + 自举测试
├── docs/                     # 设计文档 / 项目地图 / ADR
├── tasks/                    # 任务拆解（Spec Coding 容器）
├── .harness/                 # PBH 阶段状态追踪
├── AGENTS.md                 # AI 协作协议
├── Makefile
└── pyproject.toml
```

## AI 协作

本项目遵循 PBH 协议。AI 助手请阅读 `AGENTS.md` 了解项目规则和工作准则。深入架构请参考 `docs/context.md`，规则设计原则参考 `docs/design.md`。

## 生态关联

| 项目 | 说明 |
|------|------|
| [Project Bootstrap Harness (PBH)](https://github.com/renjianguojinqianfan/Project-Bootstrap-Harness) | AI 辅助项目启动框架，定义了阶段感知、归因锚定等核心协议 |
| [Harness Agent](https://github.com/renjianguojinqianfan/harness-agent) | PBH 协议的 AI Agent 运行时，负责执行计划、管理会话生命周期 |

harness-lint 是 PBH 生态中的质量守护工具，在 Agent 执行过程中对生成的代码进行静态检查。

## 许可证

MIT
