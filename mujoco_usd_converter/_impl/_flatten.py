# SPDX-FileCopyrightText: Copyright (c) 2025-2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import tempfile

import usdex.core
from pxr import Sdf, Tf, Usd

from .data import Tokens
from .utils import get_authoring_metadata


def export_flattened(asset_stage: Usd.Stage, output_dir: str, asset_dir: str, asset_stem: str, asset_format: str, comment: str) -> str:
    output_path = pathlib.Path(output_dir)
    layer: Sdf.Layer = asset_stage.Flatten()

    # Flattening resolves texture paths into the temporary payload directory. PBR materials also leave the path authored on their
    # UsdPreviewSurface texture shaders, beneath instanceable materials that cannot be edited on a stage, so they are anchored in the layer.
    tmpdir = pathlib.Path(tempfile.gettempdir())

    def anchor_texture_path(path: Sdf.Path):
        if not path.IsPropertyPath():
            return
        attr: Sdf.AttributeSpec = layer.GetAttributeAtPath(path)
        if attr and attr.typeName == Sdf.ValueTypeNames.Asset and attr.HasDefaultValue():
            file_path = pathlib.Path(attr.default.path)
            if file_path.is_relative_to(tmpdir):
                attr.default = Sdf.AssetPath(f"./{Tokens.Textures}/{file_path.name}")

    layer.Traverse(Sdf.Path.absoluteRootPath, anchor_texture_path)

    asset_identifier = f"{output_path.absolute().as_posix()}/{asset_stem}.{asset_format}"
    usdex.core.exportLayer(layer, asset_identifier, get_authoring_metadata(), comment)

    # copy texture to output dir
    temp_textures_dir = pathlib.Path(asset_dir) / Tokens.Payload / Tokens.Textures
    output_textures_dir = output_path / Tokens.Textures
    if temp_textures_dir.exists() and temp_textures_dir.is_dir():
        if output_textures_dir.exists():
            shutil.rmtree(output_textures_dir)
        shutil.copytree(temp_textures_dir, output_textures_dir)
        Tf.Status(f"Copied textures from {temp_textures_dir} to {output_textures_dir}")

    shutil.rmtree(asset_dir, ignore_errors=True)
    return asset_identifier
