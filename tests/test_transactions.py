import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bluntcloud.application import catalog, current, generate, navigate, read_mesh, revise
from bluntcloud.domain import mesh
from bluntcloud.validation import quality
from test_core import block


class Transactions(unittest.TestCase):
    def test_late_worker(self):
        with tempfile.TemporaryDirectory() as p:
            recipe = block()
            revise(p,recipe)
            def changed(snapshot):
                revise(p,recipe)
                return mesh(snapshot)
            with patch("bluntcloud.application.mesh",changed):
                with self.assertRaisesRegex(ValueError,"revision changed"):
                    generate(p)
            with catalog(p) as db, self.assertRaisesRegex(ValueError,"current revision"):
                read_mesh(db)

    def test_undo_redo_invalidates(self):
        with tempfile.TemporaryDirectory() as p:
            recipe = block()
            revise(p,recipe)
            recipe["step"] = .1
            revise(p,recipe)
            generate(p)
            for command,expected in [("undo",.2),("redo",.1)]:
                navigate(p,command)
                with catalog(p) as db:
                    self.assertEqual(json.loads(current(db)[1])["step"],expected)
                    with self.assertRaisesRegex(ValueError,"current revision"):
                        read_mesh(db)

    def test_corrupt_mesh(self):
        with tempfile.TemporaryDirectory() as p:
            revise(p,block())
            generate(p)
            with catalog(p) as db:
                db.execute("update meshes set data=x'00'")
            with catalog(p) as db, self.assertRaisesRegex(ValueError,"integrity"):
                read_mesh(db)

    def test_two_cells(self):
        recipe = {"extent":[0,1],"step":1,"sections":[{"status":"approved","z":.5,
                  "polygons":[{"outer":[[0,0],[2,0],[2,1],[0,1]]}]}]}
        result = mesh(recipe)
        self.assertEqual((len(result.cells),len(result.points),len(result.boundary)),(2,12,10))
        self.assertEqual(quality(result)["components"],1)

    def test_unobserved_and_underresolved(self):
        recipe = block()
        recipe["sections"][1]["status"] = "review"
        with self.assertRaisesRegex(ValueError,"review"):
            mesh(recipe)
        recipe = block()
        recipe["step"] = 3
        with self.assertRaisesRegex(ValueError,"resolution"):
            mesh(recipe)
