import unittest

from unclutter_directory.commons import parse_size, parse_time, is_valid_rules_file

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

    def test_is_valid_rules_file(self):
        # Test valid rules
        valid_rules = [{
            "conditions": {"larger": "1KB", "newer": "1d"},
            "action": {"type": "move", "target": "/path/to/target"},
            "check_archive": True
        }]
        self.assertEqual(is_valid_rules_file(valid_rules), [])
        
        # Test invalid rules format
        self.assertTrue(len(is_valid_rules_file("not a list")) > 0)
        
        # Test invalid rule structure
        invalid_rules = [
            "not a dict",
            {"conditions": "not a dict"},
            {"conditions": {"invalid": "value"}},
            {"conditions": {"larger": "invalid"}},
            {"conditions": {"newer": "invalid"}},
            {"conditions": {"regex": "["}},
            {"action": "not a dict"},
            {"action": {"type": "invalid"}},
            {"action": {"type": "move"}},
            {"check_archive": "not a bool"}
        ]
        for rule in invalid_rules:
            self.assertTrue(len(is_valid_rules_file([rule])) > 0)

    def test_is_valid_rule_conditions(self):
        valid_rules = [
            {
                "conditions": {"larger": "10MB"},
                "action": {"type": "move", "target": "/path/to/target"}
            },
            {
                "conditions": {"contain": "keyword"},
                "action": {"type": "delete"}
            },
            {
                "conditions": {"regex": "[a-z]+"},
                "action": {"type": "compress"}
            }
        ]

        invalid_rules = [
            # Invalid condition type
            {"conditions": {"invalid_condition": "10MB"}, "action": {}},
            
            # Invalid size value
            {"conditions": {"larger": "abc"}, "action": {}},

            # Invalid time value
            {"conditions": {"older": "abc"}, "action": {}},

            # Invalid regular expression
            {"conditions": {"regex": "[invalid[regex]"}, "action": {}}
        ]

        for i, rule in enumerate(valid_rules):
            errors = is_valid_rules_file([rule])
            self.assertEqual(errors, [], f"Rule #{i + 1} should be valid")

        for i, rule in enumerate(invalid_rules):
            errors = is_valid_rules_file([rule])
            self.assertTrue(len(errors) > 0, f"Rule #{i + 1} should be invalid")
            self.assertIn("Rule #1", errors[0])

    def test_is_valid_rule_action(self):
        valid_actions = [
            {"type": "move", "target": "/path/to/target"},
            {"type": "delete"},
            {"type": "compress"}
        ]

        invalid_actions = [
            # Missing type
            {},
            
            # Invalid action type
            {"type": "invalid_type"},
            
            # Move action without target
            {"type": "move"}
        ]

        for i, action in enumerate(valid_actions):
            rule = {"conditions": {}, "action": action}
            errors = is_valid_rules_file([rule])
            self.assertEqual(errors, [], f"Action #{i + 1} should be valid")

        for i, action in enumerate(invalid_actions):
            rule = {"conditions": {}, "action": action}
            errors = is_valid_rules_file([rule])
            self.assertTrue(len(errors) > 0, f"Action #{i + 1} should be invalid")
            if action.get("type") == "move":
                self.assertIn("'target'", errors[0])

    def test_is_valid_rule_check_archive(self):
        valid_rules = [
            {"conditions": {}, "action": {"type": "delete"}, "check_archive": False},
            {"conditions": {}, "action": {"type": "delete"}, "check_archive": True}
        ]

        invalid_rules = [
            # Non-boolean check_archive value
            {"conditions": {}, "action": {"type": "delete"}, "check_archive": 42}
        ]

        for i, rule in enumerate(valid_rules):
            errors = is_valid_rules_file([rule])
            self.assertEqual(errors, [], f"Rule #{i + 1} should be valid")

        for i, rule in enumerate(invalid_rules):
            errors = is_valid_rules_file([rule])
            self.assertTrue(len(errors) > 0, f"Rule #{i + 1} should be invalid")
            self.assertIn("must be a boolean", errors[0])


if __name__ == "__main__":
    unittest.main()
