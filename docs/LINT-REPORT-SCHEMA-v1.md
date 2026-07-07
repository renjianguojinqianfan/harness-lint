# Lint Report Schema v1.0

> 本文档定义 harness-lint 的 `--format=json` 输出格式规范。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `format_version` | string | ✅ | 固定值 `"1.0"` |
| `tool` | string | ✅ | 固定值 `"harness-lint"` |
| `violations` | array | ✅ | 违规项列表 |

## Violation 对象

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rule_id` | string | ✅ | 规则 ID（如 `"HL004"`） |
| `severity` | string | ✅ | 严重级别：`"error"` / `"warning"` / `"info"` |
| `file` | string | ✅ | 相对路径（如 `"src/auth.py"`） |
| `line` | integer | ✅ | 行号（1-based） |
| `column` | integer | ❌ | 列号（可选，如有则提供） |
| `evidence` | string | ✅ | 具体违规代码片段或证据描述 |
| `suggested_fix` | string | ❌ | 建议修复方案（人类可读文本，可选但强烈推荐） |
| `context` | string | ❌ | 上下文（如函数名、类名，可选） |

## 示例

```json
{
  "format_version": "1.0",
  "tool": "harness-lint",
  "violations": [
    {
      "rule_id": "HL004",
      "severity": "error",
      "file": "src/auth.py",
      "line": 42,
      "column": 15,
      "evidence": "检测到硬编码密钥: password='123456'",
      "suggested_fix": "将密钥移至环境变量，使用 os.getenv('AUTH_PASSWORD')",
      "context": "def login():"
    }
  ]
}
```

## 版本策略

- `format_version` 为语义化主版本号（MAJOR）
- 主版本升级允许不兼容变更，但应提供迁移指南
- 外部消费者应检查 `format_version`，拒绝解析不支持的版本
