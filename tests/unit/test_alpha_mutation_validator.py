import pytest
from unittest.mock import MagicMock
import sys

# Mocking missing dependencies
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

from agent.aether_orchestrator.alpha_evolve import MutationValidator

class TestMutationValidator:
    def test_is_safe_mutation_success(self):
        original = "def hello():\n    print('hello')"
        mutated = "def hello():\n    print('hello world')"
        is_safe, reason = MutationValidator.is_safe_mutation(original, mutated)
        assert is_safe is True
        assert reason == "Mutation is safe"

    @pytest.mark.parametrize("dangerous_code", [
        "os.system('rm -rf /')",
        "shutil.rmtree('/etc')",
        "os.remove('important.txt')",
        "subprocess.call(['ls'])",
        "eval('1+1')",
        "exec('print(1)')",
        "__import__('os').system('ls')",
        "open('file.txt', 'w')",
        "pickle.loads(data)",
        "yaml.load(stream)",
        "execfile('script.py')",
        "rm -rf /",
    ])
    def test_is_safe_mutation_dangerous_patterns(self, dangerous_code):
        original = "print('hello')"
        mutated = f"print('hello')\n{dangerous_code}"
        is_safe, reason = MutationValidator.is_safe_mutation(original, mutated)
        assert is_safe is False
        assert "Dangerous pattern detected" in reason

    def test_is_safe_mutation_too_large(self):
        original = "print('hello')"
        mutated = "print('hello')\n" + "print('world')\n" * 100
        is_safe, reason = MutationValidator.is_safe_mutation(original, mutated)
        assert is_safe is False
        assert reason == "Mutation is too large (>5x original)"

    def test_is_safe_mutation_empty(self):
        original = "print('hello')"
        mutated = ""
        is_safe, reason = MutationValidator.is_safe_mutation(original, mutated)
        assert is_safe is False
        assert reason == "Mutation is empty"

    def test_is_safe_mutation_whitespace_only(self):
        original = "print('hello')"
        mutated = "   \n\t  "
        is_safe, reason = MutationValidator.is_safe_mutation(original, mutated)
        assert is_safe is False
        assert reason == "Mutation is empty"

    def test_is_safe_mutation_comments_only(self):
        original = "print('hello')"
        mutated = "# This is just a comment\n# Another one"
        is_safe, reason = MutationValidator.is_safe_mutation(original, mutated)
        assert is_safe is False
        assert reason == "Mutation contains only comments"

    def test_is_safe_mutation_syntax_error(self):
        original = "print('hello')"
        mutated = "print('hello'"  # Missing closing parenthesis
        is_safe, reason = MutationValidator.is_safe_mutation(original, mutated)
        assert is_safe is False
        assert "Syntax error in mutation" in reason
