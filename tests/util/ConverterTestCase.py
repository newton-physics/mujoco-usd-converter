# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import math

import usd_validation_nvidia
import usdex.core
import usdex.test
from pxr import Gf, UsdGeom


class ConverterTestCase(usdex.test.TestCase):

    defaultUpAxis = UsdGeom.Tokens.z  # noqa: N815

    def setUp(self):
        super().setUp()
        # All conversion results should be valid atomic assets
        self.validationEngine.enable_rule(usd_validation_nvidia.AnchoredAssetPathsChecker)
        self.validationEngine.enable_rule(usd_validation_nvidia.SupportedFileTypesChecker)

    def assertRotationsEquivalent(  # noqa: N802
        self, rot1: Gf.Rotation | Gf.Quatf | Gf.Quatd, rot2: Gf.Rotation | Gf.Quatf | Gf.Quatd, tolerance: float = 1e-5
    ):
        """Assert that two rotations differ by at most `tolerance` degrees, regardless of quaternion sign or axis-angle form."""
        first = Gf.Quatd(rot1.GetQuat() if isinstance(rot1, Gf.Rotation) else rot1).GetNormalized()
        second = Gf.Quatd(rot2.GetQuat() if isinstance(rot2, Gf.Rotation) else rot2).GetNormalized()
        difference = first * second.GetInverse()
        error = math.degrees(2 * math.atan2(difference.GetImaginary().GetLength(), abs(difference.GetReal())))
        self.assertLessEqual(error, tolerance, f"Rotation error of {error} degrees exceeds {tolerance}")
