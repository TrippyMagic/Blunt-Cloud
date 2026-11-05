import tempfile
import unittest
from pathlib import Path

import numpy as np
from bluntcloud.cloud import import_cloud, load_cloud, propose
from bluntcloud.application import catalog, current, generate
from bluntcloud.domain import mesh
from bluntcloud.validation import quality
from test_core import block


class Surveys(unittest.TestCase):
    def test_import_formats(self):
        payloads = {
            ".xyz": b"1000 1000 0\n2000 1000 0\n2000 2000 0\n",
            ".ply": b"ply\nformat ascii 1.0\nelement vertex 3\nproperty double x\nproperty double y\nproperty double z\nend_header\n1000 1000 0\n2000 1000 0\n2000 2000 0\n",
            ".pcd": b"FIELDS x y z _\nSIZE 4 4 4 1\nTYPE F F F U\nCOUNT 1 1 1 4\nPOINTS 3\nDATA binary\n" + np.array([[1000,1000,0,0],[2000,1000,0,0],[2000,2000,0,0]],dtype="<f4").tobytes()}
        for suffix,payload in payloads.items():
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as directory:
                source = Path(directory)/("tiny"+suffix)
                source.write_bytes(payload)
                project = Path(directory)/"project"
                import_cloud(project,source,"mm")
                info, points = load_cloud(project)
                np.testing.assert_equal(points[-1],[1,1,0])
                del points
                propose(project,-.1,.1,.2,.1,.2)
                with self.assertRaisesRegex(ValueError,"review"):
                    generate(project)

    def test_large_translation(self):
        recipe = block()
        recipe["step"] = .01
        for section in recipe["sections"]:
            section["polygons"] = [{"outer":[[1e6+x*.1,1e6+y*.1] for x,y in ((0,0),(1,0),(1,1),(0,1))]}]
        result = mesh(recipe)
        self.assertEqual(len(result.cells),300)
        self.assertGreater(quality(result)["min_jacobian"],0)

    def test_gap_and_hole(self):
        recipe = block()
        recipe["sections"][1] = {"z":.3,"status":"empty","polygons":[]}
        for section in (recipe["sections"][0],recipe["sections"][2]):
            section["polygons"][0]["holes"] = [[[.2,.2],[.8,.2],[.8,.8],[.2,.8]]]
        result = mesh(recipe)
        self.assertEqual(len(result.cells),32)
        self.assertEqual(quality(result)["components"],2)
