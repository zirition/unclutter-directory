import unittest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch

# Import the class to be tested
from unclutter_directory.ActionExecutor import ActionExecutor

class TestActionExecutor(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_path = Path(self.temp_dir) / "test_file.txt"
        self.file_path.touch()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('os.makedirs')
    @patch.object(Path, 'rename')
    def test_move_action(self, rename_patch, make_dirs_patch):
        action = {"type": "move", "target": self.temp_dir}

        rename_patch.return_value = None
        make_dirs_patch.return_value = None

        executor = ActionExecutor(action)
        executor.execute_action(self.file_path, self.temp_dir)
        moved_file = Path(self.temp_dir) / "test_file_1.txt" # The _1 is needed because the file already exists

        make_dirs_patch.assert_called_once_with(Path(self.temp_dir), exist_ok=True)
        rename_patch.assert_called_once_with(moved_file)

    def test_delete_action(self):
        action = {"type": "delete"}
        executor = ActionExecutor(action)
        executor.execute_action(self.file_path, self.temp_dir)
        self.assertFalse(self.file_path.exists())

    def test_compress_action(self):
        action = {"type": "compress", "target": self.temp_dir}
        executor = ActionExecutor(action)
        executor.execute_action(self.file_path, self.temp_dir)
        compressed_file = Path(self.temp_dir) / "test_file.zip"
        self.assertTrue(compressed_file.exists())

    def test_compress_forbidden_extension(self):
        forbidden_file = Path(self.temp_dir) / "test_file.zip"
        forbidden_file.touch()
        action = {"type": "compress", "target": self.temp_dir}
        executor = ActionExecutor(action)
        with self.assertLogs(level='INFO') as log:
            executor.execute_action(forbidden_file, self.temp_dir)
            self.assertIn("Skipping compression for file with forbidden extension", log.output[0])

if __name__ == "__main__":
    unittest.main()
