import importlib.util
import unittest

import numpy as np


@unittest.skipUnless(importlib.util.find_spec("PySide6"), "requires the desktop extra")
class Navigation(unittest.TestCase):
    def test_drag_keys_and_projection(self):
        from PySide6 import QtCore, QtTest, QtWidgets
        from bluntcloud.navigation import ModelView

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        view = ModelView()
        view.GetRenderWindow().SetOffScreenRendering(1)
        view.resize(640, 480)
        test = QtTest.QTest
        try:
            for button in (QtCore.Qt.LeftButton, QtCore.Qt.MiddleButton):
                start = np.array(view.camera.GetPosition())
                center = view.camera.GetFocalPoint()
                test.mousePress(view, button, pos=QtCore.QPoint(60, 60))
                test.qWait(100)
                np.testing.assert_equal(view.camera.GetPosition(), start)
                test.mouseMove(view, QtCore.QPoint(100, 80))
                moved = view.camera.GetPosition()
                self.assertFalse(np.allclose(start, moved))
                np.testing.assert_equal(view.camera.GetFocalPoint(), center)
                test.mouseRelease(view, button, pos=QtCore.QPoint(100, 80))
                test.mouseMove(view, QtCore.QPoint(130, 85))
                test.qWait(100)
                np.testing.assert_equal(view.camera.GetPosition(), moved)

            for key, direction in [(QtCore.Qt.Key_1, (0, 1, 0)), (QtCore.Qt.Key_2, (0, 0, -1)),
                                   (QtCore.Qt.Key_3, (-1, 0, 0))]:
                test.keyClick(view, key)
                self.assertTrue(view.camera.GetParallelProjection())
                np.testing.assert_allclose(view.camera.GetDirectionOfProjection(), direction)
            for key in (QtCore.Qt.Key_W, QtCore.Qt.Key_A, QtCore.Qt.Key_S, QtCore.Qt.Key_D):
                center = np.array(view.camera.GetFocalPoint())
                start = np.array(view.camera.GetPosition())
                test.keyClick(view, key)
                delta = np.array(view.camera.GetPosition()) - start
                self.assertGreater(np.linalg.norm(delta), 0)
                np.testing.assert_allclose(view.camera.GetFocalPoint() - center, delta)
        finally:
            view.Finalize()
            view.close()
