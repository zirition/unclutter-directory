from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from unclutter_directory.FileMatcher import FileMatcher
from unclutter_directory.File import File, CompressedArchive

class TestFileMatcher(unittest.TestCase):
    def setUp(self):
        # Define some sample files for testing
        self.file1 = File(
            path=Path("/some/path"), name="example1.txt", date=100000, size=1000
        )
        self.file2 = File(
            path=Path("/some/path"), name="example2.zip", date=200000, size=2000
        )

        self.file_in_zip = File(
            path=Path("/archive/path"), name="inside.txt", date=150000, size=500
        )

        self.rule_name_start = {"conditions": {"start": "example"}}
        self.rule_name_end = {"conditions": {"end": ".txt"}}
        self.rule_name_contain = {"conditions": {"contain": "1"}}
        self.rule_name_regex = {"conditions": {"regex": "^exampl.*"}}
        self.rule_size_larger = {"conditions": {"larger": "500B"}}
        self.rule_size_smaller = {"conditions": {"smaller": "150001B"}}
        self.rule_age_older = {"conditions": {"older": "1d"}}
        self.rule_age_newer = {"conditions": {"newer": "3d"}}

    def tearDown(self):
        pass

    def test_match_name_start(self):
        matcher = FileMatcher([self.rule_name_start])
        matched_rule = matcher.match(self.file1)
        self.assertIsNotNone(matched_rule)
        self.assertEqual(matched_rule, self.rule_name_start)

    def test_match_name_end(self):
        matcher = FileMatcher([self.rule_name_end])
        matched_rule = matcher.match(self.file1)
        self.assertIsNotNone(matched_rule)
        self.assertEqual(matched_rule, self.rule_name_end)

    def test_match_name_contain(self):
        matcher = FileMatcher([self.rule_name_contain])
        matched_rule = matcher.match(self.file1)
        self.assertIsNotNone(matched_rule)
        self.assertEqual(matched_rule, self.rule_name_contain)

    def test_match_name_regex(self):
        matcher = FileMatcher([self.rule_name_regex])
        matched_rule = matcher.match(self.file2)
        self.assertIsNotNone(matched_rule)
        self.assertEqual(matched_rule, self.rule_name_regex)

    def test_match_size_larger(self):
        matcher = FileMatcher([self.rule_size_larger])
        matched_rule = matcher.match(self.file1)
        self.assertIsNotNone(matched_rule)
        self.assertEqual(matched_rule, self.rule_size_larger)

    def test_match_size_smaller(self):
        matcher = FileMatcher([self.rule_size_smaller])
        matched_rule = matcher.match(self.file1)
        self.assertIsNotNone(matched_rule)
        self.assertEqual(matched_rule, self.rule_size_smaller)

    def test_match_age_older(self):
        matcher = FileMatcher([self.rule_age_older])
        matched_rule = matcher.match(self.file1)
        self.assertIsNotNone(matched_rule)
        self.assertEqual(matched_rule, self.rule_age_older)

    def test_match_age_newer(self):
        matcher = FileMatcher([self.rule_age_newer])
        matched_rule = matcher.match(self.file1)
        self.assertIsNotNone(matched_rule)
        self.assertEqual(matched_rule, self.rule_age_newer)

    def test_no_match(self):
        matcher = FileMatcher([{"conditions": {"start": "non_existing"}}])
        matched_rule = matcher.match(self.file1)
        self.assertIsNone(matched_rule)

    def test_archive_match(self):
        with patch("unclutter_directory.FileMatcher.ZipArchive") as mock_zip_archive:
            mock_archive_manager = MagicMock(spec=CompressedArchive)
            mock_archive_manager.get_files.return_value = [self.file_in_zip]
            mock_zip_archive.return_value = mock_archive_manager

            rule_check_archive = {
                "conditions": {"start": "inside"},
                "check_archive": True,
            }
            matcher = FileMatcher([rule_check_archive])
            matched_rule = matcher.match(self.file2)
            self.assertIsNotNone(matched_rule)
            self.assertEqual(matched_rule, rule_check_archive)

    def test_match_name_start_case_insensitive(self):
        matcher = FileMatcher([self.rule_name_start])
        self.file1.name = "EXAMPLE1.TXT"  
        matched_rule = matcher.match(self.file1)
        self.assertIsNotNone(matched_rule)
        self.assertEqual(matched_rule, self.rule_name_start)

    def test_match_name_end_case_insensitive(self):
        matcher = FileMatcher([self.rule_name_end])
        self.file1.name = "EXAMPLE2.TXT"  # Cambiando el nombre a mayúsculas
        matched_rule = matcher.match(self.file1)
        self.assertIsNotNone(matched_rule)
        self.assertEqual(matched_rule, self.rule_name_end)

    def test_match_name_contain_case_insensitive(self):
        matcher = FileMatcher([self.rule_name_contain])
        self.file1.name = "Example1.txt"  # Cambiando el nombre a mayúsculas
        matched_rule = matcher.match(self.file1)
        self.assertIsNotNone(matched_rule)
        self.assertEqual(matched_rule, self.rule_name_contain)

    def test_match_name_regex_case_insensitive(self):
        matcher = FileMatcher([self.rule_name_regex])
        self.file2.name = "EXAMPL2.ZIP"  # Cambiando el nombre a mayúsculas
        matched_rule = matcher.match(self.file2)
        self.assertIsNotNone(matched_rule)
        self.assertEqual(matched_rule, self.rule_name_regex)

    def test_match_name_start_case_sensitive(self):
        self.file1.name = "EXAMPLE1.TXT"  
        matcher = FileMatcher([{"conditions": {"start": "example"}, "case_sensitive": True}])
        matched_rule = matcher.match(self.file1)
        self.assertIsNone(matched_rule)

    def test_match_name_end_case_sensitive(self):
        matcher = FileMatcher([{"conditions": {"end": ".txt"}, "case_sensitive": True}])
        self.file1.name = "EXAMPLE1.TXT"  
        matched_rule = matcher.match(self.file1)
        self.assertIsNone(matched_rule)  

    def test_match_name_contain_case_sensitive(self):
        matcher = FileMatcher([{"conditions": {"contain": "xample1"}, "case_sensitive": True}])
        self.file1.name = "EXAMPLE1.TXT"  
        matched_rule = matcher.match(self.file1)
        self.assertIsNone(matched_rule)  # No debería coincidir con "Example1.txt"

    def test_match_name_regex_case_sensitive(self):
        matcher = FileMatcher([{"conditions": {"regex": "^exampl.*"}, "case_sensitive": True}])
        self.file1.name = "EXAMPLE1.TXT"  
        matched_rule = matcher.match(self.file1)
        self.assertIsNone(matched_rule) 

if __name__ == "__main__":
    unittest.main()
