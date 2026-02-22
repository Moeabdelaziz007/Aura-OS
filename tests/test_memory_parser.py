import unittest
from agent.orchestrator.memory_parser import AuraNavigator

class TestMemoryParser(unittest.TestCase):
    def test_parse_blocks_multiple_yaml(self):
        navigator = AuraNavigator()
        # Mock content with multiple YAML blocks
        content = """
# Header

```yaml
key1: value1
```

Text

```yaml
key2: value2
```
        """
        raw_data = {"test.md": content}
        parsed = navigator._parse_blocks(raw_data)

        # Current implementation only gets the first block
        # We want it to get both merged
        expected = {"key1": "value1", "key2": "value2"}

        # This assertion will likely fail with the current implementation
        # creating a merged dictionary from all blocks
        self.assertEqual(parsed["test.md"], expected)

if __name__ == '__main__':
    unittest.main()
