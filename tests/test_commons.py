import unittest

from unclutter_directory.commons.parsers import parse_size, parse_time
from unclutter_directory.commons.validations import validate_rules_file


class TestCommons(unittest.TestCase):
    def test_parse_size(self):
        # Test different size units
        self.assertEqual(parse_size("1KB"), 1024)
        self.assertEqual(parse_size("1MB"), 1024**2)
        self.assertEqual(parse_size("1GB"), 1024**3)

        # Test raw numbers
        self.assertEqual(parse_size("1024"), 1024)

        # Test with spaces
        self.assertEqual(parse_size("1 KB"), 1024)

        # Test case insensitivity
        self.assertEqual(parse_size("1kb"), 1024)

        # Test invalid input
        with self.assertRaises(ValueError):
            parse_size("invalid")

    def test_parse_time(self):
        # Test different time units
        self.assertEqual(parse_time("1s"), 1)
        self.assertEqual(parse_time("1m"), 60)
        self.assertEqual(parse_time("1h"), 3600)
        self.assertEqual(parse_time("1d"), 86400)

        # Test raw numbers
        self.assertEqual(parse_time("60"), 60)

        # Test with spaces
        self.assertEqual(parse_time("1 h"), 3600)

        # Test invalid input
        with self.assertRaises(ValueError):
            parse_time("invalid")

    def test_validate_rules_file(self):
        # Test valid rules
        valid_rules = [
            {
                "conditions": {"larger": "1KB", "newer": "1d"},
                "action": {"type": "move", "target": "/path/to/target"},
                "check_archive": True,
            },
            {  # Additional valid from test_is_valid_rule_conditions
                "conditions": {"larger": "10MB"},
                "action": {"type": "move", "target": "/path/to/target"},
            },
            {"conditions": {"contain": "keyword"}, "action": {"type": "delete"}},
            {
                "conditions": {"regex": "[a-z]+"},
                "action": {"type": "compress", "target": "."},
            },
            {  # Additional valid from test_is_valid_rule_action
                "conditions": {"larger": "10MB"},
                "action": {"type": "delete"},
            },
            {
                "conditions": {"larger": "10MB"},
                "action": {"type": "compress", "target": "."},
            },
            {  # Additional valid from test_is_valid_rule_check_archive
                "conditions": {"larger": "10MB"},
                "action": {"type": "delete"},
                "check_archive": False,
            },
            {
                "conditions": {"larger": "10MB"},
                "action": {"type": "delete"},
                "check_archive": True,
            },
        ]
        for i, rule in enumerate(valid_rules):
            self.assertEqual(
                validate_rules_file([rule]), [], f"Valid rule #{i + 1} should pass"
            )

        # Test invalid rules format
        self.assertTrue(len(validate_rules_file("not a list")) > 0)

        # Test invalid rule structure
        invalid_rules = [
            "not a dict",
            {"conditions": "not a dict"},
            {"conditions": {"invalid": "value"}},
            {"conditions": {"larger": "invalid"}},
            {"conditions": {"newer": "invalid"}},
            {"conditions": {"regex": "["}},
            {"action": "not a dict"},
            {"conditions": {"larger": "10MB"}, "action": {"type": "invalid"}},
            {"conditions": {"larger": "10MB"}, "action": {"type": "move"}},
            {"check_archive": "not a bool"},
            # Additional invalid from test_is_valid_rule_conditions
            {"conditions": {"invalid_condition": "10MB"}, "action": {}},
            {"conditions": {"larger": "abc"}, "action": {}},
            {"conditions": {"older": "abc"}, "action": {}},
            {"conditions": {"regex": "[invalid[regex]"}, "action": {}},
            # Additional invalid from test_is_valid_rule_action
            {"conditions": {"larger": "10MB"}, "action": {}},
            {"conditions": {"larger": "10MB"}, "action": {"type": "invalid_type"}},
            {"conditions": {"larger": "10MB"}, "action": {"type": "move"}},
            # Additional invalid from test_is_valid_rule_check_archive
            {
                "conditions": {"larger": "10MB"},
                "action": {"type": "delete"},
                "check_archive": 42,
            },
        ]
        for i, rule in enumerate(invalid_rules):
            errors = validate_rules_file([rule])
            self.assertTrue(len(errors) > 0, f"Invalid rule #{i + 1} should fail")
            if isinstance(rule, dict):
                if rule.get("action") == {"type": "move"} or (
                    rule.get("conditions")
                    and rule.get("action", {}).get("type") == "move"
                ):
                    self.assertIn("'target'", errors[0])
                elif "check_archive" in rule and isinstance(rule["check_archive"], int):
                    self.assertIn("must be boolean", errors[0])


if __name__ == "__main__":
    unittest.main()
