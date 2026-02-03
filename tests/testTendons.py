# SPDX-FileCopyrightText: Copyright (c) 2025-2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib

import usdex.test
from pxr import Sdf, Tf, Usd

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestTendons(ConverterTestCase):

    def __has_authored_value(self, property: Usd.Property) -> bool:
        if hasattr(property, "HasAuthoredValue"):
            return property.HasAuthoredValue()
        else:
            return property.HasAuthoredTargets()

    def test_fixed_mjc_schema(self):
        # Test that all joint attributes are authored correctly
        model = pathlib.Path("./tests/data/tendon_fixed_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # A joints attributes are authored to USD if they are set to non-default values
        custom_tendon: Usd.Prim = stage.GetPrimAtPath("/tendon_fixed_attributes/Physics/custom_tendon")
        self.assertTrue(custom_tendon.IsValid())
        self.assertEqual(custom_tendon.GetTypeName(), "MjcTendon")

        # Check that all possible MJC properties are authored, fixed tendons don't use these
        not_authored_properties = [
            "mjc:path:divisors",
            "mjc:path:segments",
            "mjc:sideSites",
            "mjc:sideSites:indices",
            "mjc:rgba",
            "mjc:width",
        ]
        for property in custom_tendon.GetPropertiesInNamespace("mjc"):
            if property.GetName() in not_authored_properties:
                self.assertFalse(self.__has_authored_value(property), f"Property {property.GetName()} is authored")
            else:
                self.assertTrue(self.__has_authored_value(property), f"Property {property.GetName()} is not authored")

        # Check that all attributes are authored correctly
        self.assertEqual(custom_tendon.GetAttribute("mjc:actuatorfrclimited").Get(), "false")
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:actuatorfrcrange:min").Get(), 0.1)
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:actuatorfrcrange:max").Get(), 0.2)
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:armature").Get(), 0.3)
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:damping").Get(), 0.4)
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:frictionloss").Get(), 0.5)
        self.assertEqual(custom_tendon.GetAttribute("mjc:group").Get(), 1)
        self.assertEqual(custom_tendon.GetAttribute("mjc:limited").Get(), "false")
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:margin").Get(), 0.6)
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:range:min").Get(), 0.7)
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:range:max").Get(), 0.8)

        expected_solimpfriction = [0.95, 0.96, 0.002, 0.6, 3]
        actual_solimpfriction = custom_tendon.GetAttribute("mjc:solimpfriction").Get()
        for i in range(5):
            self.assertAlmostEqual(actual_solimpfriction[i], expected_solimpfriction[i])

        expected_solimplimit = [0.96, 0.97, 0.003, 0.7, 4]
        actual_solimplimit = custom_tendon.GetAttribute("mjc:solimplimit").Get()
        for i in range(5):
            self.assertAlmostEqual(actual_solimplimit[i], expected_solimplimit[i])

        expected_solreffriction = [0.03, 1.1]
        solreffriction = custom_tendon.GetAttribute("mjc:solreffriction").Get()
        for i in range(2):
            self.assertAlmostEqual(solreffriction[i], expected_solreffriction[i])
        expected_solreflimit = [0.04, 1.2]
        actual_solreflimit = custom_tendon.GetAttribute("mjc:solreflimit").Get()
        for i in range(2):
            self.assertAlmostEqual(actual_solreflimit[i], expected_solreflimit[i])
        expected_springlength = [0.95, 0.99]
        actual_springlength = custom_tendon.GetAttribute("mjc:springlength").Get()
        for i in range(2):
            self.assertAlmostEqual(actual_springlength[i], expected_springlength[i])
        expected_stiffness = 1.1
        actual_stiffness = custom_tendon.GetAttribute("mjc:stiffness").Get()
        self.assertAlmostEqual(actual_stiffness, expected_stiffness)

        # Check that the path is authored correctly
        targets = ["/tendon_fixed_attributes/Geometry/body0/joint0", "/tendon_fixed_attributes/Geometry/body0/body1/joint1"]
        self.assertEqual(custom_tendon.GetRelationship("mjc:path").GetTargets(), targets)
        expected_path_coef = [0.1, 0.2]
        actual_path_coef = custom_tendon.GetAttribute("mjc:path:coef").Get()
        for i in range(2):
            self.assertAlmostEqual(actual_path_coef[i], expected_path_coef[i])

        # A joint with explicitly authored default values in MJC does not need to author any values in USD
        default_tendon: Usd.Prim = stage.GetPrimAtPath("/tendon_fixed_attributes/Physics/default_tendon")
        self.assertTrue(default_tendon.IsValid())
        self.assertEqual(default_tendon.GetTypeName(), "MjcTendon")

        # Check that only expected MJC properties are authored
        authored_properties = [
            "mjc:type",
            "mjc:path",
            "mjc:path:indices",
            "mjc:path:coef",
        ]
        for property in default_tendon.GetPropertiesInNamespace("mjc"):
            if property.GetName() in authored_properties:
                self.assertTrue(self.__has_authored_value(property), f"Property {property.GetName()} is not authored")
            else:
                self.assertFalse(self.__has_authored_value(property), f"Property {property.GetName()} is authored")

    def test_spatial_mjc_schema(self):
        # Test that all joint attributes are authored correctly
        model = pathlib.Path("./tests/data/tendon_spatial_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # A joints attributes are authored to USD if they are set to non-default values
        custom_tendon: Usd.Prim = stage.GetPrimAtPath("/tendon_spatial_attributes/Physics/custom_tendon")
        self.assertTrue(custom_tendon.IsValid())
        self.assertEqual(custom_tendon.GetTypeName(), "MjcTendon")

        # Check that all possible MJC properties are authored, spatial tendons don't use these
        not_authored_properties = [
            "mjc:armature",  # geom wrapping not supported by tendon armature
            "mjc:path:coef",
        ]
        for property in custom_tendon.GetPropertiesInNamespace("mjc"):
            if property.GetName() in not_authored_properties:
                self.assertFalse(self.__has_authored_value(property), f"Property {property.GetName()} is authored")
            else:
                self.assertTrue(self.__has_authored_value(property), f"Property {property.GetName()} is not authored")

        # Check that all attributes are authored correctly
        self.assertEqual(custom_tendon.GetAttribute("mjc:actuatorfrclimited").Get(), "false")
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:actuatorfrcrange:min").Get(), 0.1)
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:actuatorfrcrange:max").Get(), 0.2)
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:armature").Get(), 0.0)
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:damping").Get(), 0.4)
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:frictionloss").Get(), 0.5)
        self.assertEqual(custom_tendon.GetAttribute("mjc:group").Get(), 1)
        self.assertEqual(custom_tendon.GetAttribute("mjc:limited").Get(), "false")
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:margin").Get(), 0.6)
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:range:min").Get(), 0.7)
        self.assertAlmostEqual(custom_tendon.GetAttribute("mjc:range:max").Get(), 0.8)

        expected_solimpfriction = [0.95, 0.96, 0.002, 0.6, 3]
        actual_solimpfriction = custom_tendon.GetAttribute("mjc:solimpfriction").Get()
        self.assertEqual(len(actual_solimpfriction), len(expected_solimpfriction))
        for i in range(5):
            self.assertAlmostEqual(actual_solimpfriction[i], expected_solimpfriction[i])

        expected_solimplimit = [0.96, 0.97, 0.003, 0.7, 4]
        actual_solimplimit = custom_tendon.GetAttribute("mjc:solimplimit").Get()
        self.assertEqual(len(actual_solimplimit), len(expected_solimplimit))
        for i in range(5):
            self.assertAlmostEqual(actual_solimplimit[i], expected_solimplimit[i])

        expected_solreffriction = [0.03, 1.1]
        solreffriction = custom_tendon.GetAttribute("mjc:solreffriction").Get()
        self.assertEqual(len(solreffriction), len(expected_solreffriction))
        for i in range(2):
            self.assertAlmostEqual(solreffriction[i], expected_solreffriction[i])

        expected_solreflimit = [0.04, 1.2]
        actual_solreflimit = custom_tendon.GetAttribute("mjc:solreflimit").Get()
        self.assertEqual(len(actual_solreflimit), len(expected_solreflimit))
        for i in range(2):
            self.assertAlmostEqual(actual_solreflimit[i], expected_solreflimit[i])

        expected_springlength = [0.95, 0.99]
        actual_springlength = custom_tendon.GetAttribute("mjc:springlength").Get()
        self.assertEqual(len(actual_springlength), len(expected_springlength))
        for i in range(2):
            self.assertAlmostEqual(actual_springlength[i], expected_springlength[i])

        expected_stiffness = 1.1
        actual_stiffness = custom_tendon.GetAttribute("mjc:stiffness").Get()
        self.assertAlmostEqual(actual_stiffness, expected_stiffness)

        # Check that the path is authored correctly
        targets = [
            "/tendon_spatial_attributes/Geometry/body0/site0",
            "/tendon_spatial_attributes/Geometry/body0/body1/geom1",
            "/tendon_spatial_attributes/Geometry/body0/body1/site1",
            "/tendon_spatial_attributes/Geometry/body0/body1/body2/site2",
        ]
        self.assertEqual(custom_tendon.GetRelationship("mjc:path").GetTargets(), targets)

        targets = [
            "/tendon_spatial_attributes/Geometry/body0/body1/side1",
        ]
        self.assertEqual(custom_tendon.GetRelationship("mjc:sideSites").GetTargets(), targets)

        expected_path_segments = [0, 0, 0, 0]
        actual_path_segments = custom_tendon.GetAttribute("mjc:path:segments").Get()
        self.assertEqual(len(actual_path_segments), len(expected_path_segments))
        for i in range(3):
            self.assertEqual(actual_path_segments[i], expected_path_segments[i])

        expected_side_sites_indices = [-1, 0, -1, -1]
        actual_side_sites_indices = custom_tendon.GetAttribute("mjc:sideSites:indices").Get()
        self.assertEqual(len(actual_side_sites_indices), len(expected_side_sites_indices))
        for i in range(4):
            self.assertEqual(actual_side_sites_indices[i], expected_side_sites_indices[i])

        expected_path_divisors = [1.0]
        actual_path_divisors = custom_tendon.GetAttribute("mjc:path:divisors").Get()
        self.assertEqual(len(actual_path_divisors), len(expected_path_divisors))
        for i in range(len(actual_path_divisors)):
            self.assertAlmostEqual(actual_path_divisors[i], expected_path_divisors[i])

        # A joint with explicitly authored default values in MJC does not need to author any values in USD
        default_tendon: Usd.Prim = stage.GetPrimAtPath("/tendon_spatial_attributes/Physics/default_tendon")
        self.assertTrue(default_tendon.IsValid())
        self.assertEqual(default_tendon.GetTypeName(), "MjcTendon")

        # Check that only expected MJC properties are authored
        authored_properties = [
            "mjc:type",
            "mjc:path",
            "mjc:path:indices",
            "mjc:path:divisors",
            "mjc:path:segments",
        ]
        for property in default_tendon.GetPropertiesInNamespace("mjc"):
            if property.GetName() in authored_properties:
                self.assertTrue(self.__has_authored_value(property), f"Property {property.GetName()} is not authored")
            else:
                self.assertFalse(self.__has_authored_value(property), f"Property {property.GetName()} is authored")

    def test_tendon_actuator(self):
        # Test that the actuator is using tendon transmission correctly
        model = pathlib.Path("./tests/data/tendon_actuator.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # A tendon is authored to USD if it is set to non-default values
        tendon: Usd.Prim = stage.GetPrimAtPath("/tendon_actuator/Physics/coupled_tendon")
        self.assertTrue(tendon.IsValid())
        self.assertEqual(tendon.GetTypeName(), "MjcTendon")

        # Check that all attributes are authored correctly
        self.assertEqual(tendon.GetAttribute("mjc:type").Get(), "fixed")
        target_paths = [
            "/tendon_actuator/Geometry/body1/hinge1",
            "/tendon_actuator/Geometry/body1/body2/hinge2",
        ]
        self.assertEqual(tendon.GetRelationship("mjc:path").GetTargets(), target_paths)

        expected_path_indices = [0, 1]
        self.assertEqual(list(tendon.GetAttribute("mjc:path:indices").Get()), expected_path_indices)

        # mjc:path:coef - [1.0, 1.0] since no pulleys
        self.assertEqual(tendon.GetAttribute("mjc:path:coef").Get(), [1.0, 1.0])

        # Check that the actuator is using tendon transmission correctly
        actuator: Usd.Prim = stage.GetPrimAtPath("/tendon_actuator/Physics/tendon_actuator")
        self.assertTrue(actuator.IsValid())
        self.assertEqual(actuator.GetTypeName(), "MjcActuator")

        # Check that the actuator is using tendon transmission correctly
        self.assertEqual(actuator.GetRelationship("mjc:target").GetTargets(), ["/tendon_actuator/Physics/coupled_tendon"])

    def test_sidesites(self):
        # Test that the spatial tendon is using sidesites correctly, also checks that non-collision geoms are targeted correctly
        model = pathlib.Path("./tests/data/tendon_spatial_sidesites.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        base_path = "/tendon_spatial_sidesites"
        geom_path = f"{base_path}/Geometry"
        physics_path = f"{base_path}/Physics"

        # Test multi_wrap_tendon - has 3 geom wraps with sidesites
        multi_wrap: Usd.Prim = stage.GetPrimAtPath(f"{physics_path}/multi_wrap_tendon")
        self.assertTrue(multi_wrap.IsValid())
        self.assertEqual(multi_wrap.GetTypeName(), "MjcTendon")

        # mjc:path - 7 elements: start_site, wrap_geom0, mid_site, wrap_geom1, between_site, wrap_geom2, end_site
        expected_multi_wrap_path = [
            f"{geom_path}/body0/start_site",
            f"{geom_path}/body0/wrap_geom0",
            f"{geom_path}/body0/body1/mid_site",
            f"{geom_path}/body0/body1/wrap_geom1",
            f"{geom_path}/body0/body1/body2/between_site",
            f"{geom_path}/body0/body1/body2/wrap_geom2",
            f"{geom_path}/body0/body1/body2/body3/end_site",
        ]
        self.assertEqual(multi_wrap.GetRelationship("mjc:path").GetTargets(), expected_multi_wrap_path)

        # mjc:path:indices - index into path array
        expected_multi_wrap_indices = [0, 1, 2, 3, 4, 5, 6]
        self.assertEqual(list(multi_wrap.GetAttribute("mjc:path:indices").Get()), expected_multi_wrap_indices)

        # mjc:path:segments - all 0 since no pulleys
        expected_multi_wrap_segments = [0, 0, 0, 0, 0, 0, 0]
        self.assertEqual(list(multi_wrap.GetAttribute("mjc:path:segments").Get()), expected_multi_wrap_segments)

        # mjc:sideSites - 3 sidesites
        expected_multi_wrap_sidesites = [
            f"{geom_path}/body0/sidesite0",
            f"{geom_path}/body0/body1/sidesite1",
            f"{geom_path}/body0/body1/body2/sidesite2",
        ]
        self.assertEqual(multi_wrap.GetRelationship("mjc:sideSites").GetTargets(), expected_multi_wrap_sidesites)

        # mjc:sideSites:indices - index into sideSites array, -1 if no sidesite
        expected_multi_wrap_indices = [-1, 0, -1, 1, -1, 2, -1]
        self.assertEqual(list(multi_wrap.GetAttribute("mjc:sideSites:indices").Get()), expected_multi_wrap_indices)

        # mjc:path:divisors - [1.0] since no pulleys
        expected_multi_wrap_divisors = [1.0]
        self.assertEqual(list(multi_wrap.GetAttribute("mjc:path:divisors").Get()), expected_multi_wrap_divisors)

        # Test single_wrap_tendon - has 1 geom wrap with sidesite
        single_wrap: Usd.Prim = stage.GetPrimAtPath(f"{physics_path}/single_wrap_tendon")
        self.assertTrue(single_wrap.IsValid())

        expected_single_wrap_path = [
            f"{geom_path}/body0/start_site",
            f"{geom_path}/body0/body1/wrap_geom1",
            f"{geom_path}/body0/body1/body2/body3/end_site",
        ]
        self.assertEqual(single_wrap.GetRelationship("mjc:path").GetTargets(), expected_single_wrap_path)

        expected_single_wrap_segments = [0, 0, 0]
        self.assertEqual(list(single_wrap.GetAttribute("mjc:path:segments").Get()), expected_single_wrap_segments)

        expected_single_wrap_sidesites = [f"{geom_path}/body0/body1/sidesite1"]
        self.assertEqual(single_wrap.GetRelationship("mjc:sideSites").GetTargets(), expected_single_wrap_sidesites)

        expected_single_wrap_indices = [-1, 0, -1]
        self.assertEqual(list(single_wrap.GetAttribute("mjc:sideSites:indices").Get()), expected_single_wrap_indices)

        expected_single_wrap_divisors = [1.0]
        self.assertEqual(list(single_wrap.GetAttribute("mjc:path:divisors").Get()), expected_single_wrap_divisors)

        # Test geom_no_sidesite_tendon - has 1 geom wrap but NO sidesite
        geom_no_sidesite: Usd.Prim = stage.GetPrimAtPath(f"{physics_path}/geom_no_sidesite_tendon")
        self.assertTrue(geom_no_sidesite.IsValid())

        expected_geom_no_sidesite_path = [
            f"{geom_path}/body0/start_site",
            f"{geom_path}/body0/body1/wrap_geom1",
            f"{geom_path}/body0/body1/body2/body3/end_site",
        ]
        self.assertEqual(geom_no_sidesite.GetRelationship("mjc:path").GetTargets(), expected_geom_no_sidesite_path)

        expected_geom_no_sidesite_segments = [0, 0, 0]
        self.assertEqual(list(geom_no_sidesite.GetAttribute("mjc:path:segments").Get()), expected_geom_no_sidesite_segments)

        # No sidesites - relationship should have no targets
        self.assertEqual(geom_no_sidesite.GetRelationship("mjc:sideSites").GetTargets(), [])

        # sideSites:indices should NOT be authored when there are no sidesites
        self.assertFalse(self.__has_authored_value(geom_no_sidesite.GetAttribute("mjc:sideSites:indices")))

        expected_geom_no_sidesite_divisors = [1.0]
        self.assertEqual(list(geom_no_sidesite.GetAttribute("mjc:path:divisors").Get()), expected_geom_no_sidesite_divisors)

        # Test no_wrap_tendon - no geom wraps, just sites
        no_wrap: Usd.Prim = stage.GetPrimAtPath(f"{physics_path}/no_wrap_tendon")
        self.assertTrue(no_wrap.IsValid())

        expected_no_wrap_path = [
            f"{geom_path}/body0/start_site",
            f"{geom_path}/body0/body1/mid_site",
            f"{geom_path}/body0/body1/body2/body3/end_site",
        ]
        self.assertEqual(no_wrap.GetRelationship("mjc:path").GetTargets(), expected_no_wrap_path)

        expected_no_wrap_segments = [0, 0, 0]
        self.assertEqual(list(no_wrap.GetAttribute("mjc:path:segments").Get()), expected_no_wrap_segments)

        # No sidesites - relationship should have no targets
        self.assertEqual(no_wrap.GetRelationship("mjc:sideSites").GetTargets(), [])

        # sideSites:indices should NOT be authored when there are no sidesites
        self.assertFalse(self.__has_authored_value(no_wrap.GetAttribute("mjc:sideSites:indices")))

        expected_no_wrap_divisors = [1.0]
        self.assertEqual(list(no_wrap.GetAttribute("mjc:path:divisors").Get()), expected_no_wrap_divisors)

    def test_tendon_pulley_degenerate(self):
        # @TODO: The pulley doesn't behave the same in mujoco, need to fix that...
        # Test that the pulley tendon is authored correctly
        model = pathlib.Path("./tests/data/tendon_pulley.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # A tendon is authored to USD if it is set to non-default values
        tendon: Usd.Prim = stage.GetPrimAtPath("/tendon_pulley/Physics/four_to_one_pulley")
        self.assertTrue(tendon.IsValid())
        self.assertEqual(tendon.GetTypeName(), "MjcTendon")

        self.assertEqual(tendon.GetAttribute("mjc:type").Get(), "spatial")

        # Check that the path is authored correctly
        targets = [
            "/tendon_pulley/Geometry/support/anchor_left",
            "/tendon_pulley/Geometry/heavy_weight/heavy_site",
            "/tendon_pulley/Geometry/support/anchor_right",
            "/tendon_pulley/Geometry/light_weight/light_site",
        ]
        self.assertEqual(tendon.GetRelationship("mjc:path").GetTargets(), targets)

        expected_path_indices = [0, 1, 2, 3]
        self.assertEqual(list(tendon.GetAttribute("mjc:path:indices").Get()), expected_path_indices)

        expected_path_divisors = [0.5, 2.0]
        actual_path_divisors = tendon.GetAttribute("mjc:path:divisors").Get()
        self.assertEqual(len(actual_path_divisors), len(expected_path_divisors))
        for i in range(len(actual_path_divisors)):
            self.assertAlmostEqual(actual_path_divisors[i], expected_path_divisors[i])

        expected_path_segments = [0, 0, 1, 1]
        actual_path_segments = tendon.GetAttribute("mjc:path:segments").Get()
        self.assertEqual(len(actual_path_segments), len(expected_path_segments))
        for i in range(len(actual_path_segments)):
            self.assertEqual(actual_path_segments[i], expected_path_segments[i])

        # No sidesites - relationship should have no targets
        self.assertEqual(tendon.GetRelationship("mjc:sideSites").GetTargets(), [])
        self.assertFalse(self.__has_authored_value(tendon.GetAttribute("mjc:sideSites:indices")))

    def test_tendon_pulley_from_docs(self):
        # Test that the pulley tendon is authored correctly
        model = pathlib.Path("./tests/data/tendon_docs.xml")
        with usdex.test.ScopedDiagnosticChecker(
            self,
            [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, ".*lights are not supported.*")],
            level=usdex.core.DiagnosticsLevel.eWarning,
        ):
            asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # This verifies that we auto-generate a name for the tendon if it doesn't have one
        tendon: Usd.Prim = stage.GetPrimAtPath("/tendon_docs/Physics/Tendon_0")
        self.assertTrue(tendon.IsValid())
        self.assertEqual(tendon.GetTypeName(), "MjcTendon")

        self.assertEqual(tendon.GetAttribute("mjc:type").Get(), "spatial")

        # Check that the path is authored correctly
        targets = [
            "/tendon_docs/Geometry/weight/s1",
            "/tendon_docs/Geometry/s2",
            "/tendon_docs/Geometry/Body/g1",
            "/tendon_docs/Geometry/Body/s3",
            "/tendon_docs/Geometry/Body/Body/g2",
            "/tendon_docs/Geometry/Body/Body/s4",
            "/tendon_docs/Geometry/Body/Body/s5",
            "/tendon_docs/Geometry/Body/Body/Body/g3",
            "/tendon_docs/Geometry/Body/Body/Body/s6",
        ]
        self.assertEqual(tendon.GetRelationship("mjc:path").GetTargets(), targets)

        expected_path_indices = [0, 1, 2, 3, 3, 4, 5, 3, 4, 6, 7, 8]
        self.assertEqual(tendon.GetAttribute("mjc:path:indices").Get(), expected_path_indices)

        expected_path_divisors = [1, 2, 2]
        actual_path_divisors = tendon.GetAttribute("mjc:path:divisors").Get()
        self.assertEqual(len(actual_path_divisors), len(expected_path_divisors))
        for i in range(len(actual_path_divisors)):
            self.assertAlmostEqual(actual_path_divisors[i], expected_path_divisors[i])

        expected_path_segments = [0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2]
        self.assertEqual(tendon.GetAttribute("mjc:path:segments").Get(), expected_path_segments)

        expected_side_sites = [
            "/tendon_docs/Geometry/Body/Body/side2",
            "/tendon_docs/Geometry/Body/Body/Body/side3",
        ]
        self.assertEqual(list(tendon.GetRelationship("mjc:sideSites").GetTargets()), expected_side_sites)
        expected_side_sites_indices = [-1, -1, -1, -1, -1, 0, -1, -1, 0, -1, 1, -1]
        self.assertEqual(list(tendon.GetAttribute("mjc:sideSites:indices").Get()), expected_side_sites_indices)

        self.assertAlmostEqual(tendon.GetAttribute("mjc:range:max").Get(), 0.33)
        expected_rgba = [0.95, 0.3, 0.3, 1]
        for i in range(4):
            self.assertAlmostEqual(tendon.GetAttribute("mjc:rgba").Get()[i], expected_rgba[i])
        self.assertAlmostEqual(tendon.GetAttribute("mjc:width").Get(), 0.002)

    def test_tendon_spatial_anchor(self):
        # Test that the pulley tendon is authored correctly
        model = pathlib.Path("./tests/data/tendon_spatial_anchor.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # This tendon has an invalid USD name, test that we auto-generate a name and display name
        tendon: Usd.Prim = stage.GetPrimAtPath("/tendon_spatial_anchor/Physics/tn__anchortendon_oC")
        self.assertTrue(tendon.IsValid())
        self.assertEqual(tendon.GetTypeName(), "MjcTendon")
        self.assertEqual(tendon.GetDisplayName(), "anchor tendon")

        self.assertEqual(tendon.GetAttribute("mjc:type").Get(), "spatial")

        # Check that the path is authored correctly
        targets = [
            "/tendon_spatial_anchor/Geometry/weight/weight_top",
            "/tendon_spatial_anchor/Geometry/frame/anchor_left",
            "/tendon_spatial_anchor/Geometry/frame/anchor_right",
            "/tendon_spatial_anchor/Geometry/arm_base/arm_base_site",
            "/tendon_spatial_anchor/Geometry/arm_base/arm_segment/arm_end/arm_end_site",
        ]
        self.assertEqual(tendon.GetRelationship("mjc:path").GetTargets(), targets)

        expected_path_indices = [0, 1, 2, 3, 4]
        self.assertEqual(tendon.GetAttribute("mjc:path:indices").Get(), expected_path_indices)

        expected_path_divisors = [1.0]
        actual_path_divisors = tendon.GetAttribute("mjc:path:divisors").Get()
        self.assertEqual(len(actual_path_divisors), len(expected_path_divisors))
        for i in range(len(actual_path_divisors)):
            self.assertAlmostEqual(actual_path_divisors[i], expected_path_divisors[i])

        expected_path_segments = [0, 0, 0, 0, 0]
        self.assertEqual(tendon.GetAttribute("mjc:path:segments").Get(), expected_path_segments)

        expected_side_sites = []
        self.assertEqual(list(tendon.GetRelationship("mjc:sideSites").GetTargets()), expected_side_sites)
        expected_side_sites_indices = []
        self.assertEqual(list(tendon.GetAttribute("mjc:sideSites:indices").Get()), expected_side_sites_indices)

        expected_rgba = [0.9, 0.6, 0.1, 1]
        for i in range(4):
            self.assertAlmostEqual(tendon.GetAttribute("mjc:rgba").Get()[i], expected_rgba[i])
        self.assertAlmostEqual(tendon.GetAttribute("mjc:width").Get(), 0.01)

        stiffness = 1000.0
        self.assertAlmostEqual(tendon.GetAttribute("mjc:stiffness").Get(), stiffness)

    def test_single_springlength_value(self):

        model = pathlib.Path("./tests/data/tendon_single_springlength.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # Verify springlength=[0.5] becomes [0.5, 0.5]
        tendon: Usd.Prim = stage.GetPrimAtPath("/tendon_single_springlength/Physics/tether")
        self.assertTrue(tendon.IsValid())
        self.assertEqual(tendon.GetTypeName(), "MjcTendon")
        self.assertEqual(tendon.GetAttribute("mjc:springlength").Get(), [0.3, 0.3])
