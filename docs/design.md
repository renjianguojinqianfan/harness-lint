\# Harness-Lint 设计文档



\*\*版本\*\*：v0.1.0  

\*\*状态\*\*：设计冻结，可进入原型开发  

\*\*定位\*\*：PBH 生态的第一个“果实”工具



---



\## 1. 项目定位



Harness-Lint 是一个专门针对 \*\*AI 生成代码的易错模式\*\* 的静态合规检查工具。它以 Python CLI 形态运行，检查视角不是“代码是否符合 PEP 8”，而是 \*\*“代码是否暴露了 AI 编程时的典型坏习惯”\*\*。



它不识别“哪些代码是 AI 写的”，而是直接对项目中所有源代码执行 AI 缺陷模式检查。



它不替代 Flake8 / Pylint / Ruff。那些工具检查的是“代码是否规范”。Harness-Lint 检查的是 \*\*“AI 是否在假装完成了任务”\*\*。



---



\## 2. 核心设计原则



1\. \*\*每一条规则必须有“为什么是 AI 缺陷”的解释\*\*。不能因为“PEP 8 说了”而加规则。只能因为“AI 经常在这里犯错”而加规则。



2\. \*\*默认规则集就是全部规则集\*\*。不提供隐藏的高级规则。用户看到的预置列表，就是全部。



3\. \*\*错误信息必须可行动\*\*。不能说“你错了”，必须说“你应该怎么做”。例如：“禁止使用 os.system()，请使用 subprocess.run() 替代”。



4\. \*\*自己是自己的第一个用户\*\*。Harness-Lint 的开发过程必须用自身的 make verify 检查自身代码（自举）。



5\. \*\*继承 PBH 的克制\*\*。不越界成为通用 Lint 工具。不给通用规则。不染指 Ruff 的领地。



6\. \*\*规则必须透明且可理解\*\*：每条规则的检测逻辑应能被非核心开发者在 5 分钟内读懂。这是保持项目可维护性和社区贡献门槛的底线。



---



\## 3. 输出协议硬约束



> \*\*任何无法指向 AGENTS.md 的规则输出，都是不完整的。\*\*



Harness-Lint 的每一条规则输出，必须同时包含以下三个要素：



| 要素 | 含义 | 示例 |

| :--- | :--- | :--- |

| \*\*现象\*\* (What) | 发生了什么违规 | `HL201: 函数 process\_data 长度 67 行（阈值 50 行）` |

| \*\*归因\*\* (Why) | 为什么会发生 | `↳ 原因：AGENTS.md 未明确定义函数长度上限` |

| \*\*归属\*\* (Where) | 应写入 AGENTS.md 的哪个位置 | `↳ 归属：AGENTS.md §X 行为准则` |



\*\*标准输出结构\*\*（固化）：



```text

\[RULE\_ID] 现象描述

↳ 原因：规则缺失 / 未遵守

↳ 归属：AGENTS.md §X.X

```



此结构不得在任何优化中简化或省略归因与归属行。任何缺失归因链的规则输出，视为 Bug。



---



\## 4. 偏差代价累积机制



\### 4.1 渐进累积机制



Harness-Lint 的违规不是平等的。同一违规模式若反复出现，其权重将逐步升级：



| 出现次数 | 级别 | 行为 |

| :--- | :--- | :--- |

| 首次 | Warning | 报告违规，提示修复 |

| 第 N 次（可配置阈值） | Elevated Warning | 信息变更为“该冲突已持续出现 N 次，尚未解决” |

| Evaluate 阶段 | Error（CI 阻断） | Elevated Warning 在 Evaluate 阶段自动升级为 Error |



\### 4.2 阶段感知



通过读取 `.harness/progress.json` 的 `phase` 字段，动态调整检查严格程度：



| 阶段 | 行为 |

| :--- | :--- |

| Execute 阶段 | 只激活安全类和确定性质量类规则，抑制风格噪声 |

| Evaluate 阶段 | 激活全部规则。Elevated Warning 升级为 Error |



\### 4.3 退化代价可见化



当 Harness-Lint 被停用或卸载时：

\- 首次运行 `make verify` 输出“当前未启用 Harness-Lint”

\- 同时展示启用期间的规则总数、最近一次报告的违规数量

\- 列出当前因停用而不再被验证的 AGENTS.md 条款列表



退化不是被禁止的，但退化是\*\*被系统记录的、被显性报告的、需要刻意为之的\*\*。



---



\## 5. 架构分层



```

入口层 (cli)          解析命令，派发任务

引擎层 (checker)      遍历文件，按阶段激活规则，收集违规

适配层 (pbh\_adapter)  读取 progress.json，提供阶段上下文

规则层 (rules)        每条规则：id / name / severity / message / phases / check()

输出层 (reporter)     终端彩色表格 / JSON / Summary（含归因锚定）

```



---



\## 6. 模块设计



\### 6.1 入口层 (cli)



命令：



```

harness-lint \[PATH] \[--format terminal|json|summary]

```



\- PATH：目标路径，默认当前目录

\- --format：输出格式，默认 terminal



行为：解析参数 → 调用 pbh\_adapter 获取阶段上下文 → 传给 checker → 将违规列表传给 reporter。



\### 6.2 引擎层 (checker)



核心函数：`check(path, context) -> list\[Violation]`



行为：

1\. 递归扫描 path 下所有 .py 文件

2\. 遍历默认忽略：`.git/`、`\_\_pycache\_\_/`、`.venv/`、`.mypy\_cache/`、`.pytest\_cache/`

3\. 对每个文件调用所有已激活的规则

4\. “已激活”由 context.phase 和规则的 phases 字段共同决定

5\. 返回所有违规列表



阶段感知：

\- Execute 阶段：仅激活 phases 含 "execute" 的规则

\- Evaluate 阶段：激活 phases 含 "evaluate" 的全部规则

\- 无 PBH 上下文时：激活所有规则（最严格模式）



\### 6.3 规则层 (rules)



规则对象模型：



```

Rule:

&nbsp; id: str

&nbsp; name: str

&nbsp; severity: "Error" | "Warning" | "Info"

&nbsp; message\_template: str

&nbsp; phases: list\[str]  # \["execute", "evaluate"]

&nbsp; agente\_ref: str    # 指向 AGENTS.md 的具体条款

&nbsp; check(file\_path, file\_content, ast\_tree) -> list\[Violation] | None

```



规则 ID 命名约定：

\- HL1xx：安全类

\- HL2xx：AI 代码质量类

\- HL3xx：文档与可读性类

\- HL4xx：协议一致性与归因类（新增）

\- HL5xx：保留扩展位



\#### 安全类（severity: Error，phases: \["execute", "evaluate"]）



| ID | 规则 | 说明 |

| :--- | :--- | :--- |

| HL001 | 禁止 eval() | AI 可能用 eval 实现“灵活执行”，导致代码注入 |

| HL002 | 禁止 exec() | 同上 |

| HL003 | 禁止 os.system() | 应使用 subprocess.run() 替代 |

| HL004 | 硬编码密钥检测 | 匹配 password = "..."、api\_key = "..." 等模式 |



\#### AI 代码质量类（severity: Warning，phases: \["execute", "evaluate"]）



| ID | 规则 | 说明 |

| :--- | :--- | :--- |

| HL201 | 函数体长度超限 | 默认阈值 50 行。AI 容易生成巨型函数 |

| HL202 | 假异常处理 | 检测 except: pass 和 except: print(e) 等无效处理 |



\#### 文档与可读性类（severity: Info，phases: \["evaluate"]）



| ID | 规则 | 说明 |

| :--- | :--- | :--- |

| HL301 | 公共函数无 docstring | AI 倾向“写完功能就收工” |



\#### 协议一致性类（severity: Warning → Elevated），新增



| ID | 规则 | 说明 |

| :--- | :--- | :--- |

| HL401 | 重复违规模式检测 | 同一违规模式出现 ≥N 次，合并为模式性偏差报告 |

| HL402 | 协议一致性检查 | 检测 AI 行为模式与 AGENTS.md 条款的冲突，显性化报告 |



HL402 的渐进累积逻辑：

\- 首次冲突 → Warning

\- 累计 N 次 → Elevated Warning

\- Evaluate 阶段 → Error（阻断 CI）



v0.1.0 共 9 条预置规则（安全 4 + 质量 2 + 文档 1 + 协议一致性 2）。



\### 6.4 适配层 (pbh\_adapter)



核心函数：`get\_context(path) -> Context`



Context 对象：



```

Context:

&nbsp; phase: "plan" | "execute" | "evaluate" | "done" | None

&nbsp; harness\_version: str | None

&nbsp; hint: str  # 如“当前为评估阶段，建议严格执行风格检查”

```



行为：

1\. 检查 path/.harness/progress.json 是否存在

2\. 若存在，解析 JSON 提取 phase 字段

3\. 若文件不存在或格式错误，返回 Context(phase=None)，不阻塞检查流程

4\. 若 harness\_version 与当前版本不兼容，输出 Warning 但继续执行



\### 6.5 输出层 (reporter)



\#### Terminal 格式（默认）



```

📄 src/myproject/core.py

&nbsp; 12:5   ❌ HL003 禁止使用 os.system()

&nbsp;        ↳ 原因：使用了不安全的系统调用

&nbsp;        ↳ 归属：AGENTS.md §5 Critical Rules

&nbsp; 45:1   ⚠️  HL201 函数 process\_data 长度 67 行（阈值 50 行）

&nbsp;        ↳ 原因：AGENTS.md 未定义函数长度上限

&nbsp;        ↳ 归属：AGENTS.md §4 Working Guidelines



📊 检查汇总

&nbsp; ❌ Error:   1

&nbsp; ⚠️  Warning: 1

&nbsp; ℹ️  Info:    0

&nbsp; 检查文件数: 5

&nbsp; 违规文件数: 2



💡 当前处于 Evaluate 阶段，建议优先完成所有规则固化。



⚠️ 模式性偏差：

&nbsp; HL202 假异常处理已出现 8 次

&nbsp; 建议在 AGENTS.md §5 Critical Rules 中明确异常处理规范

```



\- 违规位置使用 file:line:col 标准路径格式，支持终端点击跳转

\- 严重级别颜色：Error=红色，Warning=黄色，Info=蓝色

\- 每条违规必须包含现象（What）、归因（Why）、归属（Where）三行



\#### JSON 格式（--format json）



```

{

&nbsp; "summary": {

&nbsp;   "errors": 1,

&nbsp;   "warnings": 1,

&nbsp;   "info": 0,

&nbsp;   "files\_checked": 5

&nbsp; },

&nbsp; "violations": \[

&nbsp;   {

&nbsp;     "file": "src/myproject/core.py",

&nbsp;     "line": 12,

&nbsp;     "column": 5,

&nbsp;     "rule\_id": "HL003",

&nbsp;     "severity": "Error",

&nbsp;     "phenomenon": "禁止使用 os.system()",

&nbsp;     "attribution": "使用了不安全的系统调用",

&nbsp;     "agente\_ref": "AGENTS.md §5 Critical Rules"

&nbsp;   }

&nbsp; ],

&nbsp; "pattern\_warnings": \[

&nbsp;   {

&nbsp;     "rule\_id": "HL202",

&nbsp;     "count": 8,

&nbsp;     "suggestion": "建议在 AGENTS.md §5 中明确异常处理规范"

&nbsp;   }

&nbsp; ]

}

```



\#### Summary 格式（--format summary）



```

harness-lint: 1 error, 1 warning, 0 info (checked 5 files)

⚠️ 模式性偏差：HL202 出现 8 次

```



---



\## 7. 与 PBH 的协作流程



```

1\. 项目初始化

&nbsp;  harness-init myproject

&nbsp;  → 种下 AGENTS.md + .harness/progress.json + Makefile



2\. 开发中

&nbsp;  AI 辅助开发，代码增长

&nbsp;  → .harness/progress.json 阶段可能被更新



3\. 质量门禁

&nbsp;  make verify 调用 harness-lint .

&nbsp;  → harness-lint 读取进度文件，感知阶段

&nbsp;  → 按阶段激活规则，输出报告（含归因锚定）



4\. 反馈闭环

&nbsp;  开发者看报告 → 识别规则缺失 → 补写 AGENTS.md → 再次 make verify → 通过

```



退出码约定：

\- 存在 Error 时返回非零（CI 失败）

\- 仅 Warning/Info 时返回零

\- --strict 模式将所有 Warning 也视为非零



---



\## 8. 验收标准



\- \[ ] 对 tests/fixtures/ 预置问题文件检出所有预期违规

\- \[ ] 无 .harness/ 目录的项目正常运行，不报错

\- \[ ] .harness/progress.json 存在且 phase=evaluate 时，输出含阶段提示

\- \[ ] --format terminal/json/summary 三种输出均正确，均含归因锚定

\- \[ ] HL402 的渐进累积机制正常运作（首次 Warning → 累计 N 次升级）

\- \[ ] 退化提示在 Harness-Lint 停用后正常触发

\- \[ ] \*\*所有规则输出均包含现象-归因-归属三要素\*\*

\- \[ ] make verify 对自身项目执行通过（自举）

\- \[ ] README 含完整“PBH 初始化→AI 开发→Harness-Lint 检查”流程截图



---



\## 9. 不在 v0.1.0 范围内的内容



| 内容 | 原因 |

| :--- | :--- |

| 用户自定义规则 | v0.1.0 聚焦预置规则集 |

| 自动修复 | 先发现问题，再考虑修复 |

| 规则忽略注释（如 # noqa） | v0.1.0 先做基础检查 |

| 非 Python 文件检查 | PBH 当前只支持 Python 项目 |

| 重复代码检测（原 HL104） | 实现复杂，误报率高，延后至 v0.2.0 |

| 导入合法性（幻觉）检测 | 依赖运行环境与依赖树解析，v0.2.0 候选 |

| 增量分析（只检查变更文件） | CI 常见需求但实现复杂度高，v0.2.0 候选 |



---



\## 10. 构建顺序



1\. Violation 和 Rule 的数据类定义（含 `agente\_ref` 字段）

2\. 文件遍历器（含忽略策略）

3\. \*\*输出协议固化\*\*（现象-归因-归属三段式——\*\*最高优先级\*\*）

4\. 预置规则逐个实现（从 HL001 开始，确定性最高）

5\. HL201 作为第一条带完整归因链的规则实现

6\. 归因锚定机制（每条规则绑定 AGENTS.md 条款引用）

7\. 代价累积逻辑（重复违规计数 + 阶段升级）

8\. 终端报告器（含归因锚定）

9\. CLI 入口

10\. pbh\_adapter

11\. JSON / Summary 格式

12\. 自举测试（用 harness-lint 检查 harness-lint，验证归因链完整性）



---



\## 11. 设计冻结确认



| 维度 | 状态 |

| :--- | :--- |

| 定位与边界 | ✅ 已冻结 |

| 输出协议硬约束（三要素） | ✅ 已冻结 |

| 架构分层 | ✅ 已冻结 |

| 规则集（9 条，含 HL401/HL402） | ✅ 已冻结 |

| 阶段感知逻辑 | ✅ 已冻结 |

| 渐进累积机制 | ✅ 已冻结 |

| 退化代价可见化 | ✅ 已冻结 |

| 输出格式（三种） | ✅ 已冻结 |

| CI 退出码约定 | ✅ 已冻结 |

| 范围排除 | ✅ 已冻结 |

| 设计原则（6 条） | ✅ 已冻结 |



---



\*\*可以开始了。期待看到第一条带归因链的规则亮起红灯。\*\*

