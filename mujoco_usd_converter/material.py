# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil

import mujoco
import usdex.core
from pxr import Gf, Sdf, Tf, Usd, UsdShade

from ._future import Tokens, addAssetContent, addLibraryLayer
from .data import ConversionData
from .numpy import convert_color

__all__ = ["convert_materials"]


def convert_materials(data: ConversionData):
    if not len(data.spec.materials):
        return

    data.libraries[Tokens.Materials] = addLibraryLayer(data.content[Tokens.Contents], Tokens.Materials, format="usdc")
    data.references[Tokens.Materials] = {}

    materials_scope = data.libraries[Tokens.Materials].GetDefaultPrim()
    source_names = [x.name for x in data.spec.materials]
    safe_names = data.name_cache.getPrimNames(materials_scope, source_names)
    for material, source_name, safe_name in zip(data.spec.materials, source_names, safe_names):
        material_prim = __convert_material(materials_scope, safe_name, material, data).GetPrim()
        data.references[Tokens.Materials][source_name] = material_prim
        # FUTURE: specialize from class
        if source_name != safe_name:
            usdex.core.setDisplayName(material_prim, source_name)

    usdex.core.saveStage(data.libraries[Tokens.Materials], comment=f"Material Library for {data.spec.modelname}. {data.comment}")

    # setup a content layer for referenced materials
    data.content[Tokens.Materials] = addAssetContent(data.content[Tokens.Contents], Tokens.Materials, format="usda")


def __convert_material(parent: Usd.Prim, name: str, material: mujoco.MjsMaterial, data: ConversionData) -> UsdShade.Material:
    color, opacity = convert_color(material.rgba)

    # Build kwargs for material properties
    material_kwargs = {
        "color": color,
        "opacity": opacity,
    }

    # Only add roughness if shininess is not the default -1.0
    if material.shininess != -1.0:
        material_kwargs["roughness"] = 1.0 - material.shininess

    # Only add metallic if it's not the default -1.0
    if material.metallic != -1.0:
        material_kwargs["metallic"] = material.metallic

    # FUTURE: use UsdMtlx
    material_prim = usdex.core.definePreviewMaterial(parent, name, **material_kwargs)

    specular_color = material.specular
    # We ignore spec.default.material.specular because materials default specular enabled in MuJoCo
    # but UniversalPreviewSurface defaults to the metalness workflow in USD. We need to know to enable
    # the specular workflow, even at the default specular value.
    if specular_color != 0:
        surface_shader: UsdShade.Shader = usdex.core.computeEffectivePreviewSurfaceShader(material_prim)
        surface_shader.CreateInput("useSpecularWorkflow", Sdf.ValueTypeNames.Int).Set(1)
        surface_shader.CreateInput("specularColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(specular_color))

    emissive_color = material.emission
    if emissive_color != data.spec.default.material.emission:
        surface_shader: UsdShade.Shader = usdex.core.computeEffectivePreviewSurfaceShader(material_prim)
        surface_shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(emissive_color))

    if main_texture_name := material.textures[mujoco.mjtTextureRole.mjTEXROLE_RGB]:
        texture_path: Sdf.AssetPath = __convert_texture(data.spec.texture(main_texture_name), data)
        if texture_path and not usdex.core.addDiffuseTextureToPreviewMaterial(material_prim, texture_path):
            Tf.Warn(f"Failed to add diffuse texture to material prim '{material_prim.GetPrim().GetPath()}'")
    elif any(material.textures):
        # FUTURE: secondary texture layers
        Tf.Warn(f"Unsupported texture layers for material '{name}'")

    # FUTURE: primvars driving surface color and opacity (asset: spot_arm)

    if not material_prim:
        Tf.RaiseRuntimeError(f'Failed to convert material "{name}"')
    return material_prim


def __convert_texture(texture: mujoco.MjsTexture, data: ConversionData) -> Sdf.AssetPath:
    if texture.builtin:
        Tf.Warn(f"Unsupported builtin texture type {mujoco.mjtBuiltin(texture.builtin)} for texture '{texture.name}'")
        return Sdf.AssetPath()
    elif texture.type == mujoco.mjtTexture.mjTEXTURE_2D:
        return __convert_2d_texture(texture, data)
    else:
        Tf.Warn(f"Unsupported texture type {texture.type} for texture '{texture.name}'")
        return Sdf.AssetPath()


def __convert_2d_texture(texture: mujoco.MjsTexture, data: ConversionData) -> Sdf.AssetPath:
    if texture.content_type and texture.content_type != "image/png":
        Tf.Warn(f"Unsupported content type {texture.content_type} for texture '{texture.name}'")
        return Sdf.AssetPath()

    texture_path = pathlib.Path(data.spec.modelfiledir) / pathlib.Path(data.spec.texturedir) / pathlib.Path(texture.file)
    if not texture_path.exists():
        raise Tf.RaiseRuntimeError(f"Texture {texture.name} file {texture_path} does not exist")

    # copy the texture to the payload directory
    local_texture_dir = pathlib.Path(data.libraries[Tokens.Materials].GetRootLayer().identifier).parent / Tokens.Textures
    if not local_texture_dir.exists():
        local_texture_dir.mkdir(parents=True)
    local_texture_path = local_texture_dir / texture_path.name
    shutil.copyfile(texture_path, local_texture_path)
    Tf.Status(f"Copied texture {texture_path} to {local_texture_path}")

    relative_texture_path = local_texture_path.relative_to(pathlib.Path(data.libraries[Tokens.Materials].GetRootLayer().identifier).parent)
    return Sdf.AssetPath(f"./{relative_texture_path.as_posix()}")
