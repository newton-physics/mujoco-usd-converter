# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import unittest

import usdex.core
from pxr import Sdf, Usd, UsdPhysics

import mjc_usd_converter


class TestAssetStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # this needs to be done in the first test, which is currently this file as the tests are run in alphabetical order
        # FUTURE: refactor to a base class
        usdex.core.activateDiagnosticsDelegate()

    def tearDown(self):
        if pathlib.Path("tests/output").exists():
            shutil.rmtree("tests/output")

    def test_interface_layer(self):
        model = pathlib.Path("./tests/data/hinge_joints.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        self.assertEqual(stage.GetRootLayer().identifier, pathlib.Path(f"./tests/output/{model_name}/{model_name}.usda").absolute().as_posix())
        # FUTURE: Test contents of the interface layer

    # FUTURE: Add tests for the other layers

    def test_physics_layer(self):
        model = pathlib.Path("./tests/data/hinge_joints.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        # kg per unit is authored in the physics layer
        physics_layer_path = pathlib.Path(f"./tests/output/{model_name}/payload/Physics.usda").absolute()
        self.assertTrue(physics_layer_path.exists(), msg=f"Physics layer not found at {physics_layer_path}")
        physics_stage: Usd.Stage = Usd.Stage.Open(physics_layer_path.as_posix())
        self.assertEqual(UsdPhysics.GetStageKilogramsPerUnit(physics_stage), 1.0)

        # kg per unit is authored in the interface layer
        self.assertEqual(UsdPhysics.GetStageKilogramsPerUnit(stage), 1.0)

    def test_physics_does_not_leak(self):

        def check_layer(model_name: str):
            model = pathlib.Path(f"./tests/data/{model_name}.xml")
            mjc_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))

            for layer in pathlib.Path(f"./tests/output/{model_name}/payload").iterdir():
                if layer.is_dir():
                    continue
                if layer.name in ("Contents.usda", "Physics.usda"):
                    continue

                stage: Usd.Stage = Usd.Stage.Open(layer.as_posix())
                for prim in stage.Traverse():
                    for schema in prim.GetAppliedSchemas():
                        self.assertFalse(
                            "Physics" in schema,
                            f"Prim {prim.GetPath()} in {layer.name} layer should not have Physics schemas, but found {schema}",
                        )
                    for prop in prim.GetProperties():
                        self.assertNotEqual(
                            prop.GetNamespace(),
                            "physics",
                            f"Prim {prim.GetPath()} in {layer.name} layer should not have physics properties, but found {prop.GetName()}",
                        )

        check_layer("hinge_joints")  # has bodies and joints and geoms
        check_layer("materials")  # has textured materials
        check_layer("meshes")  # has mesh geoms
