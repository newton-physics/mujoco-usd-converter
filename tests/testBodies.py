# SPDX-FileCopyrightText: Copyright (c) 2025-2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib

import mujoco
import numpy as np
import usdex.core
import usdex.test
from pxr import Gf, Sdf, Tf, Usd, UsdGeom, UsdPhysics

import mujoco_usd_converter
from mujoco_usd_converter._impl.body import bake_body_mass, get_model_body_id
from mujoco_usd_converter._impl.data import ConversionData
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

    def test_mass_baked_when_a_visual_provides_it(self):
        """A body whose mass depends on a non-colliding geom carries explicit mass properties.

        MuJoCo infers body mass from every geom in ``inertiagrouprange``, including geoms that
        collide with nothing. USD accumulates mass only from enabled colliders, so that
        contribution would be lost; the compiled values are authored on the body instead.
        """
        prim: Usd.Prim = self.stage.GetPrimAtPath("/bodies/Geometry/mass_from_visual")
        self.assertTrue(prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(prim)
        # 3.0 from the visual geom plus 1.0 from the collider.
        self.assertAlmostEqual(mass_api.GetMassAttr().Get(), 4.0, places=5)
        self.assertTrue(mass_api.GetDiagonalInertiaAttr().HasAuthoredValue())

        # The visual itself is plain geometry: no collider, no mass.
        visual = self.stage.GetPrimAtPath("/bodies/Geometry/mass_from_visual/geom_0")
        if visual.IsValid():
            self.assertFalse(visual.HasAPI(UsdPhysics.CollisionAPI))
            self.assertFalse(visual.HasAPI(UsdPhysics.MassAPI))

    def test_mass_not_baked_when_only_colliders_provide_it(self):
        """A body whose mass comes solely from colliders is left to USD accumulation.

        The colliders carry the authored mass, so a reader can aggregate it. Baking here would
        replace the source's per-geom description with a compiled number and override the
        author's intent to leave the mass implicit.
        """
        prim: Usd.Prim = self.stage.GetPrimAtPath("/bodies/Geometry/mass_from_colliders")
        self.assertTrue(prim.HasAPI(UsdPhysics.RigidBodyAPI))
        self.assertFalse(prim.HasAPI(UsdPhysics.MassAPI))

    def test_mass_baked_onto_the_right_body_through_attach(self):
        """Bake each body's own mass when attaching has shifted the compiled body ids.

        Attaching splices the attached subtree into the body tree, so a body after the attach
        point no longer compiles to the id its authored position among its siblings suggests.
        Every body in the fixture carries a distinct mass, so a lookup that misidentified the
        compiled body would bake a wrong number rather than fail outright.
        """
        model = pathlib.Path("./tests/data/mass_bake_attach.xml")
        # a directory of its own, so this asset does not overwrite the payload of the one in setUp
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir(model.stem))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # 5.0 from the attached body's visual geom plus 1.0 from its collider
        attached: Usd.Prim = stage.GetPrimAtPath("/mass_bake_attach/Geometry/before/attached_visual_mass")
        self.assertTrue(attached.HasAPI(UsdPhysics.MassAPI))
        self.assertAlmostEqual(UsdPhysics.MassAPI(attached).GetMassAttr().Get(), 6.0, places=5)

        # 9.0 from a visual geom plus 1.0 from a collider, two ids further along than authored
        after: Usd.Prim = stage.GetPrimAtPath("/mass_bake_attach/Geometry/after")
        self.assertTrue(after.HasAPI(UsdPhysics.MassAPI))
        self.assertAlmostEqual(UsdPhysics.MassAPI(after).GetMassAttr().Get(), 10.0, places=5)

        for path in ("before", "before/attached_visual_mass/attached_nested"):
            prim: Usd.Prim = stage.GetPrimAtPath(f"/mass_bake_attach/Geometry/{path}")
            self.assertTrue(prim.HasAPI(UsdPhysics.RigidBodyAPI))
            self.assertFalse(prim.HasAPI(UsdPhysics.MassAPI))

    def test_mass_not_baked_when_the_model_cannot_compile(self):
        """Warn and carry on when a body needs its mass baked but the model will not compile.

        Baking reads compiled values, which not every parsable MJCF can produce. Nothing else in
        the conversion depends on them, so the asset is still written, without mass properties.
        """
        model = pathlib.Path("./tests/data/mass_bake_uncompilable.xml")
        with usdex.test.ScopedDiagnosticChecker(
            self,
            [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Unable to compile the model to bake mass for body 'uncompilable'.*")],
            level=usdex.core.DiagnosticsLevel.eWarning,
        ):
            asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir(model.stem))

        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)
        prim: Usd.Prim = stage.GetPrimAtPath("/mass_bake_uncompilable/Geometry/uncompilable")
        self.assertTrue(prim.HasAPI(UsdPhysics.RigidBodyAPI))
        self.assertFalse(prim.HasAPI(UsdPhysics.MassAPI))

    def test_mass_not_baked_for_a_body_outside_the_converted_spec(self):
        """Warn rather than bake when the spec being converted does not contain the body.

        The lookup is positional, so a body it cannot place has to be reported rather than
        resolved to whichever body happens to occupy that position.
        """
        spec = mujoco.MjSpec.from_string("<mujoco><worldbody><body name='a'/></worldbody></mujoco>")
        other = mujoco.MjSpec.from_string("<mujoco><worldbody><body name='b'/></worldbody></mujoco>")
        data = ConversionData(
            spec=spec,
            model=None,
            content={},
            libraries={},
            references={},
            geom_targets={},
            name_cache=usdex.core.NameCache(),
            scene=False,
            comment="",
        )
        compiled = data.get_model()
        self.assertEqual(get_model_body_id(spec.body("a"), compiled, data), 1)
        self.assertIsNone(get_model_body_id(other.body("b"), compiled, data))

        stage: Usd.Stage = Usd.Stage.CreateInMemory()
        prim: Usd.Prim = UsdGeom.Xform.Define(stage, "/body").GetPrim()
        with usdex.test.ScopedDiagnosticChecker(
            self,
            [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Unable to locate body 'b' in the compiled model.*")],
            level=usdex.core.DiagnosticsLevel.eWarning,
        ):
            bake_body_mass(other.body("b"), prim, data)
        self.assertFalse(prim.HasAPI(UsdPhysics.MassAPI))

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
