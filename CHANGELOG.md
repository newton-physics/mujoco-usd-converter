# 0.1.0.a1

## Features

- **USD Asset Structure**
  - Output Assets are completely standalone with no dependencies on the source MJCF, OBJ, or STL files
  - Atomic Component structure with Asset Interface layer and payloaded contents
  - Separate geometry, material, and physics content layers for easy asset-reuse across domains
  - Library-based asset references for meshes and materials to avoid heavy data duplication
  - Explicit USD stage metadata with units (meters, kilograms) and up-axis (Z)
- **Body Conversion**
  - MuJoCo bodies are converted as `UsdGeom.Xform` prims with `UsdPhysics.RigidBodyAPI` applied
  - worldbody becomes the `defaultPrim` on the `Usd.Stage`
  - All bodies under the worldbody have `UsdPhysics.ArticulationRootAPI` applied to indicate the root of each kinematic tree
  - Bodies are nested in USD, exactly as in the source MJCF
  - Complete mass properties including explicit inertia & center of mass via `UsdPhysics.MassAPI`
  - Mocap bodies are supported via `UsdPhysics.RigidBodyAPI.kinematicEnabled`
- **Joint Conversion**
  - Hinge joints as `UsdPhysics.RevoluteJoint` with angular limits
  - Slide joints as `UsdPhysics.PrismaticJoint` with linear limits
  - Ball joints as `UsdPhysics.SphericalJoint` with cone angle limits
  - Free joints (bodies are free by default in USD)
  - `UsdPhysics.FixedJoints` for fully constrained parent/child bodies
  - All joints have automatic joint frame alignment between Body0 and Body1, accounting for MuJoCo joint axis, position, and orientation.
  - `MjcJointAPI` is applied to all joints specifying additional properties (e.g. armature, damping, friction loss, spring-damper)
- **Geom Conversion**
  - All visual and collision geometry is converted to USD
    - Visuals are set with `default` UsdPurpose and colliders with `guide` UsdPurpose
  - `UsdPhysics.CollisionAPI` and `MjcCollisionAPI` are applied to colliders
      - Friction is provided via a bound `UsdShade.Material` with `UsdPhysics.MaterialAPI` specifying sliding (dynamic) friction
        and `MjcMaterialAPI` specifying torsional and rolling friction
      - All other MuJoCo collision properties are authored using `MjcCollisionAPI`
  - Meshes as `UsdGeom.Mesh`
    - Automatic mesh library generation with reference-based asset structure, to avoid duplicate topology
    - STL files converted to USD using `numpy-stl` and `usd-exchange` with normal processing
    - OBJ files converted using `tinyobjloader` and `usd-exchange` with UV coordinates and normal mapping
    - `UsdPhysics.MeshCollisionAPI` and `MjcMeshCollisionAPI` applied to mesh colliders with convex hull and inertia attributes
  - Planes as `UsdGeom.Plane` with infinite plane support
  - Spheres as `UsdGeom.Sphere`
  - Boxes as `UsdGeom.Cube` with scale transforms
  - Cylinders as `UsdGeom.Cylinder`
  - Capsules as `UsdGeom.Capsule`
- **Site Conversion**
  - MuJoCo sites are converted as additional geometry prims, with `guide` UsdPurpose and `MjcSiteAPI` applied
- **Visual Material and Texture Conversion**
  - `UsdPreviewSurface` materials with color, opacity, roughness, metallic, specular, and emissive properties
  - PNG texture support with automatic texture copying and path resolution
  - Color and opacity overrides on geometry are handled via `primvars:displayColor` and `primvars:displayOpacity`
- **Simulation Options**
  - Gravity direction and magnitude conversion via `UsdPhysics.Scene`
  - All other MuJoCo options & flags via `MjcSceneAPI` applied on the `UsdPhysics.Scene`
- **Prim Naming**
  - If MuJoCo names are not valid USD specifiers the are automatically transcoded & made unique & valid
  - Display name metadata preserves the original MuJoCo element names on the USD Prims
- **Command Line Interface**
  - Input is an MJCF file and default output is a USD Layer as a structured Atomic Component with an Asset Interface USDA layer
    - All heavy data is compressed binary data (via USDC layers) while lightweight data is plain text for legibility
  - Optional comment string embedded into all authored USD Layers
  - Optional Stage flattening for single-file output
  - Optionally skip the `UsdPhysics.Scene` (this may be desirable for multi-asset setups)
  - Error handling with graceful failures
  - Enable verbose output for debugging (exposes any traceback info)
- **Python API**
  - Full programmatic access via `mjc_usd_converter.Converter` class with configurable parameters for all CLI flags
  - Enables interactive editing of the MJCF data before conversion or of the USD Layers after conversion

## Release Blockers

- (NV/GDM) Authoring PhysicsScene with MjcSceneAPI causes MuJoCo Simulate to SEGFAUILT
  - GDM cannot repro
- (GDM) MjcTransmission being renamed to MjcActuator
- (GDM) MjcSceneAPI is missing critical compiler settings
- (NV) MjcActuator support is not implemented (WIP but no MR)
- (NV) Texture handling for unnamed textures is not supported
- (NV) Command line argument validation is not implemented (OSEC SRD REQ)
- (NV) Texture relocation during flattening is not implemented
- (NV) Geometry content layers use USDA format instead of USDC (might be ok, just need to decide)
- (NV) MJC schema version is not pinned to a specific tag or commit, potentially causing compatibility issues

## Known Limitations

### USD Data Conversion

- **USD Asset Structure**
  - The value inheritance provided by MuJoCo's `defaults`, `class`, and `childclass` mechanism is baked down
    - The values are preserved faithfully on the inheriting Prims
    - A more accurate data mapping would use `UsdInherits` composition arcs to preserve modularity
  - MJCF attach, composite, and flexcomp mechanisms are baked down rather than preserved via composition arcs
    - This matches behavior of the MuJoCo parser
- **Body Conversion**
  - Body gravcomp is authored as a custom attribute rather than an official MjcPhysics schema
- **Joint Conversion**
  - Custom user properties on MuJoCo joints are not converted
- **Geom Conversion**
  - Inline XML mesh topology is not implemented for meshes without files
  - For basic geom (e.g cylinders), mesh/fitscale support is not implemented
  - Ellipoid conversion is not implemented
  - Height Field conversion is not implemented
  - Signed Distance Field conversion is not implemented
  - Collision filtering via the `contype` & `conaffinity` algorithm is not implemented
  - Collision filtering via contact/exclude is not implemented
  - Collision property overrides via contact/pair is not implemented
- **Visual Material and Texture Conversion**
  - Secondary texture layers are not supported beyond the main diffuse texture
  - Primvars driving surface color and opacity are not supported
    - Primvars on geometry are supported only when there is no bound visual `UsdShade.Material`
  - More accurate PBR materials (e.g. OpenPBR via UsdMtlx) are not implemented
  - Only standard 2D file textures via texcoord mapping are supported. Texture Patterns or projections are not implemented.
    - This limits some of the more advanced features of the MuJoCo material/texture system, most notably checkerboards on ground planes
- **Frames (extra Transforms)**
  - Single `Frame` elements are supported, but recursive frame support is not implemented
  - All frames are baked down onto the respective body, geom, site transforms rather than introduce intermediate prims
    - This matches behavior of the MuJoCo parser
- **Other Elements**
  - Keyframe authoring via `MjcKeyframe` is not implemented
  - Camera conversion to `UsdGeom.Camera` is not implemented
  - Light conversion to `UsdLux` Prims is not implemented
  - Equality constraint conversion is not implemented
  - Sensor state conversion is not implemented
  - Tendon conversion is not implemented
  - Deformable flex & skin conversion is not implemented
  - The Visual, Statistic, and Size properties which control MuJoCo Simulate's default visualization and interactivity options are not preserved
  - Custom MuJoCo plugins & extensions are not mapped to USD

### Using the USD Asset in MuJoCo Simulate

- The app does not yet load visual geometry or visual materials

### Using the USD Asset in other USD Ecosystem applications

- As with MJCF and `MjSpec`, the USD Asset contains nested rigid bodies within articulations.
  - Existing applications may not support this style of nesting.
  - There is a [proposal](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/82) to adopt this change to the UsdPhysics specification.
