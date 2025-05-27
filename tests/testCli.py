# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import unittest
from unittest.mock import patch

from mjc_usd_converter.__main__ import cli_main


class TestCli(unittest.TestCase):
    @patch("builtins.print")
    def test_cli_main(self, mock_print):
        cli_main()

        # Verify that print was called 4 times (header + 3 version prints)
        self.assertEqual(mock_print.call_count, 4)

        # Verify the first print was the header
        mock_print.assert_any_call("Running mjc_usd_converter")
