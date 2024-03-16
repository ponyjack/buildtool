#!/usr/bin/env vpython3
# Copyright (c) 2024 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Unit tests for presubmit_diff.py."""

import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gclient_utils
import presubmit_diff


class PresubmitDiffTest(unittest.TestCase):

    def setUp(self):
        # State of the local directory.
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "nested"))
        with open(os.path.join(self.root, "unchanged.txt"), "w") as f:
            f.write("unchanged\n")
        with open(os.path.join(self.root, "added.txt"), "w") as f:
            f.write("added\n")
        with open(os.path.join(self.root, "modified.txt"), "w") as f:
            f.write("modified... foo\n")
        with open(os.path.join(self.root, "nested/modified.txt"), "w") as f:
            f.write("goodbye\n")

        # State of the remote repository.
        fetch_data = {
            "unchanged.txt": "unchanged\n",
            "deleted.txt": "deleted\n",
            "modified.txt": "modified... bar\n",
            "nested/modified.txt": "hello\n",
        }

        def fetch_side_effect(host, repo, ref, file):
            return fetch_data.get(file, "")

        fetch_content_mock = mock.patch("presubmit_diff.fetch_content",
                                        side_effect=fetch_side_effect)
        fetch_content_mock.start()

        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        gclient_utils.rmtree(self.root)

    def _test_create_diffs(self, files: list[str], expected: dict[str, str]):
        actual = presubmit_diff.create_diffs("host", "repo", "ref", self.root,
                                             files)
        self.assertEqual(actual.keys(), expected.keys())

        # Manually check each line in the diffs except the "index" line because
        # hashes can differ in length.
        for file, diff in actual.items():
            expected_lines = expected[file].splitlines()
            for idx, line in enumerate(diff.splitlines()):
                if line.startswith("index "):
                    continue
                self.assertEqual(line, expected_lines[idx])

    def test_create_diffs_with_nonexistent_file_raises_error(self):
        self.assertRaises(
            RuntimeError,
            presubmit_diff.create_diffs,
            "host",
            "repo",
            "ref",
            self.root,
            ["doesnotexist.txt"],
        )

    def test_create_diffs_with_unchanged_file(self):
        self._test_create_diffs(
            ["unchanged.txt"],
            {"unchanged.txt": ""},
        )

    def test_create_diffs_with_added_file(self):
        expected_diff = """diff --git a/added.txt b/added.txt
new file mode 100644
index 00000000..d5f7fc3f
--- /dev/null
+++ b/added.txt
@@ -0,0 +1 @@
+added
"""
        self._test_create_diffs(
            ["added.txt"],
            {"added.txt": expected_diff},
        )

    def test_create_diffs_with_deleted_file(self):
        expected_diff = """diff --git a/deleted.txt b/deleted.txt
deleted file mode 100644
index 71779d2c..00000000
--- a/deleted.txt
+++ /dev/null
@@ -1 +0,0 @@
-deleted
"""
        self._test_create_diffs(
            ["deleted.txt"],
            {"deleted.txt": expected_diff},
        )

    # pylint: disable=line-too-long

    def test_create_diffs_with_modified_files(self):
        expected_diff = """diff --git a/modified.txt b/modified.txt
index a7dd0b00..12d68703 100644
--- a/modified.txt
+++ b/modified.txt
@@ -1 +1 @@
-modified... bar
+modified... foo
"""
        expected_nested_diff = """diff --git a/nested/modified.txt b/nested/modified.txt
index ce013625..dd7e1c6f 100644
--- a/nested/modified.txt
+++ b/nested/modified.txt
@@ -1 +1 @@
-hello
+goodbye
"""
        self._test_create_diffs(
            ["modified.txt", "nested/modified.txt"],
            {
                "modified.txt": expected_diff,
                "nested/modified.txt": expected_nested_diff,
            },
        )

    # Test cases for _process_diff.
    def test_process_diff_with_no_changes(self):
        self.assertEqual(
            presubmit_diff._process_diff(
                "",
                "/path/to/src",
                "/path/to/dst",
            ),
            "",
        )

    @mock.patch("platform.system", return_value="Linux")
    @mock.patch("os.sep", new="/")
    def test_process_diff_handles_unix_paths(self, sys_mock):
        diff = """diff --git a/path/to/src/file.txt b/path/to/dst/file.txt
index ce013625..dd7e1c6f 100644
--- a/path/to/file.txt
+++ b/path/to/file.txt
@@ -1 +1 @@
-random
+content
"""
        expected = """diff --git a/file.txt b/file.txt
index ce013625..dd7e1c6f 100644
--- a/path/to/file.txt
+++ b/path/to/file.txt
@@ -1 +1 @@
-random
+content
"""
        self.assertEqual(
            presubmit_diff._process_diff(
                diff,
                "/path/to/src",
                "/path/to/dst",
            ),
            expected,
        )

        # Trailing slashes are handled.
        self.assertEqual(
            presubmit_diff._process_diff(
                diff,
                "/path/to/src/",
                "/path/to/dst/",
            ),
            expected,
        )

    @mock.patch("platform.system", return_value="Windows")
    @mock.patch("os.sep", new="\\")
    def test_process_diff_handles_windows_paths(self, sys_mock):
        diff = """diff --git "a/C:\\\\path\\\\to\\\\src\\\\file.txt" "b/C:\\\\path\\\\to\\\\dst\\\\file.txt"
index ce013625..dd7e1c6f 100644
--- "a/C:\\\\path\\\\to\\\\src\\\\file.txt
+++ "b/C:\\\\path\\\\to\\\\dst\\\\file.txt"
@@ -1 +1 @@
-random
+content
"""
        expected = """diff --git a/file.txt b/file.txt
index ce013625..dd7e1c6f 100644
--- a/file.txt
+++ b/file.txt
@@ -1 +1 @@
-random
+content
"""
        self.assertEqual(
            expected,
            presubmit_diff._process_diff(diff, "C:\\path\\to\\src",
                                         "C:\\path\\to\\dst"),
        )

        # Trailing slashes are handled.
        self.assertEqual(
            expected,
            presubmit_diff._process_diff(diff, "C:\\path\\to\\src\\",
                                         "C:\\path\\to\\dst\\"),
        )


if __name__ == "__main__":
    unittest.main()
