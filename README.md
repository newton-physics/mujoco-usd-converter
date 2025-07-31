# mujoco-usd-converter

# Overview

A [MuJoCo](https://mujoco.org) to [OpenUSD](https://openusd.org) Data Converter

> Important: This is currently an Alpha product. See the [CHANGELOG](./CHANGELOG.md) for features and known limitations.

Key Features:
- Converts an input MJCF file into an OpenUSD Layer
- Supports data conversion of visual geometry & materials, as well as the bodies, collision geometry, sites, joints, and actuators necessary for kinematic simulation.
- Available as a python module or command line interface (CLI).
- Creates a standalone, self-contained artifact with no connection to the source MJCF, OBJ, or STL data.
  - Structured as an [Atomic Component](https://docs.omniverse.nvidia.com/usd/latest/learn-openusd/independent/asset-structure-principles.html#atomic-model-structure-flowerpot)
  - Suitable for visualization & rendering in any OpenUSD Ecosystem application.
  - Suitable for [import & simulation directly in MuJoCo Simulate](#loading-usd-in-mujoco-simulate).

## Menagerie Benchmarks

We run regular benchmarks on the [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie). See the latest results [here](./benchmarks.md).

## Implementation Details & Dependencies

Specific implementation details are based on the "MJC to USD Conceptual Data Mapping" document, which is a collaboration between Google DeepMind and NVIDIA. This document will be made public once the project moves out of the alpha phase.

One important detail is that this document recommends nested rigid bodies within articulations, as it more faithfully matches the kinematic tree in MuJoCo and meets the needs of reduced coordinate solvers. There is an [open proposal](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/82) to adopt this change to the UsdPhysics specification. However, as it is a spec change, existing applications may not support this style of nesting.

The output asset structure is based on NVIDIA's [Principles of Scalable Asset Structure in OpenUSD](https://docs.omniverse.nvidia.com/usd/latest/learn-openusd/independent/asset-structure-principles.html).

The implementation also leverages the following dependencies:
- NVIDIA's [OpenUSD Exchange SDK](https://docs.omniverse.nvidia.com/usd/code-docs/usd-exchange-sdk/latest/index.html) to author consistent & correct USD data.
- Pixar's OpenUSD python modules & native libraries (vendored via the `usd-exchange` wheel).
- Google DeepMind's `mujoco` python module for parsing MJCF into MjSpec
- A codeless version of the [MjcPhysics USD schema](https://mujoco.readthedocs.io/en/latest/OpenUSD/mjcPhysics.html) from MuJoCo to author the MuJoCo specific Prims, Applied APIs, and Attributes.
- [tinyobjloader](https://github.com/tinyobjloader/tinyobjloader) and [numpy-stl](https://numpy-stl.readthedocs.io) for parsing any mesh data referenced by the input MJCF datasets.

# Get Started

To start using the converter, install the python wheel into a virtual environment using your favorite package manager:

```bash
python -m venv /tmp/test
source /tmp/test/bin/activate
python -m pip install mujoco-usd-converter
mujoco_usd_converter /path/to/robot.xml /tmp/usd_robot
```

See `mujoco_usd_converter --help` for CLI arguments.

Alternatively, the same converter functionality can be accessed from the python module directly, which is useful when further transforming the USD data after conversion.

```python
import mujoco_usd_converter
import usdex.core
from pxr import Sdf, Usd

converter = mujoco_usd_converter.Converter()
asset: Sdf.AssetPath = converter.convert("/path/to/robot.xml", "/tmp/usd_robot")
stage: Usd.Stage = Usd.Stage.Open(asset.path)
# modify further using Usd or usdex.core functionality
usdex.core.saveStage(stage, comment="modified after conversion")
```

## Loading the USD Asset

Once your asset is saved to storage, it can be loaded into an OpenUSD Ecosystem application, including a custom build of MuJoCo itself.

We recommend starting with [usdview](https://docs.omniverse.nvidia.com/usd/latest/usdview/index.html), a simple graphics application to confirm the visual geometry & materials are working as expected. You can inspect any of the USD properties in this application, including the UsdPhysics and MjcPhysics properties.

> Tip: [OpenUSD Exchange Samples](https://github.com/NVIDIA-Omniverse/usd-exchange-samples) provides `./usdview.sh` and `.\usdview.bat` commandline tools which bootstrap usdview with the necessary third party dependencies.

However, you cannot start simulating in usdview, as there is no native simulation engine in this application.

To simulate this asset directly, the best application is [MuJoCo itself](#loading-usd-in-mujoco-simulate)!

Simulating in other UsdPhysics enabled products (e.g. NVIDIA Omniverse, Unreal Engine, etc) may provided mixed results. The MJC physics data is structured hierarchically, which maximal coordinate solvers often do not support. Similarly, many of the important simulation settings are authored via MjcPhysics schemas, which is a USD plugin developed by Google DeepMind, that needs to be deployed & supported for import by the target runtime. In order to see faithful simulation in these applications, the USD asset will need to be modified to suit the expectations of each target runtime.

## Loading USD in MuJoCo Simulate

Loading any USD Layer into MuJoCo Simulate requires a USD enabled build of MuJoCo (i.e. built from source against your own OpenUSD distribution).

> Important : USD support in MuJoCo is currently listed as experimental

To build MuJoCo with USD support, follow the usual CMake build instructions & provide the `USD_DIR` argument when configuring cmake. If you do not have a local USD distribution you will need to build or acquire one.

> Tip: OpenUSD Exchange provides a commandline tool to acquire many precompiled distributions of OpenUSD across several platforms & python versions. See the [install_usdex](https://docs.omniverse.nvidia.com/usd/code-docs/usd-exchange-sdk/latest/docs/devtools.html#install-usdex) documentation for details.

Once MuJoCo is compiled, you can launch the `./bin/simulate` app and drag & drop your USD asset into the viewport. The robot should load & simulate just as if you were using the original MJCF dataset.

# Contribution Guidelines

Contributions from the community are welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md) to learn about contributing via GitHub issues, as well as building the project from source and our development workflow.

# Community

For questions about this mujoco-usd-converter, feel free to join or start a [GitHub Discussions](https://github.com/newton-physics/mujoco-usd-converter/discussions).

For questions about OpenUSD Exchange SDK, use the [USD Exchange GitHub Discussions](https://github.com/NVIDIA-Omniverse/usd-exchange/discussions).

For questions about MuJoCo or the MjcPhysics USD Schemas, use the [MuJoCo Forums](https://github.com/google-deepmind/mujoco/discussions/categories/asking-for-help).

For general questions about OpenUSD itself, use the [Alliance for OpenUSD Forum](https://forum.aousd.org).

# References

- [MuJoCo Docs](https://mujoco.readthedocs.io/en/latest/overview.html)
- [NVIDIA OpenUSD Exchange SDK Docs](https://docs.omniverse.nvidia.com/usd/code-docs/usd-exchange-sdk)
- [OpenUSD API Docs](https://openusd.org/release/api/index.html)
- [OpenUSD User Docs](https://openusd.org/release/index.html)
- [NVIDIA OpenUSD Resources and Learning](https://developer.nvidia.com/usd)

# License

The mujoco-usd-converter is provided under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0), as is the [OpenUSD Exchange SDK](https://docs.omniverse.nvidia.com/usd/code-docs/usd-exchange-sdk/latest/docs/licenses.html) and [MuJoCo](https://github.com/google-deepmind/mujoco/blob/main/LICENSE).
