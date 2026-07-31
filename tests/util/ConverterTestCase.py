# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0


import mujoco
import omni.asset_validator
import usdex.core
import usdex.test
from pxr import UsdGeom


class ConverterTestCase(usdex.test.TestCase):

    defaultUpAxis = UsdGeom.Tokens.z  # noqa: N815

    def setUp(self):
        super().setUp()
        # All conversion results should be valid atomic assets
        self.validationEngine.enable_rule(omni.asset_validator.AnchoredAssetPathsChecker)
        self.validationEngine.enable_rule(omni.asset_validator.SupportedFileTypesChecker)

    def limitForceScale(self, model: str, joint_name: str) -> float:  # noqa: N802
        """Compute the factor between a joint's normalized and effort-space limit gains.

        Mirrors `joint.get_limit_force_scale` from the compiled model so tests can state
        an expectation in the normalized units the MJCF authors, rather than restating
        the inertia-dependent product as a literal.
        """
        compiled = mujoco.MjSpec.from_file(str(model)).compile()
        joint_id = mujoco.mj_name2id(compiled, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        invweight = float(compiled.dof_invweight0[compiled.jnt_dofadr[joint_id]])
        dmax = float(compiled.jnt_solimp[joint_id][1])
        return invweight * (1.0 - dmax) if invweight > 0.0 and dmax < 1.0 else 1.0
