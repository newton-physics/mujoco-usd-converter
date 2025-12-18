# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib

from pxr import Sdf, Usd

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestTendons(ConverterTestCase):

    def setUp(self):
        super().setUp()

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
            "mjc:path:divisors",
            "mjc:path:segments",
        ]
        for property in default_tendon.GetPropertiesInNamespace("mjc"):
            if property.GetName() in authored_properties:
                self.assertTrue(self.__has_authored_value(property), f"Property {property.GetName()} is not authored")
            else:
                self.assertFalse(self.__has_authored_value(property), f"Property {property.GetName()} is authored")
