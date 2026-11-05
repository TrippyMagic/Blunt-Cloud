"""Qt-owned camera controls for the VTK scene."""
import math

import numpy as np
from PySide6 import QtCore
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkRenderingCore import vtkRenderer


class ModelView(QVTKRenderWindowInteractor):
    PLANES = {
        "PV": ((0, -1, 0), (0, 0, 1)),
        "PO": ((0, 0, 1), (0, 1, 0)),
        "PL": ((1, 0, 0), (0, 0, 1)),
    }

    def __init__(self):
        super().__init__()
        self.renderer = vtkRenderer()
        self.renderer.SetBackground(.12, .16, .20)
        self.GetRenderWindow().AddRenderer(self.renderer)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.drag_button = None
        self.previous = None
        axes = vtkAxesActor()
        for axis in "XYZ":
            for part in ("Shaft", "Tip"):
                getattr(axes, f"Get{axis}Axis{part}Property")().SetColor(.8, .8, .8)
            caption = getattr(axes, f"Get{axis}AxisCaptionActor2D")()
            caption.GetCaptionTextProperty().SetColor(.9, .9, .9)
        self.marker = vtkOrientationMarkerWidget()
        self.marker.SetOrientationMarker(axes)
        self.marker.SetInteractor(self.GetRenderWindow().GetInteractor())
        self.marker.SetViewport(0, 0, .19, .19)
        self.marker.SetEnabled(1)
        self.marker.InteractiveOff()

    @property
    def camera(self):
        return self.renderer.GetActiveCamera()

    def redraw(self):
        self.renderer.ResetCameraClippingRange()
        self.GetRenderWindow().Render()

    def view_plane(self, name):
        direction, up = self.PLANES[name]
        camera = self.camera
        center = np.array(camera.GetFocalPoint())
        distance = camera.GetDistance()
        if not camera.GetParallelProjection():
            camera.SetParallelScale(distance * math.tan(math.radians(camera.GetViewAngle()/2)))
        camera.ParallelProjectionOn()
        camera.SetPosition(*(center + distance*np.array(direction)))
        camera.SetViewUp(*up)
        self.redraw()

    def mousePressEvent(self, event):
        if self.drag_button is None:
            self.setFocus()
            self.drag_button = event.button()
            self.previous = event.position()
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == self.drag_button:
            self.drag_button = None
            self.previous = None
        event.accept()

    def focusOutEvent(self, event):
        self.drag_button = None
        self.previous = None
        super().focusOutEvent(event)

    def translate(self, delta):
        camera = self.camera
        camera.SetPosition(*(np.array(camera.GetPosition()) + delta))
        camera.SetFocalPoint(*(np.array(camera.GetFocalPoint()) + delta))

    def basis(self):
        camera = self.camera
        forward = np.array(camera.GetDirectionOfProjection())
        right = np.cross(forward, camera.GetViewUp())
        right /= np.linalg.norm(right)
        return right, np.cross(right, forward)

    def half_height(self):
        camera = self.camera
        if camera.GetParallelProjection():
            return camera.GetParallelScale()
        return camera.GetDistance() * math.tan(math.radians(camera.GetViewAngle()/2))

    def mouseMoveEvent(self, event):
        if self.previous is None or not (event.buttons() & self.drag_button):
            return
        delta = event.position() - self.previous
        self.previous = event.position()
        if delta.isNull():
            return
        if self.drag_button in (QtCore.Qt.LeftButton, QtCore.Qt.MiddleButton):
            self.camera.Azimuth(-180 * delta.x()/max(1,self.width()))
            self.camera.Elevation(180 * delta.y()/max(1,self.height()))
            self.camera.OrthogonalizeViewUp()
        elif self.drag_button == QtCore.Qt.RightButton:
            right, up = self.basis()
            self.translate((up*delta.y()-right*delta.x()) * (2*self.half_height()/max(1,self.height())))
        self.redraw()

    def wheelEvent(self, event):
        factor = 1.2 ** (event.angleDelta().y()/120)
        if self.camera.GetParallelProjection():
            self.camera.SetParallelScale(self.camera.GetParallelScale()/factor)
        else:
            self.camera.Dolly(factor)
        self.redraw()
        event.accept()

    def keyPressEvent(self, event):
        key = event.key()
        planes = {QtCore.Qt.Key_1:"PV", QtCore.Qt.Key_2:"PO", QtCore.Qt.Key_3:"PL"}
        if key in planes:
            self.view_plane(planes[key])
        elif key == QtCore.Qt.Key_0:
            self.renderer.ResetCamera()
            self.redraw()
        elif key in (QtCore.Qt.Key_W, QtCore.Qt.Key_A, QtCore.Qt.Key_S, QtCore.Qt.Key_D):
            right, up = self.basis()
            movement = {QtCore.Qt.Key_W:up, QtCore.Qt.Key_S:-up,
                        QtCore.Qt.Key_A:-right, QtCore.Qt.Key_D:right}
            self.translate(movement[key] * self.half_height() * .08)
            self.redraw()
        else:
            event.ignore()
