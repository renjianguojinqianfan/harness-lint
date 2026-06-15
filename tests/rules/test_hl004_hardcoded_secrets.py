"""Tests for HL004: Hardcoded secrets detection."""

from __future__ import annotations

import ast

from harness_lint.attribution import validate_violation
from harness_lint.rules.hl004_hardcoded_secrets import HL004HardcodedSecretsRule


class TestHL004HardcodedSecretsRule:
    """Tests for the HL004 hardcoded secrets detection rule."""

    def test_password_string_detected(self) -> None:
        """password = 'secret123' should be detected."""
        code = 'password = "secret123"\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.line == 1
        assert v.rule_id == "HL004"
        assert v.severity == "Error"
        assert "password" in v.phenomenon

    def test_api_key_detected(self) -> None:
        """api_key = 'sk-12345' should be detected."""
        code = 'api_key = "sk-12345"\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "api_key" in v.phenomenon

    def test_uppercase_token_detected(self) -> None:
        """TOKEN = 'abc' should be detected (case insensitive)."""
        code = 'TOKEN = "abc"\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1

    def test_empty_string_not_detected(self) -> None:
        """password = '' should NOT be detected."""
        code = 'password = ""\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_placeholder_not_detected(self) -> None:
        """password = 'changeme' should NOT be detected."""
        code = 'password = "changeme"\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_environ_get_not_detected(self) -> None:
        """password = os.environ.get('PASSWORD') should NOT be detected."""
        code = 'password = os.environ.get("PASSWORD")\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_my_password_detected(self) -> None:
        """my_password = 'real_secret' should be detected."""
        code = 'my_password = "real_secret"\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1

    def test_no_secrets_returns_none(self) -> None:
        """Code without sensitive variables should return None."""
        code = "x = 1 + 1\nname = 'hello'\n"
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_violation_contains_full_attribution_chain(self) -> None:
        """Each violation must contain the full attribution chain."""
        code = 'password = "secret123"\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.attribution == "硬编码密钥存在泄露风险，应使用环境变量或 .env 文件"
        assert v.agente_ref == "AGENTS.md §5 Critical Rules"
        assert validate_violation(v) == []

    def test_secret_key_detected(self) -> None:
        """secret_key = 'key123' should be detected."""
        code = 'secret_key = "key123"\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert "secret_key" in v.phenomenon

    def test_multiple_secrets_multiple_violations(self) -> None:
        """Multiple hardcoded secrets should return multiple violations."""
        code = '''password = "secret1"
api_key = "key123"
'''
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 2

    def test_non_string_value_not_detected(self) -> None:
        """password = get_password() should NOT be detected."""
        code = "password = get_password()\n"
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_os_getenv_not_detected(self) -> None:
        """token = os.getenv('TOKEN') should NOT be detected."""
        code = 'token = os.getenv("TOKEN")\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_annotated_password_detected(self) -> None:
        """password: str = 'secret123' (AnnAssign) should be detected."""
        code = 'password: str = "secret123"\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        v = result[0]
        assert v.rule_id == "HL004"
        assert "password" in v.phenomenon

    def test_annotated_api_key_detected(self) -> None:
        """api_key: str = 'sk-12345' (AnnAssign) should be detected."""
        code = 'api_key: str = "sk-12345"\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is not None
        assert len(result) == 1
        assert "api_key" in result[0].phenomenon

    def test_annotated_empty_not_detected(self) -> None:
        """password: str = '' (AnnAssign) should NOT be detected."""
        code = 'password: str = ""\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_annotated_placeholder_not_detected(self) -> None:
        """password: str = 'changeme' (AnnAssign) should NOT be detected."""
        code = 'password: str = "changeme"\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_annotated_environ_get_not_detected(self) -> None:
        """password: str = os.environ.get('PW') (AnnAssign) should NOT be detected."""
        code = 'password: str = os.environ.get("PW")\n'
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_annotation_without_value_not_detected(self) -> None:
        """password: str (AnnAssign without value) should NOT be detected."""
        code = "password: str\n"
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []

    def test_annotated_non_string_not_detected(self) -> None:
        """password: int = 123 (AnnAssign with non-string value) should NOT be detected."""
        code = "password: int = 123\n"
        tree = ast.parse(code)
        rule = HL004HardcodedSecretsRule()
        result = rule.check("test.py", code, tree)

        assert result is None or result == []
