# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import numpy as np
from pxr import Gf, Vt

__all__ = ["convert_color", "convert_quat", "convert_vec3d", "convert_vec3f_array"]


def convert_vec3d(source: np.ndarray) -> Gf.Vec3d:
    """
    Convert a numpy 3D vector array to a USD Vec3d.

    Args:
        source: A numpy array of shape (3,) containing XYZ values.

    Returns:
        Gf.Vec3d: The converted 3D vector.

    Raises:
        AssertionError: If the input array does not have shape (3,).
    """
    assert source.shape == (3,)
    return Gf.Vec3d(float(source[0]), float(source[1]), float(source[2]))


def convert_quat(source: np.ndarray) -> Gf.Quatf:
    """
    Convert a numpy quaternion array to a USD rotation.

    Args:
        source: A numpy array of shape (4,) containing quaternion values (w, x, y, z).

    Returns:
        Gf.Quatf: The converted rotation quaternion.

    Raises:
        AssertionError: If the input array does not have shape (4,).
    """
    assert source.shape == (4,) or source.shape == (4, 1)
    return Gf.Quatf(float(source[0]), Gf.Vec3f(float(source[1]), float(source[2]), float(source[3])))


def convert_color(source: np.ndarray) -> tuple[Gf.Vec3f, float]:
    """
    Convert a numpy RGBA color array to a USD Color3f and opacity value.

    Args:
        source: A numpy array of shape (4,) containing RGBA values in the range [0, 1].

    Returns:
        A tuple containing:
            - Gf.Vec3f: The RGB color component
            - float: The alpha/opacity value

    Raises:
        AssertionError: If the input array does not have shape (4,).
    """
    assert source.shape == (4,)
    return Gf.Vec3f(float(source[0]), float(source[1]), float(source[2])), float(source[3])


def convert_vec3f_array(source: np.ndarray) -> Vt.Vec3fArray:
    """
    Convert a numpy array of 3D vectors to a USD Vec3fArray.

    Args:
        source: A numpy array of shape (N, M) where M is divisible by 3,
                 representing N elements each with M/3 3D vectors.

    Returns:
        Vt.Vec3fArray: A USD array of 3D vectors.

    Raises:
        AssertionError: If the second dimension of the input array is not divisible by 3.
    """
    num_elements, element_size = source.shape
    assert element_size % 3 == 0
    result = []
    for i in range(num_elements):
        result.extend([Gf.Vec3f(float(source[i][j]), float(source[i][j + 1]), float(source[i][j + 2])) for j in range(0, element_size, 3)])
    return Vt.Vec3fArray(result)
