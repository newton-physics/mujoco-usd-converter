# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import mujoco
import numpy as np
import usdex.core
from pxr import Gf, Tf, Usd, UsdGeom, UsdPhysics, UsdShade, Vt

from ._future import Tokens, defineRelativeReference
from .data import ConversionData
from .numpy import convert_color
from .utils import get_fromto_vectors, set_purpose, set_schema_attribute, set_transform

__all__ = ["convert_geom", "get_geom_name"]


def get_geom_name(geom: mujoco.MjsGeom) -> str:
    if geom.name:
        return geom.name

    if geom.type == mujoco.mjtGeom.mjGEOM_MESH:
        return geom.meshname or UsdGeom.Tokens.Mesh
    elif geom.type == mujoco.mjtGeom.mjGEOM_PLANE:
        return UsdGeom.Tokens.Plane
    elif geom.type == mujoco.mjtGeom.mjGEOM_SPHERE:
        return UsdGeom.Tokens.Sphere
    elif geom.type == mujoco.mjtGeom.mjGEOM_BOX:
        return "Box"  # USD uses Cube
    elif geom.type == mujoco.mjtGeom.mjGEOM_CYLINDER:
        return UsdGeom.Tokens.Cylinder
    elif geom.type == mujoco.mjtGeom.mjGEOM_CAPSULE:
        return UsdGeom.Tokens.Capsule
    elif geom.type == mujoco.mjtGeom.mjGEOM_ELLIPSOID:
        return "Ellipsoid"
    elif geom.type == mujoco.mjtGeom.mjGEOM_HFIELD:
        return "HField"
    elif geom.type == mujoco.mjtGeom.mjGEOM_SDF:
        return "SDF"
    else:
        Tf.Warn(f"Unsupported or unknown geom type {geom.type}")
        return ""


def convert_geom(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Gprim:
    source_name = get_geom_name(geom)
    if geom.type == mujoco.mjtGeom.mjGEOM_MESH:
        geom_prim = __convert_mesh(parent, name, geom, data)
    elif geom.type == mujoco.mjtGeom.mjGEOM_PLANE:
        geom_prim = __convert_plane(parent, name, geom, data)
    elif geom.type == mujoco.mjtGeom.mjGEOM_SPHERE:
        geom_prim = __convert_sphere(parent, name, geom, data)
    elif geom.type == mujoco.mjtGeom.mjGEOM_BOX:
        geom_prim = __convert_box(parent, name, geom, data)
    elif geom.type == mujoco.mjtGeom.mjGEOM_CYLINDER:
        geom_prim = __convert_cylinder(parent, name, geom, data)
    elif geom.type == mujoco.mjtGeom.mjGEOM_CAPSULE:
        geom_prim = __convert_capsule(parent, name, geom, data)
    else:
        Tf.Warn(f"Unsupported or unknown geom type {geom.type} for geom '{source_name}'")
        return Usd.Prim()

    # FUTURE: specialize from class (asset: spot (type, group, scale, pos), shadow_hand (type, material, group, scale), barkour (rgba))

    set_purpose(geom_prim, geom.group)
    set_transform(geom_prim, geom, data.spec)
    if source_name and geom_prim.GetPrim().GetName() != source_name:
        usdex.core.setDisplayName(geom_prim.GetPrim(), source_name)

    if geom.material:
        __bind_material(geom_prim, geom.material, data)

    # set color and opacity primvars when they are not the default
    if not np.array_equal(geom.rgba, data.spec.default.geom.rgba):
        color, opacity = convert_color(geom.rgba)
        usdex.core.Vec3fPrimvarData(UsdGeom.Tokens.constant, Vt.Vec3fArray([color])).setPrimvar(geom_prim.CreateDisplayColorPrimvar())
        usdex.core.FloatPrimvarData(UsdGeom.Tokens.constant, Vt.FloatArray([opacity])).setPrimvar(geom_prim.CreateDisplayOpacityPrimvar())

    if not isinstance(geom, mujoco.MjsSite):
        __apply_physics(geom_prim, geom, data)

    return geom_prim


def __convert_mesh(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Mesh:
    ref_mesh: Usd.Prim = data.references[Tokens.Geometry].get(geom.meshname)
    if not ref_mesh:
        Tf.RaiseRuntimeError(f"Mesh '{geom.meshname}' not found in Geometry Library {data.libraries[Tokens.Geometry].GetRootLayer().identifier}")
    prim = defineRelativeReference(parent, ref_mesh, name)
    # the reference mesh may have an invalid source name, and thus a display name
    # however, the prim name may already be valid and override this, in which case
    # we need to block the referenced display name
    if prim.GetPrim().GetName() != ref_mesh.GetPrim().GetName():
        usdex.core.blockDisplayName(prim.GetPrim())
    return UsdGeom.Mesh(prim)


def __convert_plane(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Plane:
    plane: UsdGeom.Plane = UsdGeom.Plane.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    half_width = geom.size[0]
    half_length = geom.size[1]
    # special case for infinite plane in MuJoCo, we need to set a reasonable width and length for USD
    # note that for UsdPhysics the plane is treated as infinite regardless, this is just for visualization
    if half_width == 0:
        half_width = UsdGeom.GetStageMetersPerUnit(parent.GetStage()) * 10
    if half_length == 0:
        half_length = UsdGeom.GetStageMetersPerUnit(parent.GetStage()) * 10
    plane.GetWidthAttr().Set(half_width * 2)
    plane.GetLengthAttr().Set(half_length * 2)
    plane.CreateExtentAttr().Set(UsdGeom.Boundable.ComputeExtentFromPlugins(plane, Usd.TimeCode.Default()))
    return plane


def __convert_sphere(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Sphere:
    sphere: UsdGeom.Sphere = UsdGeom.Sphere.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    sphere.GetRadiusAttr().Set(geom.size[0])
    sphere.CreateExtentAttr().Set(UsdGeom.Boundable.ComputeExtentFromPlugins(sphere, Usd.TimeCode.Default()))
    # FUTURE: mesh/fitscale
    if hasattr(geom, "meshname") and geom.meshname:
        Tf.Warn(f"Sphere '{name}' has incorrect size. It needs to be scaled to fit '{geom.meshname}'")
    return sphere


def __convert_box(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Cube:
    start, end = get_fromto_vectors(geom)
    # FUTURE: mesh/fitscale
    if hasattr(geom, "meshname") and geom.meshname:
        Tf.Warn(f"Box '{name}' has incorrect size. It needs to be scaled to fit '{geom.meshname}'")
    if start is not None and end is not None:
        width = length = geom.size[0]
        height = (end - start).GetLength() / 2.0
    else:
        width = geom.size[0]
        length = geom.size[1]
        height = geom.size[2]

    cube: UsdGeom.Cube = UsdGeom.Cube.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    cube.GetSizeAttr().Set(2)  # author the default explicitly
    scale_op = cube.AddScaleOp()
    scale_op.Set(Gf.Vec3f(width, length, height))
    cube.CreateExtentAttr().Set(UsdGeom.Boundable.ComputeExtentFromPlugins(cube, Usd.TimeCode.Default()))
    return cube


def __convert_cylinder(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Cylinder:
    radius = geom.size[0]
    start, end = get_fromto_vectors(geom)
    # FUTURE: mesh/fitscale
    if hasattr(geom, "meshname") and geom.meshname:
        Tf.Warn(f"Cylinder '{name}' has incorrect size. It needs to be scaled to fit '{geom.meshname}'")
    if start is not None and end is not None:  # noqa: SIM108
        height = (end - start).GetLength()
    else:
        height = geom.size[1] * 2

    cylinder: UsdGeom.Cylinder = UsdGeom.Cylinder.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    cylinder.GetAxisAttr().Set(UsdGeom.Tokens.z)
    cylinder.GetRadiusAttr().Set(radius)
    cylinder.GetHeightAttr().Set(height)
    cylinder.CreateExtentAttr().Set(UsdGeom.Boundable.ComputeExtentFromPlugins(cylinder, Usd.TimeCode.Default()))
    return cylinder


def __convert_capsule(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Capsule:
    radius = geom.size[0]
    start, end = get_fromto_vectors(geom)
    # FUTURE: mesh/fitscale
    if hasattr(geom, "meshname") and geom.meshname:
        Tf.Warn(f"Capsule '{name}' has incorrect size. It needs to be scaled to fit '{geom.meshname}'")
    if start is not None and end is not None:  # noqa: SIM108
        height = (end - start).GetLength()
    else:
        height = geom.size[1] * 2

    capsule: UsdGeom.Capsule = UsdGeom.Capsule.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    capsule.GetAxisAttr().Set(UsdGeom.Tokens.z)
    capsule.GetRadiusAttr().Set(radius)
    capsule.GetHeightAttr().Set(height)
    capsule.CreateExtentAttr().Set(UsdGeom.Boundable.ComputeExtentFromPlugins(capsule, Usd.TimeCode.Default()))
    return capsule


def __bind_material(geom_prim: Usd.Prim, name: str, data: ConversionData):
    local_materials = data.content[Tokens.Materials].GetDefaultPrim().GetChild(Tokens.Materials)
    ref_material: Usd.Prim = data.references[Tokens.Materials].get(name)
    if not ref_material:
        Tf.RaiseRuntimeError(f"Material '{name}' not found in Material Library {data.libraries[Tokens.Materials].GetRootLayer().identifier}")
    material_prim = UsdShade.Material(local_materials.GetChild(ref_material.GetName()))
    if not material_prim:
        material_prim = UsdShade.Material(defineRelativeReference(local_materials, ref_material, ref_material.GetName()))

    # Check if geom_prim is not a USD mesh type
    prim = geom_prim.GetPrim()
    if not prim.IsA(UsdGeom.Mesh):
        # Check if material_prim's diffuseColor is bound to a texture
        has_diffuse_texture = False
        shader = usdex.core.computeEffectivePreviewSurfaceShader(material_prim)
        if shader:
            diffuse_input = shader.GetInput("diffuseColor")
            if diffuse_input:
                value_attrs = diffuse_input.GetValueProducingAttributes()
                for attr in value_attrs:
                    source_prim = attr.GetPrim()
                    if source_prim and source_prim.GetTypeName() == "Shader":
                        shader_type = source_prim.GetAttribute("info:id").Get()
                        if shader_type == "UsdUVTexture":
                            has_diffuse_texture = True
                            break

        if has_diffuse_texture:
            Tf.Warn(
                f"Binding a textured Material '{material_prim.GetPath()}' to a {prim.GetTypeName()} Prim ('{prim.GetPath()}') "
                "will discard textures at render time."
            )

    geom_over = data.content[Tokens.Materials].OverridePrim(geom_prim.GetPath())
    usdex.core.bindMaterial(geom_over, material_prim)


def __apply_physics(geom_prim: Usd.Prim, geom: mujoco.MjsGeom, data: ConversionData):
    # most geom are colliders
    is_collider = True
    collider_enabled = True

    # some geom are for vizualization only, but still contribute to the mass of the body
    if geom.contype == 0 and geom.conaffinity == 0:
        if geom.group in range(data.spec.compiler.inertiagrouprange[0], data.spec.compiler.inertiagrouprange[1] + 1):
            if not np.isnan(geom.mass) or geom.density != data.spec.default.geom.density:
                collider_enabled = False
            else:
                is_collider = False
        else:
            is_collider = False

    if not is_collider:
        # this is a purely visual geom, so we skip physics authoring
        return

    geom_over: Usd.Prim = data.content[Tokens.Physics].OverridePrim(geom_prim.GetPrim().GetPath())

    collider: UsdPhysics.CollisionAPI = UsdPhysics.CollisionAPI.Apply(geom_over)
    if not collider_enabled:
        collider.CreateCollisionEnabledAttr().Set(False)

    geom_over.ApplyAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsCollisionAPI"))

    # Set all MjcCollisionAPI attributes
    set_schema_attribute(geom_over, "mjc:condim", geom.condim)
    set_schema_attribute(geom_over, "mjc:gap", geom.gap)
    set_schema_attribute(geom_over, "mjc:group", geom.group)
    set_schema_attribute(geom_over, "mjc:margin", geom.margin)
    set_schema_attribute(geom_over, "mjc:priority", geom.priority)
    set_schema_attribute(geom_over, "mjc:solimp", list(geom.solimp))
    set_schema_attribute(geom_over, "mjc:solmix", geom.solmix)
    set_schema_attribute(geom_over, "mjc:solref", list(geom.solref))

    if geom.type == mujoco.mjtGeom.mjGEOM_MESH:
        mesh_collider: UsdPhysics.MeshCollisionAPI = UsdPhysics.MeshCollisionAPI.Apply(geom_over)
        mesh_collider.CreateApproximationAttr().Set(UsdPhysics.Tokens.convexHull)
        if inertia := __get_inertia_token(geom, data):
            geom_over.ApplyAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsMeshCollisionAPI"))
            set_schema_attribute(geom_over, "mjc:inertia", inertia)
        if maxhullvert := __get_maxhullvert(geom, data):
            geom_over.ApplyAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsMeshCollisionAPI"))
            set_schema_attribute(geom_over, "mjc:maxhullvert", maxhullvert)
    else:
        set_schema_attribute(geom_over, "mjc:shellinertia", bool(geom.typeinertia == mujoco.mjtGeomInertia.mjINERTIA_SHELL))

    if not np.isnan(geom.mass):
        geom_mass: UsdPhysics.MassAPI = UsdPhysics.MassAPI.Apply(geom_over)
        geom_mass.CreateMassAttr().Set(geom.mass)

    if geom.density != data.spec.default.geom.density:
        geom_mass: UsdPhysics.MassAPI = UsdPhysics.MassAPI.Apply(geom_over)
        geom_mass.CreateDensityAttr().Set(geom.density)

    physics_material: UsdPhysics.MaterialAPI = __acquire_physics_material(geom_over, geom, data)
    if physics_material:
        UsdShade.MaterialBindingAPI.Apply(geom_over).Bind(physics_material, materialPurpose="physics")

    # FUTURE: collision filtering


def __acquire_physics_material(geom_prim: Usd.Prim, geom: mujoco.MjsGeom, data: ConversionData) -> UsdShade.Material:
    sliding_friction = geom.friction[0]
    torsional_friction = geom.friction[1]
    rolling_friction = geom.friction[2]
    material_hash = Gf.Vec3f(sliding_friction, torsional_friction, rolling_friction)

    # check for an existing physics material with the same values
    physics_scope = data.content[Tokens.Physics].GetDefaultPrim().GetChild(Tokens.Physics)
    for child in physics_scope.GetChildren():
        if child.HasAPI(UsdPhysics.MaterialAPI):
            physics_material: UsdPhysics.MaterialAPI = UsdPhysics.MaterialAPI(child.GetPrim())
            if Gf.IsClose(material_hash, __hash_physics_material(physics_material), 1e-6):
                return UsdShade.Material(physics_material)

    return __create_physics_material(physics_scope, geom, data)


def __create_physics_material(physics_materials: Usd.Prim, geom: mujoco.MjsGeom, data: ConversionData) -> UsdShade.Material:
    sliding_friction = geom.friction[0]
    torsional_friction = geom.friction[1]
    rolling_friction = geom.friction[2]

    material: UsdShade.Material = usdex.core.createMaterial(physics_materials, data.name_cache.getPrimName(physics_materials, "PhysicsMaterial"))
    physics_material: UsdPhysics.MaterialAPI = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
    physics_material.CreateDynamicFrictionAttr().Set(sliding_friction)

    # Apply MjcMaterialAPI for torsional and rolling friction
    material.GetPrim().ApplyAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsMaterialAPI"))
    set_schema_attribute(material.GetPrim(), "mjc:torsionalfriction", torsional_friction)
    set_schema_attribute(material.GetPrim(), "mjc:rollingfriction", rolling_friction)

    return material


def __hash_physics_material(material: UsdPhysics.MaterialAPI) -> Gf.Vec3f:
    # we know that all materials in the physics layer have the values authored, so we can just get them
    sliding_friction = material.GetDynamicFrictionAttr().Get()
    torsional_friction = material.GetPrim().GetAttribute("mjc:torsionalfriction").Get()
    rolling_friction = material.GetPrim().GetAttribute("mjc:rollingfriction").Get()
    return Gf.Vec3f(sliding_friction, torsional_friction, rolling_friction)


def __get_inertia_token(geom: mujoco.MjsGeom, data: ConversionData) -> str:
    if geom.type != mujoco.mjtGeom.mjGEOM_MESH or not geom.meshname:
        return None

    # Find the mesh by name
    mesh = data.spec.mesh(geom.meshname)
    if not mesh:
        return None

    if mesh.inertia == mujoco.mjtMeshInertia.mjMESH_INERTIA_EXACT:
        return "exact"
    elif mesh.inertia == mujoco.mjtMeshInertia.mjMESH_INERTIA_CONVEX:
        return "convex"
    elif mesh.inertia == mujoco.mjtMeshInertia.mjMESH_INERTIA_SHELL:
        return "shell"
    else:
        # explicitly return None for legacy to indicate it should not be applied
        return None


def __get_maxhullvert(geom: mujoco.MjsGeom, data: ConversionData) -> int:
    if geom.type != mujoco.mjtGeom.mjGEOM_MESH or not geom.meshname:
        return None

    # Find the mesh by name
    mesh = data.spec.mesh(geom.meshname)
    if not mesh:
        return None

    return mesh.maxhullvert if mesh.maxhullvert != -1 else None
