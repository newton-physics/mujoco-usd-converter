# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import typing

import omni.asset_validator
import usdex.core
import usdex.test
from pxr import Gf, UsdGeom


class ConverterTestCase(usdex.test.TestCase):

    defaultUpAxis = UsdGeom.Tokens.z  # noqa: N815

    defaultValidationIssuePredicates: typing.ClassVar[list[omni.asset_validator.IssuePredicates]] = [  # noqa: N815
        # MuJoCo USD Converter uses nested bodies, as it more faithfully matches the kinematic tree in MuJoCo.
        # There is an open proposal (https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/82) to adopt this change to the
        # UsdPhysics specification.
        #
        # Once adopted, the asset validator should be updated to support nested bodies within articulations. For now, we just ignore the issues.
        omni.asset_validator.IssuePredicates.ContainsMessage("Enabled rigid body is missing xformstack reset, when a child of a rigid body"),
        omni.asset_validator.IssuePredicates.ContainsMessage("ArticulationRootAPI definition on a kinematic rigid body is not allowed"),
    ]

    def assert_rotation_almost_equal(self, rot1: Gf.Rotation | Gf.Quatf | Gf.Quatd, rot2: Gf.Rotation | Gf.Quatf | Gf.Quatd, tolerance: float = 1e-6):
        """Assert two rotations are almost equal (same concrete type required).
        Strict: Rotations must be the same class (Rotation vs Quatf vs Quatd). Antipodal quaternions
        are treated as different.
        """
        # Enforce identical concrete type without direct type comparison triggering E721.
        if not (isinstance(rot1, type(rot2)) and isinstance(rot2, type(rot1))):
            self.fail(f"Rotation types do not match or are unsupported: {type(rot1)} vs {type(rot2)}")

        if isinstance(rot1, Gf.Rotation):
            self.assertTrue(
                Gf.IsClose(rot1.GetAxis(), rot2.GetAxis(), tolerance),
                f"Axis mismatch: {rot1.GetAxis()} != {rot2.GetAxis()}",
            )
            self.assertTrue(
                Gf.IsClose(rot1.GetAngle(), rot2.GetAngle(), tolerance),
                f"Angle mismatch: {rot1.GetAngle()} != {rot2.GetAngle()}",
            )
        else:  # Quatf or Quatd (same concrete type guaranteed)
            self.assertTrue(
                Gf.IsClose(rot1.GetReal(), rot2.GetReal(), tolerance),
                f"Real part mismatch: {rot1.GetReal()} != {rot2.GetReal()}",
            )
            self.assertTrue(
                Gf.IsClose(rot1.GetImaginary(), rot2.GetImaginary(), tolerance),
                f"Imaginary part mismatch: {rot1.GetImaginary()} != {rot2.GetImaginary()}",
            )

    def setUp(self):
        super().setUp()
        # All conversion results should be valid atomic assets
        self.validationEngine.enable_rule(omni.asset_validator.AnchoredAssetPathsChecker)
        self.validationEngine.enable_rule(omni.asset_validator.SupportedFileTypesChecker)
