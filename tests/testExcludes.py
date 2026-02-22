# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import pathlib

import usdex.core
import usdex.test
from pxr import Sdf, Tf, Usd, UsdPhysics

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestExcludes(ConverterTestCase):

    def test_contact_excludes(self):
        model_path = pathlib.Path("./tests/data/contact_excludes.xml")
        model_name = model_path.stem

        with usdex.test.ScopedDiagnosticChecker(
            self,
            [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, ".*Body 'world' or 'world' not found for contact exclude")],
            level=usdex.core.DiagnosticsLevel.eWarning,
        ):
            asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model_path, self.tmpDir())
        stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # Test that the exclude is applied to the bodies
        body1 = stage.GetPrimAtPath(f"/{model_name}/Geometry/no_collide_A")
        self.assertTrue(body1.IsValid())
        self.assertTrue(body1.HasAPI(UsdPhysics.FilteredPairsAPI))
        filtered_pairs_api = UsdPhysics.FilteredPairsAPI(body1)
        self.assertEqual(len(filtered_pairs_api.GetFilteredPairsRel().GetTargets()), 2)
        self.assertEqual(filtered_pairs_api.GetFilteredPairsRel().GetTargets()[0], f"/{model_name}/Geometry/no_collide_B")
        self.assertEqual(filtered_pairs_api.GetFilteredPairsRel().GetTargets()[1], f"/{model_name}/Geometry/no_collide_C")

        body2 = stage.GetPrimAtPath(f"/{model_name}/Geometry/no_collide_B")
        self.assertTrue(body2.IsValid())
        self.assertTrue(body2.HasAPI(UsdPhysics.FilteredPairsAPI))
        filtered_pairs_api = UsdPhysics.FilteredPairsAPI(body2)
        self.assertEqual(len(filtered_pairs_api.GetFilteredPairsRel().GetTargets()), 1)
        self.assertEqual(filtered_pairs_api.GetFilteredPairsRel().GetTargets()[0], f"/{model_name}/Geometry/no_collide_C")

        # Test that the exclude is not applied to the bodies
        body3 = stage.GetPrimAtPath(f"/{model_name}/Geometry/no_collide_C")
        self.assertTrue(body3.IsValid())
        self.assertFalse(body3.HasAPI(UsdPhysics.FilteredPairsAPI))
