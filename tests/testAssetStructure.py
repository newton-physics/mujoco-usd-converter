# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import unittest

import usdex.core
from pxr import Kind, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade

import mujoco_usd_converter


class TestAssetStructure(unittest.TestCase):

    def tearDown(self):
        if pathlib.Path("tests/output").exists():
            shutil.rmtree("tests/output")

    def test_display_name(self):
        model = pathlib.Path("./tests/data/invalid names.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, pathlib.Path(f"./tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        # Test that geoms get proper display names
        body_prim = stage.GetPrimAtPath("/tn__invalidnames_pC/Geometry/tn__Body1_f5")
        self.assertEqual(usdex.core.getDisplayName(body_prim), "Body 1")

        geom_prim = stage.GetPrimAtPath("/tn__invalidnames_pC/Geometry/tn__Body1_f5/tn__Geom1_f5")
        self.assertEqual(usdex.core.getDisplayName(geom_prim), "Geom 1")

        joint_prim = stage.GetPrimAtPath("/tn__invalidnames_pC/Geometry/tn__Body1_f5/tn__Body2_f5/tn__Joint1_h6")
        self.assertEqual(usdex.core.getDisplayName(joint_prim), "Joint 1")

        geometry_library = pathlib.Path(f"./tests/output/{model_name}/Payload/GeometryLibrary.usdc").absolute()
        stage = Usd.Stage.Open(geometry_library.as_posix())
        mesh_prim = stage.GetPrimAtPath("/Geometry/tn__Mesh1_f5")
        self.assertEqual(usdex.core.getDisplayName(mesh_prim), "Mesh 1")

        material_library = pathlib.Path(f"./tests/output/{model_name}/Payload/MaterialsLibrary.usdc").absolute()
        stage = Usd.Stage.Open(material_library.as_posix())
        material_prim = stage.GetPrimAtPath("/Materials/tn__Material1_n9")
        self.assertEqual(usdex.core.getDisplayName(material_prim), "Material 1")

    def test_interface_layer(self):
        model = pathlib.Path("./tests/data/hinge_joints.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        self.assertEqual(stage.GetRootLayer().identifier, pathlib.Path(f"./tests/output/{model_name}/{model_name}.usda").absolute().as_posix())

        # Test stage metrics
        self.assertEqual(UsdGeom.GetStageUpAxis(stage), UsdGeom.Tokens.z)
        self.assertEqual(UsdGeom.GetStageMetersPerUnit(stage), 1.0)
        self.assertEqual(UsdPhysics.GetStageKilogramsPerUnit(stage), 1.0)
        self.assertEqual(usdex.core.getLayerAuthoringMetadata(stage.GetRootLayer()), f"MuJoCo USD Converter v{mujoco_usd_converter.__version__}")

        # Test default prim structure
        default_prim: Usd.Prim = stage.GetDefaultPrim()
        self.assertTrue(default_prim)
        self.assertEqual(default_prim.GetName(), model_name)
        self.assertEqual(default_prim.GetAssetInfoByKey("name"), model_name)

        self.assertEqual(Usd.ModelAPI(default_prim).GetKind(), Kind.Tokens.component)

        self.assertTrue(default_prim.HasAPI(UsdGeom.ModelAPI))
        self.assertTrue(UsdGeom.ModelAPI(default_prim).GetExtentsHintAttr().HasAuthoredValue())
        # FUTURE: use validator to check extents

        payloads: Usd.Payloads = default_prim.GetPayloads()
        self.assertTrue(payloads)

    def test_prim_stack(self):
        model = pathlib.Path("./tests/data/physics_materials.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        parent_path = pathlib.Path(asset.path).parent
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        prim_stack: list[Sdf.PrimSpec] = stage.GetDefaultPrim().GetPrimStack()
        self.assertEqual(len(prim_stack), 5)

        interface_spec: Sdf.PrimSpec = prim_stack[0]
        contents_spec: Sdf.PrimSpec = prim_stack[1]
        physics_spec: Sdf.PrimSpec = prim_stack[2]
        materials_spec: Sdf.PrimSpec = prim_stack[3]
        geometry_spec: Sdf.PrimSpec = prim_stack[4]

        self.assertEqual(interface_spec.layer.identifier, asset.path)
        self.assertEqual(contents_spec.layer.identifier, (parent_path / pathlib.Path("./Payload/Contents.usda")).as_posix())
        self.assertEqual(physics_spec.layer.identifier, (parent_path / pathlib.Path("./Payload/Physics.usda")).as_posix())
        self.assertEqual(materials_spec.layer.identifier, (parent_path / pathlib.Path("./Payload/Materials.usda")).as_posix())
        self.assertEqual(geometry_spec.layer.identifier, (parent_path / pathlib.Path("./Payload/Geometry.usda")).as_posix())

    def test_prim_stack_no_materials(self):
        model = pathlib.Path("./tests/data/hinge_joints.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        parent_path = pathlib.Path(asset.path).parent
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        prim_stack: list[Sdf.PrimSpec] = stage.GetDefaultPrim().GetPrimStack()
        self.assertEqual(len(prim_stack), 4)

        interface_spec: Sdf.PrimSpec = prim_stack[0]
        contents_spec: Sdf.PrimSpec = prim_stack[1]
        physics_spec: Sdf.PrimSpec = prim_stack[2]
        geometry_spec: Sdf.PrimSpec = prim_stack[3]

        self.assertEqual(interface_spec.layer.identifier, asset.path)
        self.assertEqual(contents_spec.layer.identifier, (parent_path / pathlib.Path("./Payload/Contents.usda")).as_posix())
        self.assertEqual(physics_spec.layer.identifier, (parent_path / pathlib.Path("./Payload/Physics.usda")).as_posix())
        self.assertEqual(geometry_spec.layer.identifier, (parent_path / pathlib.Path("./Payload/Geometry.usda")).as_posix())
        self.assertFalse((parent_path / pathlib.Path("./Payload/Materials.usda")).exists())

    def test_contents_layer(self):
        model = pathlib.Path("./tests/data/physics_materials.xml")
        model_name = pathlib.Path(model).stem
        mujoco_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))

        contents_layer_path = pathlib.Path(f"./tests/output/{model_name}/Payload/Contents.usda").absolute()
        self.assertTrue(contents_layer_path.exists(), msg=f"Contents layer not found at {contents_layer_path}")
        contents_stage: Usd.Stage = Usd.Stage.Open(contents_layer_path.as_posix())

        # Test stage metrics
        self.assertEqual(UsdGeom.GetStageUpAxis(contents_stage), UsdGeom.Tokens.z)
        self.assertEqual(UsdGeom.GetStageMetersPerUnit(contents_stage), 1.0)
        self.assertEqual(UsdPhysics.GetStageKilogramsPerUnit(contents_stage), 1.0)
        self.assertEqual(
            usdex.core.getLayerAuthoringMetadata(contents_stage.GetRootLayer()), f"MuJoCo USD Converter v{mujoco_usd_converter.__version__}"
        )

        # Test default prim structure
        default_prim: Usd.Prim = contents_stage.GetDefaultPrim()
        self.assertTrue(default_prim)
        self.assertEqual(default_prim.GetName(), model_name)

        self.assertEqual(contents_stage.GetRootLayer().subLayerPaths, ["./Physics.usda", "./Materials.usda", "./Geometry.usda"])

    def test_geometry_layer(self):
        model = pathlib.Path("./tests/data/meshes.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        parent_path = pathlib.Path(asset.path).parent

        geometry_layer_path = pathlib.Path(f"./tests/output/{model_name}/Payload/Geometry.usda").absolute()
        self.assertTrue(geometry_layer_path.exists(), msg=f"Geometry layer not found at {geometry_layer_path}")
        geometry_stage: Usd.Stage = Usd.Stage.Open(geometry_layer_path.as_posix())

        # Test stage metrics
        self.assertEqual(UsdGeom.GetStageUpAxis(geometry_stage), UsdGeom.Tokens.z)
        self.assertEqual(UsdGeom.GetStageMetersPerUnit(geometry_stage), 1.0)
        self.assertEqual(UsdPhysics.GetStageKilogramsPerUnit(geometry_stage), 1.0)
        self.assertEqual(
            usdex.core.getLayerAuthoringMetadata(geometry_stage.GetRootLayer()), f"MuJoCo USD Converter v{mujoco_usd_converter.__version__}"
        )

        # Test default prim structure
        default_prim: Usd.Prim = geometry_stage.GetDefaultPrim()
        self.assertTrue(default_prim)
        self.assertEqual(default_prim.GetName(), model_name)

        self.assertEqual(len(geometry_stage.GetDefaultPrim().GetAllChildren()), 1)
        geom_scope = UsdGeom.Scope(geometry_stage.GetDefaultPrim().GetChild("Geometry"))
        self.assertTrue(geom_scope)

        # Test that all descendant prims which are meshes are references
        for prim in geometry_stage.TraverseAll():
            if prim.IsA(UsdGeom.Mesh):
                self.assertTrue(prim.GetReferences(), f"Mesh {prim.GetPath()} should be a reference")
                prim_specs: list[Sdf.PrimSpec] = prim.GetPrimStack()
                self.assertEqual(len(prim_specs), 2)
                self.assertEqual(prim_specs[0].layer.identifier, (parent_path / pathlib.Path("./Payload/Geometry.usda")).as_posix())
                self.assertEqual(prim_specs[0].path, prim.GetPath())
                self.assertEqual(prim_specs[1].layer.identifier, (parent_path / pathlib.Path("./Payload/GeometryLibrary.usdc")).as_posix())
                self.assertEqual(prim_specs[1].path, f"/Geometry/{prim.GetName()}")

    def test_materials_layer(self):
        model = pathlib.Path("./tests/data/physics_materials.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        parent_path = pathlib.Path(asset.path).parent

        materials_layer_path = pathlib.Path(f"./tests/output/{model_name}/Payload/Materials.usda").absolute()
        self.assertTrue(materials_layer_path.exists(), msg=f"Materials layer not found at {materials_layer_path}")
        materials_stage: Usd.Stage = Usd.Stage.Open(materials_layer_path.as_posix())

        # Test stage metrics
        self.assertEqual(UsdGeom.GetStageUpAxis(materials_stage), UsdGeom.Tokens.z)
        self.assertEqual(UsdGeom.GetStageMetersPerUnit(materials_stage), 1.0)
        self.assertEqual(UsdPhysics.GetStageKilogramsPerUnit(materials_stage), 1.0)
        self.assertEqual(
            usdex.core.getLayerAuthoringMetadata(materials_stage.GetRootLayer()), f"MuJoCo USD Converter v{mujoco_usd_converter.__version__}"
        )

        # Test default prim structure
        default_prim: Usd.Prim = materials_stage.GetDefaultPrim()
        self.assertTrue(default_prim)
        self.assertEqual(default_prim.GetName(), model_name)

        self.assertEqual(len(materials_stage.GetDefaultPrim().GetAllChildren()), 2)
        materials_scope = UsdGeom.Scope(materials_stage.GetDefaultPrim().GetChild("Materials"))
        self.assertTrue(materials_scope)

        for prim in materials_scope.GetPrim().GetAllChildren():
            self.assertTrue(prim.IsA(UsdShade.Material), f"Material {prim.GetPath()} should be a material")
            prim_specs: list[Sdf.PrimSpec] = prim.GetPrimStack()
            self.assertEqual(len(prim_specs), 2)
            self.assertEqual(prim_specs[0].layer.identifier, (parent_path / pathlib.Path("./Payload/Materials.usda")).as_posix())
            self.assertEqual(prim_specs[0].path, prim.GetPath())
            self.assertEqual(prim_specs[1].layer.identifier, (parent_path / pathlib.Path("./Payload/MaterialsLibrary.usdc")).as_posix())
            self.assertEqual(prim_specs[1].path, f"/Materials/{prim.GetName()}")

        geom_scope: Usd.Prim = materials_stage.GetDefaultPrim().GetChild("Geometry")
        for prim in Usd.PrimRange(geom_scope, Usd.PrimAllPrimsPredicate):
            # all prims in the geometry scope are overrides in this layer
            self.assertEqual(prim.GetSpecifier(), Sdf.SpecifierOver)
            if prim.HasAPI(UsdShade.MaterialBindingAPI):
                # any prim with a bound material uses a local material binding with all purposes
                self.assertEqual(prim.GetAppliedSchemas(), [UsdShade.Tokens.MaterialBindingAPI])
                material_binding: UsdShade.MaterialBindingAPI = UsdShade.MaterialBindingAPI(prim)
                self.assertEqual(material_binding.GetMaterialPurposes(), [UsdShade.Tokens.allPurpose, UsdShade.Tokens.preview, UsdShade.Tokens.full])
                self.assertEqual(len(material_binding.GetDirectBindingRel().GetTargets()), 1)
                self.assertTrue(str(material_binding.GetDirectBindingRel().GetTargets()[0]).startswith(f"/{model_name}/Materials/"))
            else:
                # any prim without a bound material is a pure over in this layer
                self.assertEqual(prim.GetAppliedSchemas(), [])
                self.assertEqual(prim.GetPropertyNames(), [])

    def test_physics_layer(self):
        model = pathlib.Path("./tests/data/simple_actuator.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        parent_path = pathlib.Path(asset.path).parent

        # kg per unit is authored in the physics layer
        physics_layer_path = pathlib.Path(f"./tests/output/{model_name}/Payload/Physics.usda").absolute()
        self.assertTrue(physics_layer_path.exists(), msg=f"Physics layer not found at {physics_layer_path}")
        physics_stage: Usd.Stage = Usd.Stage.Open(physics_layer_path.as_posix())
        self.assertEqual(UsdPhysics.GetStageKilogramsPerUnit(physics_stage), 1.0)

        # Test stage metrics
        self.assertEqual(UsdGeom.GetStageUpAxis(physics_stage), UsdGeom.Tokens.z)
        self.assertEqual(UsdGeom.GetStageMetersPerUnit(physics_stage), 1.0)
        self.assertEqual(UsdPhysics.GetStageKilogramsPerUnit(physics_stage), 1.0)
        self.assertEqual(
            usdex.core.getLayerAuthoringMetadata(physics_stage.GetRootLayer()), f"MuJoCo USD Converter v{mujoco_usd_converter.__version__}"
        )

        # Test default prim structure
        default_prim: Usd.Prim = physics_stage.GetDefaultPrim()
        self.assertTrue(default_prim)
        self.assertEqual(default_prim.GetName(), model_name)

        self.assertEqual(len(physics_stage.GetDefaultPrim().GetAllChildren()), 2)

        # no visual materials in the physics layer
        materials_scope = UsdGeom.Scope(physics_stage.GetDefaultPrim().GetChild("Materials"))
        self.assertFalse(materials_scope)

        physics_scope: Usd.Prim = physics_stage.GetDefaultPrim().GetChild("Physics")
        self.assertTrue(physics_scope.IsA(UsdGeom.Scope))
        self.assertEqual(len(physics_scope.GetAllChildren()), 2)

        actuator: Usd.Prim = physics_scope.GetChild("position")
        self.assertEqual(actuator.GetSpecifier(), Sdf.SpecifierDef)
        self.assertTrue(actuator.IsA("MjcActuator"))
        self.assertEqual(actuator.GetAppliedSchemas(), [])
        self.assertEqual(actuator.GetAllChildren(), [])

        physics_material: Usd.Prim = physics_scope.GetChild("PhysicsMaterial")
        self.assertEqual(physics_material.GetSpecifier(), Sdf.SpecifierDef)
        self.assertTrue(physics_material.IsA(UsdShade.Material))
        self.assertEqual(physics_material.GetAppliedSchemas(), [UsdPhysics.Tokens.PhysicsMaterialAPI, "MjcMaterialAPI"])
        # physics materials are not references (visual materials are references)
        prim_specs: list[Sdf.PrimSpec] = physics_material.GetPrimStack()
        self.assertEqual(len(prim_specs), 1)
        self.assertEqual(prim_specs[0].layer.identifier, (parent_path / pathlib.Path("./Payload/Physics.usda")).as_posix())
        self.assertEqual(prim_specs[0].path, physics_material.GetPath())

        # Test the sidecar PhysicsScene prim
        physics_scene = UsdPhysics.Scene(physics_stage.GetPseudoRoot().GetChild("PhysicsScene"))
        self.assertTrue(physics_scene)
        self.assertEqual(physics_scene.GetPrim().GetAllChildren(), [])

    def test_physics_does_not_leak(self):

        def check_layer(model_name: str):
            model = pathlib.Path(f"./tests/data/{model_name}.xml")
            mujoco_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))

            for layer in pathlib.Path(f"./tests/output/{model_name}/Payload").iterdir():
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

    def test_physics_scene(self):
        model = pathlib.Path("./tests/data/hinge_joints.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))

        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        physics_scene: UsdPhysics.Scene = UsdPhysics.Scene(stage.GetPseudoRoot().GetChild("PhysicsScene"))
        self.assertTrue(physics_scene)
        self.assertEqual(physics_scene.GetPrim().GetAppliedSchemas(), [Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsSceneAPI")])
        self.assertEqual(physics_scene.GetGravityDirectionAttr().Get(), (0, 0, -1))
        self.assertAlmostEqual(physics_scene.GetGravityMagnitudeAttr().Get(), 9.81, 6)

    def test_no_layer_structure_material_texture(self):
        # Test --no-layer-structure with material and textures
        model = pathlib.Path("./tests/data/materials.xml")
        model_name = model.stem
        output_dir = pathlib.Path(f"./tests/output/{model_name}_no_layer_structure")
        usdc_path = output_dir / f"{model_name}.usdc"
        textures_dir = output_dir / "Textures"
        texture_file = textures_dir / "grid.png"

        # convert without layer structure
        mujoco_usd_converter.Converter(layer_structure=False).convert(model, output_dir)

        # check usdc and texture
        self.assertTrue(usdc_path.exists(), f"{usdc_path} not found")
        self.assertTrue(texture_file.exists(), f"{texture_file} not found")

        # check Shader prim inputs:file
        stage = Usd.Stage.Open(str(usdc_path))
        material_prim = stage.GetPrimAtPath("/materials/Materials/Grid")
        self.assertTrue(material_prim)
        shader = usdex.core.computeEffectivePreviewSurfaceShader(UsdShade.Material(material_prim))
        self.assertTrue(shader)

        texture_input: UsdShade.Input = shader.GetInput("diffuseColor")
        connected_source = texture_input.GetConnectedSource()
        texture_prim = connected_source[0].GetPrim()
        texture_file_attr = texture_prim.GetAttribute("inputs:file")
        self.assertEqual(texture_file_attr.Get().path, "./Textures/grid.png")
