# SPDX-FileCopyrightText: Copyright (c) 2025-2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib
import tempfile
from dataclasses import dataclass

import mujoco
import usdex.core
from pxr import Sdf, Tf, Usd, UsdGeom, UsdPhysics

from ._flatten import export_flattened
from .actuator import convert_actuators
from .body import convert_bodies
from .data import ConversionData, Tokens
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
            model=None,
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
            massUnits=UsdPhysics.MassUnits.kilograms,
            authoringMetadata=get_authoring_metadata(),
        )
        data.content[Tokens.Asset] = asset_stage
        root: Usd.Prim = usdex.core.defineXform(asset_stage, asset_stage.GetDefaultPrim().GetPath()).GetPrim()
        if asset_name != spec.modelname:
            usdex.core.setDisplayName(root, spec.modelname)

        # setup the root layer of the payload
        data.content[Tokens.Contents] = usdex.core.createAssetPayload(asset_stage)

        # author the mesh library
        convert_meshes(data)
        # setup a content layer for referenced meshes
        data.content[Tokens.Geometry] = usdex.core.addAssetContent(data.content[Tokens.Contents], Tokens.Geometry, format="usda")

        # author the material library and setup the content layer for materials only if there are materials
        convert_materials(data)

        # setup a content layer for physics
        data.content[Tokens.Physics] = usdex.core.addAssetContent(data.content[Tokens.Contents], Tokens.Physics, format="usda")
        data.references[Tokens.Physics] = {}

        # author the physics scene
        if self.params.scene:
            convert_scene(data)

        # author the kinematic tree
        convert_bodies(data)

        # author the actuators
        convert_actuators(data)

        # create the asset interface
        usdex.core.addAssetInterface(asset_stage, source=data.content[Tokens.Contents])

        # optionally flatten the asset
        if not self.params.layer_structure:
            asset_identifier = export_flattened(asset_stage, output_dir, asset_dir, asset_stem, asset_format, self.params.comment)
        else:
            usdex.core.saveStage(asset_stage, comment=self.params.comment)

        # warn about known limitations
        self.warn(spec)

        return Sdf.AssetPath(asset_identifier)

    def warn(self, spec: mujoco.MjSpec):
        if spec.cameras:
            Tf.Warn("cameras are not supported")
        if spec.lights:
            Tf.Warn("lights are not supported")
        if spec.keys:
            Tf.Warn("keys are not supported")
        if spec.tendons:
            Tf.Warn("tendons are not supported")
        if spec.flexes:
            Tf.Warn("flexes are not supported")
        if spec.skins:
            Tf.Warn("skins are not supported")
        if spec.equalities:
            Tf.Warn("equalities are not supported")
        if spec.excludes:
            Tf.Warn("excludes are not supported")
        if spec.pairs:
            Tf.Warn("pairs are not supported")
        if spec.sensors:
            Tf.Warn("sensors are not supported")
