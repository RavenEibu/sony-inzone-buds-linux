#!/usr/bin/env python3
"""Tests for tools/inzone-hid-capture; no hardware required.

Loaded by path since the tool has no .py extension (it is invoked directly).
"""

from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
import subprocess
import sys
import unittest

PROJECT_DIR = Path(__file__).resolve().parents[1]
TOOL_PATH = PROJECT_DIR / "tools/inzone-hid-capture"

# The tool has no .py extension (it is invoked directly), so the loader must
# be given explicitly instead of inferred from the suffix.
_loader = SourceFileLoader("inzone_hid_capture", str(TOOL_PATH))
spec = importlib.util.spec_from_file_location("inzone_hid_capture", TOOL_PATH, loader=_loader)
capture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture_module)


class FormatReportTests(unittest.TestCase):
    def test_formats_report_id_length_and_hex_bytes(self):
        line = capture_module.format_report(bytes([176, 0x01, 0x02, 0xFF]))
        self.assertEqual(line, "id=176  len=  4  b0 01 02 ff")

    def test_single_byte_report(self):
        line = capture_module.format_report(bytes([12]))
        self.assertEqual(line, "id= 12  len=  1  0c")


class FindHidrawDeviceTests(unittest.TestCase):
    def _make_hidraw_tree(self, directory: Path, modalias_fragment: str) -> None:
        hidraw_class = directory / "hidraw"
        node = hidraw_class / "hidraw3"
        node.mkdir(parents=True)
        # The real sysfs "device" symlink resolves into a path that embeds the
        # HID modalias, e.g. .../0003:054C:0EC2.0007. Reproduce that shape.
        real_device_dir = directory / f"real-device/{modalias_fragment}"
        real_device_dir.mkdir(parents=True)
        (node / "device").symlink_to(real_device_dir)

    def test_finds_matching_device_case_insensitively(self):
        with TemporaryDirectoryPath() as directory:
            self._make_hidraw_tree(directory, "0003:054c:0ec2.0007")
            original = capture_module.HIDRAW_CLASS
            capture_module.HIDRAW_CLASS = directory / "hidraw"
            try:
                found = capture_module.find_hidraw_device()
            finally:
                capture_module.HIDRAW_CLASS = original
            self.assertEqual(found, Path("/dev/hidraw3"))

    def test_returns_none_when_no_device_matches(self):
        with TemporaryDirectoryPath() as directory:
            self._make_hidraw_tree(directory, "0003:054C:0EC3.0007")  # MOBILE mode
            original = capture_module.HIDRAW_CLASS
            capture_module.HIDRAW_CLASS = directory / "hidraw"
            try:
                found = capture_module.find_hidraw_device()
            finally:
                capture_module.HIDRAW_CLASS = original
            self.assertIsNone(found)

    def test_returns_none_when_class_directory_is_absent(self):
        original = capture_module.HIDRAW_CLASS
        capture_module.HIDRAW_CLASS = Path("/nonexistent/hidraw")
        try:
            self.assertIsNone(capture_module.find_hidraw_device())
        finally:
            capture_module.HIDRAW_CLASS = original


class TemporaryDirectoryPath:
    """tempfile.TemporaryDirectory, but __enter__ returns a Path."""

    def __init__(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()

    def __enter__(self) -> Path:
        return Path(self._tmp.__enter__())

    def __exit__(self, *exc_info):
        return self._tmp.__exit__(*exc_info)


class CommandLineTests(unittest.TestCase):
    def test_missing_device_reports_error_and_exits_nonzero(self):
        result = subprocess.run(
            [sys.executable, str(TOOL_PATH), "--device", "/nonexistent/hidraw-device"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("not readable", result.stderr)

    def test_never_imports_a_write_capable_ioctl_helper(self):
        # Guard against a future edit accidentally adding write capability.
        source = TOOL_PATH.read_text(encoding="utf-8")
        self.assertNotIn("os.write(", source)
        self.assertNotIn("fcntl.ioctl(", source)
        self.assertNotIn("O_RDWR", source)
        self.assertNotIn("O_WRONLY", source)


if __name__ == "__main__":
    unittest.main()
