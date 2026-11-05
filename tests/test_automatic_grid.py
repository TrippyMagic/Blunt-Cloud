from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bluntcloud.adapters import export
from bluntcloud.application import catalog, current, read_mesh, restore_variant, saved_grids
from bluntcloud.automatic import grid_volume
from bluntcloud.cloud import import_cloud, load_cloud


class AutomaticGrid(unittest.TestCase):
    def test_variants_fill_restore_and_clip(self):
        with TemporaryDirectory() as directory:
            project = Path(directory)
            samples = [f"{x} {y} {z}" for z in (0,1.4,3) for x in range(3)
                       for y in range(3) if (x,y) != (1,1)]
            source = project/"tower.xyz"
            source.write_text("\n".join(samples))
            import_cloud(project,source,"m")
            shell = grid_volume(project,0,1.4,1,1)
            with catalog(project) as db:
                m = read_mesh(db)
                self.assertEqual(len(m.cells),16)
                self.assertAlmostEqual(m.volume,11.2)
            filled = grid_volume(project,0,1.4,1,1,fill=True)
            with catalog(project) as db:
                self.assertEqual(len(read_mesh(db).cells),18)
            export(project,project/"filled.vtu")
            restored = restore_variant(project,shell,filled)
            export(project,project/"shell.inp")
            self.assertEqual([v["id"] for v in saved_grids(project)],[filled,shell])
            with self.assertRaisesRegex(ValueError,"No occupied"):
                grid_volume(project,0,1.4,1,1,min_points=2)
            with catalog(project) as db:
                self.assertEqual(current(db)[0],restored)
                self.assertEqual(len(read_mesh(db).cells),16)
            self.assertTrue((project/"filled.vtu").exists())
            self.assertTrue((project/"shell.inp").exists())

    def test_legacy_project_migration_preserves_user_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/"scan.xyz"
            source.write_text("0 0 0\n1 0 0")
            import_cloud(root,source,"m")
            private = root/".bluntcloud"
            for name in ("clouds","project.sqlite"):
                (private/name).rename(root/name)
            unrelated = root/"clouds"/"notes.txt"
            unrelated.write_text("keep")
            metadata,points = load_cloud(root)
            self.assertEqual(metadata["filename"],source.name)
            self.assertEqual(len(points),2)
            del points
            self.assertEqual(unrelated.read_text(),"keep")
            self.assertFalse((root/"project.sqlite").exists())
            self.assertTrue((private/"project.sqlite").exists())
