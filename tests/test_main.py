import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Define App class mock
class AppMock:
    def __init__(self):
        self._video_path = MagicMock()
        self._srt_path = MagicMock()
        self._output_dir = MagicMock()

    def _pick_path(self, var, title, is_dir=False, filetypes=None):
        import filedialog_mock as filedialog
        if is_dir:
            path = filedialog.askdirectory(title=title)
        else:
            path = filedialog.askopenfilename(
                title=title,
                filetypes=filetypes,
                initialdir="/fake/dir",
            )
        if path:
            var.set(path)

    def _choose_video(self):
        self._pick_path(
            self._video_path,
            "选择视频文件",
            filetypes=[("视频文件", "*.mp4"), ("所有文件", "*.*")],
        )

    def _choose_srt(self):
        self._pick_path(
            self._srt_path,
            "选择字幕文件",
            filetypes=[("字幕文件", "*.srt"), ("所有文件", "*.*")],
        )

    def _choose_output(self):
        self._pick_path(self._output_dir, "选择输出目录", is_dir=True)

# Mock modules for the real import if needed, but here we just test the logic
sys.modules['filedialog_mock'] = MagicMock()

class TestAppRefactor(unittest.TestCase):
    def setUp(self):
        self.app = AppMock()

    @patch('filedialog_mock.askopenfilename')
    def test_pick_path_file(self, mock_askopenfilename):
        mock_askopenfilename.return_value = "/path/to/file.mp4"
        var = MagicMock()

        self.app._pick_path(var, "Title", is_dir=False, filetypes=[("Test", "*.test")])

        mock_askopenfilename.assert_called_once_with(
            title="Title",
            filetypes=[("Test", "*.test")],
            initialdir="/fake/dir"
        )
        var.set.assert_called_once_with("/path/to/file.mp4")

    @patch('filedialog_mock.askdirectory')
    def test_pick_path_dir(self, mock_askdirectory):
        mock_askdirectory.return_value = "/path/to/dir"
        var = MagicMock()

        self.app._pick_path(var, "Title", is_dir=True)

        mock_askdirectory.assert_called_once_with(title="Title")
        var.set.assert_called_once_with("/path/to/dir")

    def test_choose_video(self):
        with patch.object(AppMock, '_pick_path') as mock_pick_path:
            self.app._choose_video()
            mock_pick_path.assert_called_once_with(
                self.app._video_path,
                "选择视频文件",
                filetypes=[("视频文件", "*.mp4"), ("所有文件", "*.*")]
            )

    def test_choose_srt(self):
        with patch.object(AppMock, '_pick_path') as mock_pick_path:
            self.app._choose_srt()
            mock_pick_path.assert_called_once_with(
                self.app._srt_path,
                "选择字幕文件",
                filetypes=[("字幕文件", "*.srt"), ("所有文件", "*.*")]
            )

    def test_choose_output(self):
        with patch.object(AppMock, '_pick_path') as mock_pick_path:
            self.app._choose_output()
            mock_pick_path.assert_called_once_with(
                self.app._output_dir,
                "选择输出目录",
                is_dir=True
            )

if __name__ == '__main__':
    unittest.main()
