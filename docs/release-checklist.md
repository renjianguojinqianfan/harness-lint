# Release Checklist

> 集中开发后的发版收尾清单。配套 `AGENTS.md §4 Working Guidelines` 中"代码改动同步文档"原则。
>
> 适用范围：本项目（Python 包 + setuptools + PyPI trusted publishing + GitHub Actions）。
> 本清单基于 v0.1.0 → v0.2.0 实战流程整理。

---

## 一、决策前置：要不要发版？

动文档前先回答 3 个问题：

| 问题 | 判断标准 |
|---|---|
| 自上次发版以来有什么变化？ | `git log v<last>..HEAD --oneline` + 翻 PR 列表 |
| 属于哪种 SemVer 升级？ | breaking → major；新功能向后兼容 → minor；纯 bugfix/格式 → patch |
| PyPI 上当前版本号还能用吗？ | 不能。PyPI 不允许覆盖已发布版本，必须升号 |

**SemVer 速查**（Python 包语境）：

- `MAJOR`：删除/重命名公共 API、改变默认行为、退出码语义变化
- `MINOR`：新增规则/命令/参数、新增可选依赖、新增配置项
- `PATCH`：bug 修复、文档/CHANGELOG/格式、性能优化、内部重构

---

## 二、版本号同步矩阵（高漏率区）

**版本号不止一处。漏改一个，CLI 输出会和包元数据不一致。**

| 文件 | 字段 | 是否必改 | 备注 |
|---|---|---|---|
| `pyproject.toml` | `[project] version` | 必改 | PyPI 实际识别的版本号 |
| `src/harness_lint/__init__.py` | `__version__` | 必改 | Python 代码读取的版本号 |
| `src/harness_lint/cli.py` | `version_callback` 内的硬编码字符串 | 必改 | `--version` 输出 |
| `tests/test_cli.py` | `--version` / `-v` 断言 | 必改 | 不改测试会红 |
| `src/harness_lint/pbh_adapter.py` | `_CURRENT_VERSION` | **不改** | PBH 协议版本号，与包版本号语义独立 |
| `tests/test_pbh_adapter.py` | `harness_version` 测试断言 | **不改** | 跟随 `_CURRENT_VERSION` |

### 防漏改的搜索命令

```powershell
grep "<old-version>" --include="*.py" --include="*.toml" --include="*.md"
```

> **教训**：v0.2.0 发版时 `pbh_adapter.py:10` 也匹配到了 `0.1.0`，第一直觉是改，但它是协议兼容性版本号（跟 `.harness/progress.json` 里的 `harness_version` 配套），跟 PyPI 包版本无关。**不要看到字符串就改，要看语义**。

---

## 三、CHANGELOG.md 归档

格式：[Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)。

### 归档操作

1. `[Unreleased]` 内容**整体迁移**到 `[<new-version>] - YYYY-MM-DD`
2. `[Unreleased]` **重置为空**（保留标题，方便下个周期累积）
3. **更新比较链接**：
   - `[Unreleased]` 改为 `compare/v<new>...HEAD`
   - 新增 `[<new>]` 行：`compare/v<old>...v<new>`
4. 不要删旧版本条目

### 内容质量自检

每个变更项至少包含：

- **变更分类**（Added / Changed / Deprecated / Removed / Fixed / Security）
- **影响范围**（具体文件路径或模块）
- **简短归因**（为什么改）

Bad: `修复了 bug`

Good: `修复 hl401_repeated_pattern.py 在 ruff format --check 下不通过的格式问题（折叠多行函数签名为单行），解除 CI lint job 红灯`

---

## 四、必备元数据文件

### `LICENSE`

- 必须存在于 repo 根目录
- 内容与 `README.md` 声明的协议一致（避免"README 写 MIT，pyproject 没写"的不一致）

### `pyproject.toml` 必备字段

- `[project]`：`name`、`version`、`description`、`readme`、`requires-python`、`license`、`authors`、`classifiers`、`dependencies`
- `[project.urls]`：`Homepage`、`Repository`、`Issues`、`Changelog`
- `[project.scripts]`：CLI 入口

### 文档文件（按需更新）

| 文件 | 何时更新 |
|---|---|
| `README.md` | 新增/删除 CLI 参数、规则数量变化、安装方式变化 |
| `README.en.md`（如有） | 与 README.md 同步变更 |
| `docs/PROJECT_MAP.md` | 新增/删除核心模块、目录结构变化 |
| `docs/context.md` | 架构演进、设计决策变化 |
| `docs/decisions/` ADR | 重大架构选择（不可逆决策） |
| `docs/design.md` | **冻结契约文件，原则上不动** |
| `AGENTS.md` | AI 协作规则变化（行数硬上限 80） |
| `.harness/known_pitfalls.md` | 实战踩坑记录 |

> **教训**：v0.2.0 周期 PR #4 不得不一次性同步 README/CHANGELOG/PROJECT_MAP/context 共 5 文件，是因为 PR #2/#3 没把文档当成代码改动的一部分。**每个 PR 都应该自检配套文档同步**，不要等到发版前补。

---

## 五、本地预飞行检查（合并前）

```bash
# 1. 完整验证
make verify
# 期望：lint pass + tests pass + coverage >= 阈值

# 2. 本地构建
python -m build --outdir <tmp-dir>
# 期望：sdist + wheel 都生成，文件名版本号正确

# 3. PyPI 元数据校验
twine check <tmp-dir>/*
# 期望：双 PASSED

# 4. 防止漏改
grep "<old-version>" --include="*.py" --include="*.toml"
# 期望：只剩你确认不该改的位置（如 PBH 协议版本号）
```

**任何一项不通过 → 不要提 PR**。

---

## 六、PR + Tag + 发布流程

### 标准发版 PR

- **分支命名**：`release/v<version>`
- **标题**：`release: v<version>`
- **PR body 必含**：
  - SemVer 升级理由
  - 改动清单（哪些文件改了什么）
  - **明确不改动的字段**（防止 reviewer 困惑）
  - 本地验证结果
  - 后续发布流程预告

### 合并方式

- **squash merge**：单一 release commit，历史干净
- 注意：squash 后**本地** release 分支会被 git 视为"未合并"（commit SHA 不在 main 祖先链）
  - 远程：auto-delete head branches 自动清理
  - 本地：必须 `git branch -D <branch>`（先用 `git diff main <branch> --stat` 验证内容已进 main）

### Tag 推送（触发 publish workflow）

```bash
git checkout main
git fetch origin              # 必须先 fetch
git pull --ff-only origin main
git tag -a v<version> -m "Release v<version>" <merge-commit-sha>
git push origin v<version>
```

必须先 fetch 后 pull——否则 tag 会打在旧 commit 上。

---

## 七、发布后验证（必做，不能假设成功）

### Workflow 状态检查

```bash
gh run list --workflow publish.yml --limit 1
gh run view <run-id>
```

**所有 job 都必须 success**（不只是 build，还要 publish 和 release）。

### PyPI 真实上传验证（防 `skip-existing` 静默跳过）

```bash
# 直接命中版本端点
curl https://pypi.org/pypi/<pkg>/<version>/json
# 期望：200，且 info.version == <new-version>
```

`skip-existing: true` 是双刃剑：版本号没升的话会静默跳过，workflow 显示 success 但实际啥都没传。**必须查 publish job 日志确认看到 `Uploading <pkg>-<version>...`**。

### GitHub Release 验证

```bash
gh release view v<version>
```

期望：

- `tag: v<version>` 正确
- `assets:` 包含 `.whl` + `.tar.gz`

### PyPI 缓存延迟

PyPI JSON `latest` 字段（`/pypi/<pkg>/json`）有 fastly 边缘缓存，可能 30 秒到几分钟才更新。**版本端点**（`/pypi/<pkg>/<version>/json`）通常即时可用。

---

## 八、Trusted Publishing 前置条件（首次发版必须配，后续无感）

发版前确认：

- [ ] PyPI 项目页面 → Settings → Publishing → 已添加 trusted publisher
  - Owner: `<github-org>`
  - Repository: `<repo>`
  - Workflow filename: `publish.yml`
  - Environment: `pypi`
- [ ] GitHub repo → Settings → Environments → 存在名为 `pypi` 的 environment
- [ ] `publish.yml` 配置：
  - `permissions: id-token: write`
  - `environment: pypi`

```bash
# 验证 environment 存在
gh api "repos/<org>/<repo>/environments" --jq ".environments[].name"
# 期望输出：pypi
```

---

## 九、清洁度收尾

### 远程分支

- 仅剩 `main`（auto-delete head branches 处理）
- 验证：`git ls-remote --heads origin`

### 本地分支

- 删除已 squash merge 的本地分支
- 验证：`git branch` 仅剩 `main`

### Working tree

- `git status --short` 输出空

### Tag

- `git tag --list` 包含新版本
- 远程：`git ls-remote --tags origin` 包含新版本

---

## 十、推荐 Checklist 模板（直接抄进发版 PR body）

```markdown
## v<X.Y.Z> 发版检查清单

### 决策
- [ ] SemVer 升级类型确认（major/minor/patch）
- [ ] PyPI 上 v<X.Y.Z> 不存在

### 版本号同步
- [ ] pyproject.toml `version`
- [ ] src/<pkg>/__init__.py `__version__`
- [ ] src/<pkg>/cli.py `version_callback` 字符串
- [ ] tests/test_cli.py `--version` 断言

### 文档
- [ ] CHANGELOG.md 归档 [Unreleased] → [<X.Y.Z>] - YYYY-MM-DD
- [ ] CHANGELOG.md 比较链接更新
- [ ] README.md / README.en.md 必要同步
- [ ] docs/PROJECT_MAP.md 同步（若结构变化）

### 元数据
- [ ] LICENSE 存在
- [ ] pyproject.toml 含 license / classifiers / project.urls

### 本地验证
- [ ] make verify 通过
- [ ] python -m build 成功
- [ ] twine check 双 PASSED

### 发布
- [ ] PR squash 合并到 main
- [ ] git tag -a v<X.Y.Z> 打在合并 commit
- [ ] git push origin v<X.Y.Z>
- [ ] publish workflow 全 3 job success
- [ ] PyPI /pypi/<pkg>/<X.Y.Z>/json 返回 200
- [ ] GitHub Release v<X.Y.Z> 含 .whl + .tar.gz

### 收尾
- [ ] 远程仅剩 main
- [ ] 本地仅剩 main
- [ ] working tree clean
```




