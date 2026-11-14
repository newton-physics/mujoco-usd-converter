# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0


import usd_validation_nvidia
import usdex.core
import usdex.test
from pxr import UsdGeom


class ConverterTestCase(usdex.test.TestCase):

    defaultUpAxis = UsdGeom.Tokens.z  # noqa: N815

    def setUp(self):
        super().setUp()
        # All conversion results should be valid atomic assets
        self.validationEngine.enable_rule(usd_validation_nvidia.AnchoredAssetPathsChecker)
        self.validationEngine.enable_rule(usd_validation_nvidia.SupportedFileTypesChecker)
