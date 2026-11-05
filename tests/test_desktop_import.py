"""Exercise Import from a fresh desktop session using synthetic survey data."""
import importlib.util
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec("PySide6"), "requires the desktop extra")
class DesktopImport(unittest.TestCase):
    def test_first_import_creates_visible_project_and_cloud(self):
        from bluntcloud.ui import W, Window

        app = W.QApplication.instance() or W.QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "Survey project"
            project.mkdir()
            cloud = Path(directory) / "wall.xyz"
            cloud.write_text("0 0 0\n1 0 0\n0 1 0\n", encoding="ascii")
            window = Window()
            window.vtk.GetRenderWindow().SetOffScreenRendering(1)
            def wait_for_worker():
                deadline = time.monotonic() + 30
                while not window.actions[0].isEnabled() and time.monotonic() < deadline:
                    app.processEvents()
                    time.sleep(.01)
                self.assertTrue(window.actions[0].isEnabled(), "Worker timed out")

            try:
                with patch.object(W.QFileDialog, "getExistingDirectory", return_value=""), patch.object(
                    W.QFileDialog, "getOpenFileName"
                ) as choose_cloud:
                    window.import_file()
                    choose_cloud.assert_not_called()
                with patch.object(W.QFileDialog, "getExistingDirectory", return_value=str(project)), patch.object(
                    W.QFileDialog, "getOpenFileName", return_value=(str(cloud), "")
                ), patch.object(W.QInputDialog, "getItem", return_value=("m", True)):
                    window.import_file()
                self.assertEqual(window.tree.topLevelItem(0).text(0), project.name)
                wait_for_worker()
                self.assertEqual(Path(window.file_model.rootPath()).resolve(), project.resolve())
                self.assertTrue(window.file_model.index(str(project / "project.sqlite")).isValid())
                root = window.tree.topLevelItem(0)
                self.assertTrue(root.isExpanded())
                self.assertEqual(root.child(0).text(0), cloud.name)
                self.assertEqual(len(window.cloud_preview), 3)
                self.assertEqual(window.renderer.GetActors().GetNumberOfItems(), 1)
                self.assertIn("Imported 3 points", window.statusBar().currentMessage())
                window.generate_volume()
                self.assertIn("Create sections first", window.statusBar().currentMessage())
                self.assertTrue(window.actions[0].isEnabled())
                window.run("propose", "-0.1", "0.1", "0.2", "0.005", "0.2")
                wait_for_worker()
                window.generate_volume()
                self.assertEqual(window.state.currentText(), "review")
                self.assertIn("Review the selected rings", window.statusBar().currentMessage())
                window.state.setCurrentText("approved")
                window.apply()
                window.generate_volume()
                wait_for_worker()
                self.assertIn("HEX8 volume visible", window.statusBar().currentMessage())
                self.assertEqual(window.renderer.GetActors().GetNumberOfItems(), 2)
            finally:
                window.close()


