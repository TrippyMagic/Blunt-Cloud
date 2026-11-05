import tempfile
import unittest
from pathlib import Path

from bluntcloud.domain import mesh
from bluntcloud.application import revise, generate
from bluntcloud.adapters import export


def block():
    polygon = {"outer": [[0,0],[1,0],[1,1],[0,1]]}
    return {"step": .2, "extent": [0,.6], "sections": [
        {"z": z, "status": "approved", "polygons": [polygon]} for z in (.1,.3,.5)]}


class Core(unittest.TestCase):
    def test_block(self):
        result = mesh(block())
        self.assertEqual((len(result.points),len(result.cells),len(result.boundary)), (144,75,110))
        self.assertAlmostEqual(result.volume,.6)

    def test_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            revise(project, block())
            generate(project)
            for ext in ("dxf","inp","vtu","stl","ply"):
                target = root / ("block."+ext)
                export(project,target,True)
                self.assertGreater(target.stat().st_size,0)
            revise(project, block())
            with self.assertRaisesRegex(ValueError,"current revision"):
                export(project,root/"old.inp")
