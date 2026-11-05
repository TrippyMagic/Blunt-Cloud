"""Planar ring editor in local metres."""
from math import hypot
from PySide6 import QtCore, QtGui, QtWidgets as W


class Vertex(W.QGraphicsEllipseItem):
    def __init__(self, x, y, edited):
        super().__init__(-3,-3,6,6)
        self.edited = edited
        self.setBrush(QtGui.QColor("#298875"))
        self.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        self.setFlags(W.QGraphicsItem.GraphicsItemFlag.ItemIsMovable | W.QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations | W.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setPos(x,-y)
        self.setZValue(2)

    def mouseReleaseEvent(self,event):
        super().mouseReleaseEvent(event)
        self.edited()


class SectionView(W.QGraphicsView):
    changed = QtCore.Signal(object)
    measured = QtCore.Signal(float)

    def __init__(self, scene):
        super().__init__(scene)
        self.parts = []
        self.handles = []
        self.paths = []
        self.mode = "move"
        self.draft = []
        self.anchor = None

    def load(self, parts):
        self.parts = parts
        self.draft.clear()
        self.anchor = None
        self.scene().clear()
        self.handles.clear()
        self.paths.clear()
        for part in parts:
            for ring in [part["outer"],*part.get("holes",[])]:
                path = self.scene().addPolygon(QtGui.QPolygonF(), QtGui.QPen(QtGui.QColor("#308574"),0))
                handles = []
                for x,y in ring:
                    vertex = Vertex(x,y,self.sync)
                    self.scene().addItem(vertex)
                    handles.append(vertex)
                self.handles.append((ring,handles))
                self.paths.append(path)
        self.sync(False)
        if self.handles:
            self.fitInView(self.scene().itemsBoundingRect(),QtCore.Qt.KeepAspectRatio)

    def sync(self, emit=True):
        for (ring,handles),path in zip(self.handles,self.paths):
            ring[:] = [[v.pos().x(),-v.pos().y()] for v in handles]
            path.setPolygon(QtGui.QPolygonF([v.pos() for v in handles]))
        if emit:
            self.changed.emit(self.parts)

    def mousePressEvent(self,event):
        pos = self.mapToScene(event.position().toPoint())
        xy = [pos.x(),-pos.y()]
        if self.mode == "measure":
            if self.anchor:
                self.measured.emit(hypot(xy[0]-self.anchor[0],xy[1]-self.anchor[1]))
                self.anchor = None
            else:
                self.anchor = xy
            return
        if self.mode in {"outer","hole"}:
            if event.button() == QtCore.Qt.RightButton and len(self.draft)>=3:
                if self.mode == "outer":
                    self.parts.append({"outer":self.draft.copy(),"holes":[]})
                else:
                    from shapely.geometry import Polygon
                    owners = [p for p in self.parts if Polygon(p["outer"],p.get("holes",[])).contains(Polygon(self.draft))]
                    if len(owners)!=1:
                        return
                    owners[0].setdefault("holes",[]).append(self.draft.copy())
                self.load(self.parts)
                self.changed.emit(self.parts)
            elif event.button() == QtCore.Qt.LeftButton:
                self.draft.append(xy)
                dot = self.scene().addEllipse(-2,-2,4,4)
                dot.setFlag(W.QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
                dot.setPos(pos)
            return
        super().mousePressEvent(event)

    def keyPressEvent(self,event):
        if event.key() == QtCore.Qt.Key_Delete:
            for ring,handles in self.handles:
                ring[:] = [[v.pos().x(),-v.pos().y()] for v in handles if not v.isSelected()]
            self.load(self.parts)
            self.changed.emit(self.parts)
        else:
            super().keyPressEvent(event)

