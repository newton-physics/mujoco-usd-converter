# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import usdex.core
import usdex.test
from pxr import Sdf, Tf, Usd

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestActuators(ConverterTestCase):

    def test_simple_actuator(self):
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert("./tests/data/simple_actuator.xml", self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        simple_actuator = stage.GetPrimAtPath("/simple_actuator/Physics/position")
        self.assertTrue(simple_actuator.IsValid())
        self.assertEqual(simple_actuator.GetTypeName(), "MjcActuator")

        target_rel: Usd.Relationship = simple_actuator.GetRelationship("mjc:target")
        self.assertTrue(target_rel.IsValid())
        target_paths = target_rel.GetTargets()
        self.assertEqual(len(target_paths), 1)
        self.assertEqual(str(target_paths[0]), "/simple_actuator/Geometry/body/hinge")

        self.assertTrue(simple_actuator.GetAttribute("mjc:inheritRange").HasAuthoredValue())
        self.assertEqual(simple_actuator.GetAttribute("mjc:inheritRange").Get(), 0.9)
        self.assertEqual(simple_actuator.GetAttribute("mjc:gear").Get(), [10.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        self.assertIsValidUsd(stage)

    def test_joint_actuators(self):
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert("./tests/data/actuators.xml", self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        motor: Usd.Prim = stage.GetPrimAtPath("/actuators/Physics/Actuator_0")
        self.assertTrue(motor.IsValid())
        self.assertEqual(motor.GetTypeName(), "MjcActuator")

        # Check target relationship points to slide joint
        target_rel: Usd.Relationship = motor.GetRelationship("mjc:target")
        self.assertTrue(target_rel.IsValid())
        target_paths = target_rel.GetTargets()
        self.assertEqual(len(target_paths), 1)
        self.assertEqual(str(target_paths[0]), "/actuators/Geometry/base/box/box_joint")

        # Check actuator attributes
        self.assertEqual(motor.GetAttribute("mjc:ctrlLimited").Get(), "true")
        self.assertEqual(motor.GetAttribute("mjc:ctrlRange:min").Get(), -1.0)
        self.assertEqual(motor.GetAttribute("mjc:ctrlRange:max").Get(), 1.0)
        self.assertEqual(motor.GetAttribute("mjc:gear").Get(), [100.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual(motor.GetAttribute("mjc:group").Get(), 1)

        # Test position actuator (MjcActuator) for hinge joint
        position_actuator: Usd.Prim = stage.GetPrimAtPath("/actuators/Physics/Actuator_1")
        self.assertTrue(position_actuator.IsValid())
        self.assertEqual(position_actuator.GetTypeName(), "MjcActuator")

        # Check target relationship points to hinge joint
        target_rel = position_actuator.GetRelationship("mjc:target")
        self.assertTrue(target_rel.IsValid())
        target_paths = target_rel.GetTargets()
        self.assertEqual(len(target_paths), 1)
        self.assertEqual(str(target_paths[0]), "/actuators/Geometry/base/box/child/child_joint")

        self.assertTrue(position_actuator.GetAttribute("mjc:inheritRange").HasAuthoredValue())
        self.assertEqual(position_actuator.GetAttribute("mjc:inheritRange").Get(), True)
        self.assertFalse(position_actuator.GetAttribute("mjc:ctrlLimited").HasAuthoredValue())
        self.assertFalse(position_actuator.GetAttribute("mjc:ctrlRange:min").HasAuthoredValue())
        self.assertFalse(position_actuator.GetAttribute("mjc:ctrlRange:max").HasAuthoredValue())
        self.assertEqual(position_actuator.GetAttribute("mjc:gear").Get(), [10.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual(position_actuator.GetAttribute("mjc:group").Get(), 2)

        self.assertIsValidUsd(stage)

    def test_site_actuators(self):
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert("./tests/data/actuators.xml", self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        # Test site actuator without refsite (MjcActuator)
        site_actuator: Usd.Prim = stage.GetPrimAtPath("/actuators/Physics/Actuator_2")
        self.assertTrue(site_actuator.IsValid())
        self.assertEqual(site_actuator.GetTypeName(), "MjcActuator")

        # Check target relationship points to box site
        target_rel: Usd.Relationship = site_actuator.GetRelationship("mjc:target")
        self.assertTrue(target_rel.IsValid())
        target_paths = target_rel.GetTargets()
        self.assertEqual(len(target_paths), 1)
        self.assertEqual(str(target_paths[0]), "/actuators/Geometry/base/box/box_site")

        self.assertEqual(site_actuator.GetAttribute("mjc:dynType").Get(), "none")
        self.assertEqual(site_actuator.GetAttribute("mjc:gainType").Get(), "fixed")
        self.assertEqual(site_actuator.GetAttribute("mjc:biasType").Get(), "none")
        self.assertEqual(site_actuator.GetAttribute("mjc:gear").Get(), [1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual(site_actuator.GetAttribute("mjc:group").Get(), 3)

        # Test site actuator with refsite (MjcActuator)
        refsite_actuator: Usd.Prim = stage.GetPrimAtPath("/actuators/Physics/Actuator_3")
        self.assertTrue(refsite_actuator.IsValid())
        self.assertEqual(refsite_actuator.GetTypeName(), "MjcActuator")

        # Check target relationship points to child site
        target_rel: Usd.Relationship = refsite_actuator.GetRelationship("mjc:target")
        self.assertTrue(target_rel.IsValid())
        target_paths = target_rel.GetTargets()
        self.assertEqual(len(target_paths), 1)
        self.assertEqual(str(target_paths[0]), "/actuators/Geometry/base/box/child/child_site")

        self.assertEqual(refsite_actuator.GetAttribute("mjc:dynType").Get(), "integrator")
        self.assertEqual(refsite_actuator.GetAttribute("mjc:gainType").Get(), "affine")
        self.assertEqual(refsite_actuator.GetAttribute("mjc:gear").Get(), [0.0, 1.0, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual(refsite_actuator.GetAttribute("mjc:group").Get(), 0)

        # Check refsite relationship
        refsite_rel: Usd.Relationship = refsite_actuator.GetRelationship("mjc:refSite")
        self.assertTrue(refsite_rel.IsValid())
        refsite_targets = refsite_rel.GetTargets()
        self.assertEqual(len(refsite_targets), 1)
        self.assertEqual(str(refsite_targets[0]), "/actuators/Geometry/base/box/box_site")

        self.assertIsValidUsd(stage)

    def test_body_actuator(self):
        # Test body actuator (MjcActuator)
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert("./tests/data/actuators.xml", self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        body_actuator: Usd.Prim = stage.GetPrimAtPath("/actuators/Physics/Actuator_4")
        self.assertTrue(body_actuator.IsValid())
        self.assertEqual(body_actuator.GetTypeName(), "MjcActuator")

        # Check target relationship points to box body
        target_rel: Usd.Relationship = body_actuator.GetRelationship("mjc:target")
        self.assertTrue(target_rel.IsValid())
        target_paths = target_rel.GetTargets()
        self.assertEqual(len(target_paths), 1)
        self.assertEqual(str(target_paths[0]), "/actuators/Geometry/base/box")

        self.assertEqual(body_actuator.GetAttribute("mjc:dynType").Get(), "filter")
        self.assertEqual(body_actuator.GetAttribute("mjc:gainType").Get(), "fixed")
        self.assertEqual(body_actuator.GetAttribute("mjc:biasType").Get(), "none")
        self.assertEqual(body_actuator.GetAttribute("mjc:gear").Get(), [0.0, 0.0, 1.0, 0.0, 0.0, 0.0])
        self.assertEqual(body_actuator.GetAttribute("mjc:forceLimited").Get(), "true")
        self.assertEqual(body_actuator.GetAttribute("mjc:forceRange:min").Get(), -100.0)
        self.assertEqual(body_actuator.GetAttribute("mjc:forceRange:max").Get(), 100.0)
        self.assertEqual(body_actuator.GetAttribute("mjc:group").Get(), 0)

        self.assertIsValidUsd(stage)

    def test_slider_crank_actuator(self):
        # Test slider-crank actuator (MjcActuator)
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert("./tests/data/actuators.xml", self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        slider_crank: Usd.Prim = stage.GetPrimAtPath("/actuators/Physics/Actuator_5")
        self.assertTrue(slider_crank.IsValid())
        self.assertEqual(slider_crank.GetTypeName(), "MjcActuator")

        # Check target relationship points to crank site
        target_rel: Usd.Relationship = slider_crank.GetRelationship("mjc:target")
        self.assertTrue(target_rel.IsValid())
        target_paths = target_rel.GetTargets()
        self.assertEqual(len(target_paths), 1)
        self.assertEqual(str(target_paths[0]), "/actuators/Geometry/base/box/box_site")

        # Check slider-crank specific attributes
        self.assertEqual(slider_crank.GetAttribute("mjc:crankLength").Get(), 0.1)
        self.assertEqual(slider_crank.GetAttribute("mjc:gear").Get(), [1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual(slider_crank.GetAttribute("mjc:group").Get(), 0)

        # Check slidersite relationship
        slidersite_rel: Usd.Relationship = slider_crank.GetRelationship("mjc:sliderSite")
        self.assertTrue(slidersite_rel.IsValid())
        slidersite_targets = slidersite_rel.GetTargets()
        self.assertEqual(len(slidersite_targets), 1)
        self.assertEqual(str(slidersite_targets[0]), "/actuators/Geometry/base/box/child/child_site")

        self.assertIsValidUsd(stage)


class TestActuatorEdgeCases(ConverterTestCase):

    def setUp(self):
        super().setUp()
        with usdex.test.ScopedDiagnosticChecker(
            self,
            [
                (Tf.TF_DIAGNOSTIC_WARNING_TYPE, ".*not found for actuator 'missing_target'"),
                (Tf.TF_DIAGNOSTIC_WARNING_TYPE, ".*not found for actuator 'missing_refsite'"),
                (Tf.TF_DIAGNOSTIC_WARNING_TYPE, ".*not found for actuator 'missing_slidersite'"),
            ],
            level=usdex.core.DiagnosticsLevel.eWarning,
        ):
            asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert("./tests/data/actuator_edge_cases.xml", self.tmpDir())
        self.stage: Usd.Stage = Usd.Stage.Open(asset.path)

    def tearDown(self):
        self.assertIsValidUsd(self.stage)
        self.stage = None
        super().tearDown()

    def test_unnamed(self):
        unnamed_actuator = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/Actuator_0")
        self.assertTrue(unnamed_actuator.IsValid())
        self.assertEqual(unnamed_actuator.GetTypeName(), "MjcActuator")

    def test_duplicate_name(self):
        # One actuator should keep the original name, the other should get a modified name
        dup1 = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/duplicate_name")
        dup2 = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/duplicate_name_1")
        self.assertTrue(dup1.IsValid() or dup2.IsValid())
        self.assertEqual(dup1.GetTypeName(), "MjcActuator")
        self.assertTrue(dup2.IsValid())
        self.assertEqual(dup2.GetTypeName(), "MjcActuator")

    def test_missing_target(self):
        # Test actuators with missing targets (should create actuators but with warnings)
        missing_target = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/missing_target")
        self.assertTrue(missing_target.IsValid())
        self.assertEqual(missing_target.GetTypeName(), "MjcActuator")
        self.assertFalse(missing_target.GetRelationship("mjc:target").GetTargets())

        missing_refsite = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/missing_refsite")
        self.assertTrue(missing_refsite.IsValid())
        self.assertEqual(missing_refsite.GetTypeName(), "MjcActuator")
        self.assertFalse(missing_refsite.GetRelationship("mjc:refSite").GetTargets())

        missing_slidersite = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/missing_slidersite")
        self.assertTrue(missing_slidersite.IsValid())
        self.assertEqual(missing_slidersite.GetTypeName(), "MjcActuator")
        self.assertFalse(missing_slidersite.GetRelationship("mjc:sliderSite").GetTargets())

    def test_dyntype(self):
        none_dyn = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/none_dyn")
        self.assertTrue(none_dyn.IsValid())
        self.assertEqual(none_dyn.GetAttribute("mjc:dynType").Get(), "none")

        integrator_dyn = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/integrator_dyn")
        self.assertTrue(integrator_dyn.IsValid())
        self.assertEqual(integrator_dyn.GetAttribute("mjc:dynType").Get(), "integrator")

        filter_dyn = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/filter_dyn")
        self.assertTrue(filter_dyn.IsValid())
        self.assertEqual(filter_dyn.GetAttribute("mjc:dynType").Get(), "filter")

        filterexact_actuator = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/filterexact_dyn")
        self.assertTrue(filterexact_actuator.IsValid())
        self.assertEqual(filterexact_actuator.GetAttribute("mjc:dynType").Get(), "filterexact")

        muscle_dyn_actuator = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/muscle_dyn")
        self.assertTrue(muscle_dyn_actuator.IsValid())
        self.assertEqual(muscle_dyn_actuator.GetAttribute("mjc:dynType").Get(), "muscle")

        user_dyn_actuator = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/user_dyn")
        self.assertTrue(user_dyn_actuator.IsValid())
        self.assertEqual(user_dyn_actuator.GetAttribute("mjc:dynType").Get(), "user")

    def test_gaintype(self):
        fixed_gain = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/fixed_gain")
        self.assertTrue(fixed_gain.IsValid())
        self.assertEqual(fixed_gain.GetAttribute("mjc:gainType").Get(), "fixed")

        affine_gain = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/affine_gain")
        self.assertTrue(affine_gain.IsValid())
        self.assertEqual(affine_gain.GetAttribute("mjc:gainType").Get(), "affine")

        muscle_gain_actuator = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/muscle_gain")
        self.assertTrue(muscle_gain_actuator.IsValid())
        self.assertEqual(muscle_gain_actuator.GetAttribute("mjc:gainType").Get(), "muscle")

        user_gain_actuator = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/user_gain")
        self.assertTrue(user_gain_actuator.IsValid())
        self.assertEqual(user_gain_actuator.GetAttribute("mjc:gainType").Get(), "user")

    def test_biastype(self):
        none_bias = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/none_bias")
        self.assertTrue(none_bias.IsValid())
        self.assertEqual(none_bias.GetAttribute("mjc:biasType").Get(), "none")

        affine_bias = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/affine_bias")
        self.assertTrue(affine_bias.IsValid())
        self.assertEqual(affine_bias.GetAttribute("mjc:biasType").Get(), "affine")

        muscle_bias_actuator = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/muscle_bias")
        self.assertTrue(muscle_bias_actuator.IsValid())
        self.assertEqual(muscle_bias_actuator.GetAttribute("mjc:biasType").Get(), "muscle")

        user_bias_actuator = self.stage.GetPrimAtPath("/actuator_edge_cases/Physics/user_bias")
        self.assertTrue(user_bias_actuator.IsValid())
        self.assertEqual(user_bias_actuator.GetAttribute("mjc:biasType").Get(), "user")
