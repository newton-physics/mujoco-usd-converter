# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib

import usdex.core
from pxr import Ar, Kind, Sdf, Usd, UsdGeom

# Placeholder for future functions to propose to usdex.core
# N802 will be disabled throughout this file as usdex functions prefer camelCase


def getLayerAuthoringMetadata(layer: Sdf.Layer) -> str:  # noqa: N802
    if usdex.core.hasLayerAuthoringMetadata(layer):
        return layer.customLayerData["creator"]
    return ""


def addAssetInterface(stage: Usd.Stage, source: Usd.Stage) -> None:  # noqa: N802
    usdex.core.configureStage(
        stage,
        defaultPrimName=source.GetDefaultPrim().GetName(),
        upAxis=UsdGeom.GetStageUpAxis(source),
        linearUnits=UsdGeom.GetStageMetersPerUnit(source),
        authoringMetadata=getLayerAuthoringMetadata(source.GetRootLayer()),
    )
    Sdf.CopySpec(source.GetRootLayer(), source.GetDefaultPrim().GetPath(), stage.GetRootLayer(), stage.GetDefaultPrim().GetPath())
    root: Usd.Prim = stage.GetDefaultPrim()

    # Make the payload path relative to the interface directory
    payload_path = getRelativeIdentifier(source.GetRootLayer(), stage.GetRootLayer())
    root.GetPayloads().AddPayload(payload_path)

    # annotate the asset interface
    model: Usd.ModelAPI = Usd.ModelAPI(root)
    model.SetAssetName(usdex.core.computeEffectiveDisplayName(root))
    # FUTURE: add variants interface
    # FUTURE: add primvars interface
    createAssetComponent(root)
    geom_model: UsdGeom.ModelAPI = UsdGeom.ModelAPI.Apply(root)
    geom_model.SetExtentsHint(
        geom_model.ComputeExtentsHint(UsdGeom.BBoxCache(Usd.TimeCode.Default(), UsdGeom.Imageable(root).GetOrderedPurposeTokens()))
    )


def createAssetContents(asset_stage: Usd.Stage) -> Usd.Stage:  # noqa: N802
    resolver: Ar.Resolver = Ar.GetResolver()
    contents_stage: Usd.Stage = usdex.core.createStage(
        resolver.CreateIdentifier(f"./payload/{Tokens.Contents}.usda", resolver.Resolve(asset_stage.GetRootLayer().identifier)),
        defaultPrimName=asset_stage.GetDefaultPrim().GetName(),
        upAxis=UsdGeom.GetStageUpAxis(asset_stage),
        linearUnits=UsdGeom.GetStageMetersPerUnit(asset_stage),
        authoringMetadata=getLayerAuthoringMetadata(asset_stage.GetRootLayer()),
    )
    Sdf.CopySpec(
        asset_stage.GetRootLayer(),
        asset_stage.GetDefaultPrim().GetPath(),
        contents_stage.GetRootLayer(),
        contents_stage.GetDefaultPrim().GetPath(),
    )
    return contents_stage


def addAssetContent(  # noqa: N802
    stage: Usd.Stage,
    name: str,
    format: str = "usdc",
    prepend: bool = True,
    createScope: bool = True,  # noqa: N803
) -> Usd.Stage:
    resolver: Ar.Resolver = Ar.GetResolver()
    relative_identifier = f"./{name}.{format}"
    identifier = resolver.CreateIdentifier(relative_identifier, resolver.Resolve(stage.GetRootLayer().identifier))
    new_stage: Usd.Stage = usdex.core.createStage(
        identifier,
        defaultPrimName=stage.GetDefaultPrim().GetName(),
        upAxis=UsdGeom.GetStageUpAxis(stage),
        linearUnits=UsdGeom.GetStageMetersPerUnit(stage),
        authoringMetadata=getLayerAuthoringMetadata(stage.GetRootLayer()),
    )
    if prepend:
        stage.GetRootLayer().subLayerPaths.insert(0, relative_identifier)
    else:
        stage.GetRootLayer().subLayerPaths.append(relative_identifier)
    Sdf.CopySpec(stage.GetRootLayer(), stage.GetDefaultPrim().GetPath(), new_stage.GetRootLayer(), new_stage.GetDefaultPrim().GetPath())
    if createScope:
        defineScope(new_stage.GetDefaultPrim(), name)
    return new_stage


class Tokens:
    Asset = "Asset"
    Library = "Library"
    Classes = "Classes"
    Contents = "Contents"
    Geometry = "Geometry"
    Materials = "Materials"
    Textures = "Textures"
    Physics = "Physics"


def defineScope(parent: Usd.Prim, name: str) -> Usd.Prim:  # noqa: N802
    prim = UsdGeom.Scope.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    return prim


def createLibraryPrim(parent: Usd.Prim, name: str) -> Usd.Prim:  # noqa: N802
    prim: Usd.Prim = defineScope(parent, name).GetPrim()
    prim.SetSpecifier(Sdf.SpecifierClass)
    return prim


def addLibraryLayer(contents_stage: Usd.Stage, name: str, format: str = "usdc") -> Usd.Stage:  # noqa: N802
    resolver: Ar.Resolver = Ar.GetResolver()
    relative_identifier = f"./{name}{Tokens.Library}.{format}"
    identifier = resolver.CreateIdentifier(relative_identifier, resolver.Resolve(contents_stage.GetRootLayer().identifier))
    stage: Usd.Stage = usdex.core.createStage(
        identifier,
        defaultPrimName=usdex.core.getValidPrimName(name),
        upAxis=UsdGeom.GetStageUpAxis(contents_stage),
        linearUnits=UsdGeom.GetStageMetersPerUnit(contents_stage),
        authoringMetadata=getLayerAuthoringMetadata(contents_stage.GetRootLayer()),
    )
    createLibraryPrim(stage.GetPseudoRoot(), name)
    return stage


def createAssetComponent(prim: Usd.Prim):  # noqa: N802
    Usd.ModelAPI(prim).SetKind(Kind.Tokens.component)
    for descendant in Usd.PrimRange(prim):
        if descendant == prim:
            continue

        model: Usd.ModelAPI = Usd.ModelAPI(descendant)
        current_kind = model.GetKind()
        if current_kind == Kind.Tokens.component:
            model.SetKind(Kind.Tokens.subcomponent)
        elif current_kind:
            model.SetKind(None)


def getRelativeIdentifier(layer: Sdf.Layer, anchorLayer: Sdf.Layer) -> str:  # noqa: N802, N803
    return f"./{pathlib.Path(layer.identifier).relative_to(pathlib.Path(anchorLayer.identifier).parent).as_posix()}"


def defineRelativeReference(parent: Usd.Prim, reference: Usd.Prim, name: str | None = None) -> Usd.Prim:  # noqa: N802
    name = name or reference.GetName()
    prim: Usd.Prim = defineScope(parent, name).GetPrim()
    prim.SetSpecifier(reference.GetSpecifier())
    prim.SetTypeName(reference.GetTypeName())
    relative_identifier = getRelativeIdentifier(reference.GetStage().GetRootLayer(), parent.GetStage().GetRootLayer())
    prim.GetReferences().AddReference(relative_identifier, reference.GetPath())
    return prim
