# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import tempfile
from dataclasses import dataclass

import mujoco
import usdex.core
from pxr import Sdf, Tf, Usd, UsdGeom, UsdPhysics

from ._future import Tokens, addAssetContent, addAssetInterface, createAssetContents
from .body import convert_bodies
from .data import ConversionData
from .material import convert_materials
from .mesh import convert_meshes
from .scene import convert_scene
from .utils import get_authoring_metadata

__all__ = ["Converter"]


class Converter:
    @dataclass
    class Params:
        layer_structure: bool = True
        scene: bool = True
        comment: str = ""

    def __init__(self, layer_structure: bool = True, scene: bool = True, comment: str = ""):
        self.params = self.Params(layer_structure=layer_structure, scene=scene, comment=comment)

    def convert(self, input_file: str, output_dir: str) -> Sdf.AssetPath:
        """
        Convert a MuJoCo model to a USD stage.

        Args:
            input_file: Path to the input MJCF file.
            output_dir: Path to the output USD directory.

        Returns:
            The path to the created USD asset.

        Raises:
            ValueError: If input_file does not exist or is not a readable file.
            ValueError: If input_file cannot be parsed as a valid MJCF.
            ValueError: If output_dir exists but is not a directory.
        """
        input_path = pathlib.Path(input_file)
        if not input_path.exists() or not input_path.is_file():
            raise ValueError(f"Input file {input_file} is not a readable file")

        output_path = pathlib.Path(output_dir)
        if output_path.exists() and not output_path.is_dir():
            raise ValueError(f"Output directory {output_dir} is not a directory")

        if not output_path.exists():
            output_path.mkdir(parents=True)

        Tf.Status(f"Converting {input_path} into {output_path}")
        spec = mujoco.MjSpec.from_file(str(input_path.absolute()))

        # Create the conversion data object
        data = ConversionData(
            spec=spec,
            content={},
            libraries={},
            references={},
            name_cache=usdex.core.NameCache(),
            scene=self.params.scene,
            comment=self.params.comment,
        )

        # setup the main output layer (which will become an asset interface later)
        if not self.params.layer_structure:
            asset_dir = tempfile.mkdtemp()
            asset_format = "usdc"
        else:
            asset_dir = output_path.absolute().as_posix()
            asset_format = "usda"
        asset_stem = f"{spec.modelname}"
        asset_identifier = f"{asset_dir}/{asset_stem}.{asset_format}"
        asset_name = usdex.core.getValidPrimName(spec.modelname)
        asset_stage = usdex.core.createStage(
            asset_identifier,
            defaultPrimName=asset_name,
            upAxis=UsdGeom.Tokens.z,
            linearUnits=UsdGeom.LinearUnits.meters,
            authoringMetadata=get_authoring_metadata(),
        )
        data.content[Tokens.Asset] = asset_stage
        data.content[Tokens.Asset].SetMetadata(UsdPhysics.Tokens.kilogramsPerUnit, 1)
        root: Usd.Prim = usdex.core.defineXform(asset_stage, asset_stage.GetDefaultPrim().GetPath()).GetPrim()
        if asset_name != spec.modelname:
            usdex.core.setDisplayName(root, spec.modelname)

        # setup the root layer of the payload
        data.content[Tokens.Contents] = createAssetContents(asset_stage)

        # author the mesh library
        convert_meshes(data)
        # setup a content layer for referenced meshes
        data.content[Tokens.Geometry] = addAssetContent(data.content[Tokens.Contents], Tokens.Geometry, format="usda")

        # author the material library and setup the content layer for materials only if there are materials
        convert_materials(data)

        # setup a content layer for physics
        data.content[Tokens.Physics] = addAssetContent(data.content[Tokens.Contents], Tokens.Physics, format="usda", createScope=False)
        data.content[Tokens.Physics].SetMetadata(UsdPhysics.Tokens.kilogramsPerUnit, 1)

        # author the physics scene
        if self.params.scene:
            convert_scene(data)

        # FUTURE: author the keyframes with MjcPhysicsKeyframe

        # author the kinematic tree
        convert_bodies(data)

        # create the asset interface
        addAssetInterface(asset_stage, source=data.content[Tokens.Contents])

        # optionally flatten the asset
        if not self.params.layer_structure:
            layer: Sdf.Layer = asset_stage.Flatten()
            asset_identifier = f"{output_path.absolute().as_posix()}/{asset_stem}.{asset_format}"
            usdex.core.exportLayer(layer, asset_identifier, get_authoring_metadata(), comment=self.params.comment)
            # TODO: relocate textures to the output directory
            shutil.rmtree(asset_dir, ignore_errors=True)
        else:
            usdex.core.saveStage(asset_stage, comment=self.params.comment)

        return Sdf.AssetPath(asset_identifier)
