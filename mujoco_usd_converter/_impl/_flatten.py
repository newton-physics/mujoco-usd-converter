# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import tempfile

import usdex.core
from pxr import Sdf, Tf, Usd, UsdShade

from .data import Tokens
from .utils import get_authoring_metadata


def export_flattened(asset_stage: Usd.Stage, output_dir: str, asset_dir: str, asset_stem: str, asset_format: str, comment: str):
    output_path = pathlib.Path(output_dir)
    layer: Sdf.Layer = asset_stage.Flatten()
    asset_identifier = f"{output_path.absolute().as_posix()}/{asset_stem}.{asset_format}"
    usdex.core.exportLayer(layer, asset_identifier, get_authoring_metadata(), comment)

    # fix all PreviewMaterial inputs:file to ./Textures/xxx
    stage = Usd.Stage.Open(asset_identifier)
    for prim in stage.Traverse():
        if prim.IsA(UsdShade.Shader):
            shader = UsdShade.Shader(prim)
            file_input = shader.GetInput("file")
            if file_input and file_input.Get() is not None:
                file_path = pathlib.Path(file_input.Get().path if hasattr(file_input.Get(), "path") else file_input.Get())
                tmpdir = pathlib.Path(tempfile.gettempdir())
                if file_path.is_relative_to(tmpdir):
                    new_path = f"./{Tokens.Textures}/{file_path.name}"
                    file_input.Set(Sdf.AssetPath(new_path))
    stage.Save()
    # copy texture to output dir
    temp_textures_dir = pathlib.Path(asset_dir) / Tokens.Payload / Tokens.Textures
    output_textures_dir = output_path / Tokens.Textures
    if temp_textures_dir.exists() and temp_textures_dir.is_dir():
        if output_textures_dir.exists():
            shutil.rmtree(output_textures_dir)
        shutil.copytree(temp_textures_dir, output_textures_dir)
        Tf.Status(f"Copied textures from {temp_textures_dir} to {output_textures_dir}")

    shutil.rmtree(asset_dir, ignore_errors=True)
