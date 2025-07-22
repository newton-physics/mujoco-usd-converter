# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import unittest

import mujoco
import numpy as np
from pxr import Gf, Sdf, Usd, UsdPhysics

import mujoco_usd_converter


class TestBodies(unittest.TestCase):
    def setUp(self):
        model = pathlib.Path("./tests/data/bodies.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        self.stage: Usd.Stage = Usd.Stage.Open(asset.path)

    def tearDown(self):
        if pathlib.Path("tests/output").exists():
            shutil.rmtree("tests/output")

    def test_bodies(self):
        # Root body is an Articulation Root
        prim = self.stage.GetPrimAtPath("/bodies/Geometry/root_body")
        self.assertTrue(prim.HasAPI(UsdPhysics.ArticulationRootAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.RigidBodyAPI))

        # Nested Body is not an articulation root
        prim = self.stage.GetPrimAtPath("/bodies/Geometry/root_body/nested_body")
        self.assertFalse(prim.HasAPI(UsdPhysics.ArticulationRootAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.RigidBodyAPI))

    def test_kinematic_body(self):
        # mocap body is kinematic
        prim = self.stage.GetPrimAtPath("/bodies/Geometry/kinematic_body")
        body = UsdPhysics.RigidBodyAPI(prim)
        self.assertTrue(body.GetKinematicEnabledAttr().Get())

        # Child body inherits the kinematic flag
        prim = self.stage.GetPrimAtPath("/bodies/Geometry/kinematic_body/kinematic_child")
        body = UsdPhysics.RigidBodyAPI(prim)
        self.assertTrue(body.GetKinematicEnabledAttr().Get())

    def test_explicit_inertia_principal_axes(self):
        principal_prim = self.stage.GetPrimAtPath("/bodies/Geometry/explicit_inertia_principal")
        self.assertTrue(principal_prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(principal_prim)
        self.assertAlmostEqual(mass_api.GetMassAttr().Get(), 2.0)
        self.assertEqual(mass_api.GetCenterOfMassAttr().Get(), Gf.Vec3f(0.1, 0.2, 0.3))
        self.assertEqual(mass_api.GetPrincipalAxesAttr().Get(), Gf.Quatf(0.92388, 0, 0.38268, 0))
        self.assertEqual(mass_api.GetDiagonalInertiaAttr().Get(), Gf.Vec3f(0.2, 0.1, 0.3))

    def test_explicit_inertia_full_matrix(self):
        full_prim = self.stage.GetPrimAtPath("/bodies/Geometry/explicit_inertia_full")
        self.assertTrue(full_prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(full_prim)
        self.assertAlmostEqual(mass_api.GetMassAttr().Get(), 3.0)
        self.assertEqual(mass_api.GetCenterOfMassAttr().Get(), Gf.Vec3f(0.1, 0.2, 0.3))
        self.assertTrue(mass_api.GetPrincipalAxesAttr().IsDefined())
        self.assertTrue(mass_api.GetDiagonalInertiaAttr().IsDefined())

        mat = np.array(
            [
                [0.4, 0.05, 0.02],
                [0.05, 0.3, 0.01],
                [0.02, 0.01, 0.2],
            ]
        )
        # mju_eig3 expects flattened column-major matrix
        flat_mat = mat.flatten("F")

        eigval = np.zeros(3)
        eigvec = np.zeros(9)
        quat = np.zeros(4)

        # Call mju_eig3 to get eigenvalues
        mujoco.mju_eig3(eigval, eigvec, quat, flat_mat)

        expected_diag_inertia = Gf.Vec3f(*eigval)
        actual_diag_inertia = mass_api.GetDiagonalInertiaAttr().Get()
        self.assertTrue(Gf.IsClose(actual_diag_inertia, expected_diag_inertia, 1e-5))

        expected_principal_axes = Gf.Quatf(float(quat[0]), Gf.Vec3f(float(quat[1]), float(quat[2]), float(quat[3])))
        actual_principal_axes = mass_api.GetPrincipalAxesAttr().Get()
        self.assertEqual(actual_principal_axes, expected_principal_axes)

    def test_regular_body(self):
        regular_prim: Usd.Prim = self.stage.GetPrimAtPath("/bodies/Geometry/regular_dynamic")
        self.assertTrue(regular_prim.HasAPI(UsdPhysics.RigidBodyAPI))
        self.assertFalse(regular_prim.HasAPI(UsdPhysics.MassAPI))
        self.assertFalse(regular_prim.HasAttribute("mjc:body:gravcomp"))

    def test_gravity_compensated(self):
        gravcomp_prim: Usd.Prim = self.stage.GetPrimAtPath("/bodies/Geometry/gravity_compensated")
        self.assertTrue(gravcomp_prim.HasAPI(UsdPhysics.RigidBodyAPI))
        self.assertAlmostEqual(gravcomp_prim.GetAttribute("mjc:body:gravcomp").Get(), 0.2)
