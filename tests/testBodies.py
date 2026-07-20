# SPDX-FileCopyrightText: Copyright (c) 2025-2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib

import mujoco
import numpy as np
import usdex.core
import usdex.test
from pxr import Gf, Sdf, Tf, Usd, UsdGeom, UsdPhysics

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestBodies(ConverterTestCase):
    def setUp(self):
        super().setUp()
        model = pathlib.Path("./tests/data/bodies.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        self.stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(self.stage)

    def test_articulation_roots(self):
        # Root body is an Articulation Root
        prim = self.stage.GetPrimAtPath("/bodies/Geometry/root_body")
        self.assertTrue(prim.HasAPI(UsdPhysics.ArticulationRootAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.RigidBodyAPI))

        # Nested Body is not an articulation root
        prim = self.stage.GetPrimAtPath("/bodies/Geometry/root_body/nested_body")
        self.assertFalse(prim.HasAPI(UsdPhysics.ArticulationRootAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.RigidBodyAPI))

        # Kinematic Body is also an articulation root as there is an implicit fixed joint to the child body
        prim = self.stage.GetPrimAtPath("/bodies/Geometry/kinematic_body")
        self.assertTrue(prim.HasAPI(UsdPhysics.ArticulationRootAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.RigidBodyAPI))

        # Static Base is an articulation root as it has a descendant body with a non-free joint
        prim = self.stage.GetPrimAtPath("/bodies/Geometry/static_base")
        self.assertTrue(prim.HasAPI(UsdPhysics.ArticulationRootAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.RigidBodyAPI))

        # regular_dynamic is not an articulation as it has no child bodies
        prim = self.stage.GetPrimAtPath("/bodies/Geometry/regular_dynamic")
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
        self.assertFalse(principal_prim.HasAPI("NewtonMassAPI"))
        mass_api = UsdPhysics.MassAPI(principal_prim)
        self.assertAlmostEqual(mass_api.GetMassAttr().Get(), 2.0)
        self.assertEqual(mass_api.GetCenterOfMassAttr().Get(), Gf.Vec3f(0.1, 0.2, 0.3))
        self.assertRotationsAlmostEqual(mass_api.GetPrincipalAxesAttr().Get(), Gf.Quatf(0.92388, 0, 0.38268, 0))
        self.assertEqual(mass_api.GetDiagonalInertiaAttr().Get(), Gf.Vec3f(0.2, 0.1, 0.3))

    def test_explicit_non_unit_inertia_principal_axes(self):
        principal_prim = self.stage.GetPrimAtPath("/bodies/Geometry/explicit_non_unit_inertia_principal")
        self.assertTrue(principal_prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(principal_prim)
        self.assertAlmostEqual(mass_api.GetMassAttr().Get(), 2.0)
        self.assertEqual(mass_api.GetCenterOfMassAttr().Get(), Gf.Vec3f(0.1, 0.2, 0.3))
        self.assertRotationsAlmostEqual(mass_api.GetPrincipalAxesAttr().Get(), Gf.Quatf(0.98643655, 0.16414304, 0, 0))
        self.assertEqual(mass_api.GetDiagonalInertiaAttr().Get(), Gf.Vec3f(0.2, 0.1, 0.3))

    def test_explicit_inertia_full_matrix(self):
        full_prim = self.stage.GetPrimAtPath("/bodies/Geometry/explicit_inertia_full")
        self.assertTrue(full_prim.HasAPI(UsdPhysics.MassAPI))
        self.assertTrue(full_prim.HasAPI("NewtonMassAPI"))
        newton_inertia = full_prim.GetAttribute("newton:inertia").Get()
        self.assertTrue(newton_inertia is not None)
        expected = [0.4, 0.3, 0.2, 0.05, 0.02, 0.01]
        for actual, exp in zip(newton_inertia, expected):
            self.assertAlmostEqual(actual, exp, places=6)
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
        self.assertRotationsAlmostEqual(actual_principal_axes, expected_principal_axes)

    def test_regular_body(self):
        regular_prim: Usd.Prim = self.stage.GetPrimAtPath("/bodies/Geometry/regular_dynamic")
        self.assertTrue(regular_prim.HasAPI(UsdPhysics.RigidBodyAPI))
        self.assertFalse(regular_prim.HasAPI(UsdPhysics.MassAPI))
        self.assertFalse(regular_prim.HasAPI("NewtonMassAPI"))
        self.assertFalse(regular_prim.HasAttribute("mjc:body:gravcomp"))

    def test_gravity_compensated(self):
        gravcomp_prim: Usd.Prim = self.stage.GetPrimAtPath("/bodies/Geometry/gravity_compensated")
        self.assertTrue(gravcomp_prim.HasAPI(UsdPhysics.RigidBodyAPI))
        self.assertAlmostEqual(gravcomp_prim.GetAttribute("mjc:body:gravcomp").Get(), 0.2)

    def test_zero_inertia(self):
        zero_inertia_prim: Usd.Prim = self.stage.GetPrimAtPath("/bodies/Geometry/zero_inertia")
        self.assertTrue(zero_inertia_prim.HasAPI(UsdPhysics.RigidBodyAPI))
        self.assertTrue(zero_inertia_prim.HasAPI(UsdPhysics.MassAPI))
        self.assertFalse(zero_inertia_prim.HasAPI("NewtonMassAPI"))
        mass_api = UsdPhysics.MassAPI(zero_inertia_prim)
        self.assertAlmostEqual(mass_api.GetMassAttr().Get(), 2.0)
        self.assertEqual(mass_api.GetCenterOfMassAttr().Get(), Gf.Vec3f(0.1, 0.2, 0.3))
        self.assertFalse(mass_api.GetPrincipalAxesAttr().HasAuthoredValue())
        self.assertFalse(mass_api.GetDiagonalInertiaAttr().HasAuthoredValue())


class TestInferredInertia(ConverterTestCase):
    """Bodies without an explicit inertial, whose mass properties are inferred from geoms

    When several geoms contribute mass, the compiled body-level mass properties are
    authored so downstream readers reproduce MuJoCo's inferred inertial unambiguously.
    Single-geom bodies rely on the geom-level mass properties alone.
    """

    def setUp(self):
        super().setUp()
        self.model = pathlib.Path("./tests/data/inferred_inertia.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(self.model, self.tmpDir())
        self.stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(self.stage)
        self.mj_model: mujoco.MjModel = mujoco.MjModel.from_xml_path(str(self.model))

    def assertBodyMassMatchesModel(self, prim: Usd.Prim, body_id: int):  # noqa: N802
        self.assertTrue(prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(prim)
        self.assertAlmostEqual(mass_api.GetMassAttr().Get(), self.mj_model.body_mass[body_id], places=5)
        expected_com = Gf.Vec3f(*self.mj_model.body_ipos[body_id])
        self.assertTrue(Gf.IsClose(mass_api.GetCenterOfMassAttr().Get(), expected_com, 1e-5))
        expected_inertia = Gf.Vec3f(*self.mj_model.body_inertia[body_id])
        self.assertTrue(Gf.IsClose(mass_api.GetDiagonalInertiaAttr().Get(), expected_inertia, 1e-5))
        quat = self.mj_model.body_iquat[body_id]
        expected_axes = Gf.Quatf(float(quat[0]), Gf.Vec3f(float(quat[1]), float(quat[2]), float(quat[3])))
        self.assertRotationsAlmostEqual(mass_api.GetPrincipalAxesAttr().Get(), expected_axes)

    def test_multi_geom_body(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/inferred_inertia/Geometry/multi_geom")
        self.assertTrue(prim.HasAPI(UsdPhysics.RigidBodyAPI))
        self.assertFalse(prim.HasAPI("NewtonMassAPI"))
        self.assertBodyMassMatchesModel(prim, self.mj_model.body("multi_geom").id)

    def test_single_geom_body(self):
        # the geom-level mass properties are authoritative, so no body-level MassAPI is authored
        prim: Usd.Prim = self.stage.GetPrimAtPath("/inferred_inertia/Geometry/single_geom")
        self.assertTrue(prim.HasAPI(UsdPhysics.RigidBodyAPI))
        self.assertFalse(prim.HasAPI(UsdPhysics.MassAPI))
        self.assertFalse(prim.HasAPI("NewtonMassAPI"))

    def test_unnamed_bodies(self):
        # unnamed bodies must convert successfully, including the compiled model
        # lookup for multi-geom bodies, which cannot be resolved by name
        prims = [x for x in self.stage.GetPrimAtPath("/inferred_inertia/Geometry").GetChildren() if x.GetName().startswith("Body")]
        self.assertEqual(len(prims), 2)

        spec = mujoco.MjSpec.from_file(str(self.model))
        spec.compile()
        unnamed_ids = [x.id for x in spec.worldbody.bodies if not x.name]
        self.assertEqual(len(unnamed_ids), 2)

        def gprim_count(prim: Usd.Prim) -> int:
            return len([x for x in prim.GetChildren() if x.IsA(UsdGeom.Gprim)])

        multi_geom_prim, single_geom_prim = prims
        if gprim_count(multi_geom_prim) == 1:
            multi_geom_prim, single_geom_prim = single_geom_prim, multi_geom_prim
        self.assertEqual(gprim_count(multi_geom_prim), 2)
        self.assertEqual(gprim_count(single_geom_prim), 1)

        self.assertTrue(multi_geom_prim.HasAPI(UsdPhysics.RigidBodyAPI))
        self.assertBodyMassMatchesModel(multi_geom_prim, unnamed_ids[0])

        self.assertTrue(single_geom_prim.HasAPI(UsdPhysics.RigidBodyAPI))
        self.assertFalse(single_geom_prim.HasAPI(UsdPhysics.MassAPI))

    def test_nested_unnamed_body(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/inferred_inertia/Geometry/multi_geom/Body")
        self.assertTrue(prim.HasAPI(UsdPhysics.RigidBodyAPI))
        spec = mujoco.MjSpec.from_file(str(self.model))
        spec.compile()
        nested_body = spec.worldbody.bodies[0].bodies[0]
        self.assertBodyMassMatchesModel(prim, nested_body.id)

    def test_massless_collider_body(self):
        # the massless density="0" collider authors no geom-level mass properties, so the
        # body-level inertial is required for downstream readers to reproduce the mass
        prim: Usd.Prim = self.stage.GetPrimAtPath("/inferred_inertia/Geometry/massless_collider")
        self.assertTrue(prim.HasAPI(UsdPhysics.RigidBodyAPI))
        self.assertBodyMassMatchesModel(prim, self.mj_model.body("massless_collider").id)
        self.assertAlmostEqual(UsdPhysics.MassAPI(prim).GetMassAttr().Get(), 0.5, places=6)


class TestCompilerOverrides(ConverterTestCase):
    """Compiler settings that mutate the spec during compilation must not affect conversion"""

    def test_fusestatic(self):
        # compiling a spec with fusestatic restructures the body tree, so no body-level
        # mass properties can be transferred, but the conversion itself must be unaffected
        model = pathlib.Path("./tests/data/fusestatic.xml")
        with usdex.test.ScopedDiagnosticChecker(
            self,
            [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Body-level mass properties will not be authored.*")],
            level=usdex.core.DiagnosticsLevel.eWarning,
        ):
            asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)
        self.assertTrue(stage.GetPrimAtPath("/fusestatic/Geometry/root/static_child"))
        for prim in stage.Traverse():
            if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                self.assertFalse(prim.HasAPI(UsdPhysics.MassAPI))

    def test_discardvisual(self):
        # compiling a spec with discardvisual removes visual geoms from the compiled spec;
        # the converted USD must keep them, while the body-level mass still matches MuJoCo
        model = pathlib.Path("./tests/data/discardvisual.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)
        self.assertTrue(stage.GetPrimAtPath("/discardvisual/Geometry/second/vis2"))
        mj_model = mujoco.MjModel.from_xml_path(str(model))
        for name in ("first", "second"):
            prim = stage.GetPrimAtPath(f"/discardvisual/Geometry/{name}")
            self.assertTrue(prim.HasAPI(UsdPhysics.MassAPI))
            mass_api = UsdPhysics.MassAPI(prim)
            self.assertAlmostEqual(mass_api.GetMassAttr().Get(), mj_model.body_mass[mj_model.body(name).id], places=5)
