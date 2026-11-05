"""Desktop workbench. Geometry jobs use the headless entry point."""
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets as W
import vtkmodules.vtkInteractionStyle
import vtkmodules.vtkRenderingOpenGL2
from .navigation import ModelView
from vtkmodules.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkCellArray, vtkPlane
from vtkmodules.vtkFiltersGeneral import vtkVertexGlyphFilter
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper

from .application import catalog, current, revise
from .cloud import load_cloud
from .editor import SectionView


class Window(W.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blunt-Cloud")
        self.resize(1220,760)
        self.project = None
        self.preview_dir = tempfile.TemporaryDirectory()
        self.preview = Path(self.preview_dir.name)/"surface.npy"
        self.plane = vtkPlane()
        self.plane.SetNormal(0,0,-1)
        self.cloud_preview = np.empty((0,3))
        self.mappers = []
        self.job = None
        self.recipe = {}
        self.worker = QtCore.QProcess(self)
        self.worker.finished.connect(self.finished)
        self.worker.errorOccurred.connect(self.worker_error)
        bar = self.addToolBar("Project")
        self.actions = []
        for title,slot in [("Open project",self.open),("Import",self.import_file),
                           ("Create sections",self.propose),("Generate volume",self.generate_volume),
                           ("Undo",lambda:self.run("undo")),("Redo",lambda:self.run("redo")),("Export",self.export)]:
            self.actions.append(bar.addAction(title,slot))
        self.cancel = bar.addAction("Cancel job",self.worker.kill)
        self.cancel.setEnabled(False)
        body = W.QSplitter()
        self.setCentralWidget(body)
        self.tree = W.QTreeWidget()
        self.tree.setHeaderLabel("Project")
        sidebar = W.QSplitter(QtCore.Qt.Vertical)
        sidebar.addWidget(self.tree)
        self.files = W.QTreeView()
        self.file_model = W.QFileSystemModel(self.files)
        self.file_model.setReadOnly(True)
        self.file_filter = QtCore.QSortFilterProxyModel(self.files)
        self.file_filter.setSourceModel(self.file_model)
        self.file_filter.setFilterRegularExpression(r"^(?!\.bluntcloud$).*")
        self.files.setModel(self.file_filter)
        self.files.setHeaderHidden(True)
        for column in range(1, self.file_model.columnCount()):
            self.files.hideColumn(column)
        directory = W.QGroupBox("Working directory")
        layout = W.QVBoxLayout(directory)
        layout.addWidget(self.files)
        sidebar.addWidget(directory)
        self.files.setVisible(False)
        body.addWidget(sidebar)
        self.vtk = ModelView()
        body.addWidget(self.vtk)
        self.renderer = self.vtk.renderer
        bar.addSeparator()
        for i, plane in enumerate(self.vtk.PLANES, start=1):
            action = bar.addAction(plane)
            action.setToolTip(f"{plane} ({i} in the 3D view)")
            action.triggered.connect(lambda checked=False, name=plane: self.vtk.view_plane(name))
        panel = W.QWidget()
        form = W.QFormLayout(panel)
        body.addWidget(panel)
        self.params = []
        for title,default in [("Base (m)",0),("Roof (m)",1),("Z spacing (m)",.2),
                              ("Band thickness (m)",.05),("XY spacing (m)",.2)]:
            field = W.QDoubleSpinBox()
            field.setDecimals(6)
            field.setRange(-1e8,1e8)
            field.setValue(default)
            self.params.append(field)
            form.addRow(title,field)
        self.clip = W.QCheckBox("Clip at section height")
        form.addRow(self.clip)
        self.clip.toggled.connect(lambda:self.select(self.tree.currentItem()))
        self.scene = W.QGraphicsScene(self)
        self.section = SectionView(self.scene)
        modes = W.QComboBox()
        for label,mode in [("Move vertex","move"),("Draw outer ring","outer"),("Draw hole","hole"),("Measure","measure")]:
            modes.addItem(label,mode)
        modes.setToolTip("Click to add a vertex. Right-click to close the ring. Delete removes selected vertices.")
        modes.currentIndexChanged.connect(lambda:setattr(self.section,"mode",modes.currentData()))
        self.section.changed.connect(lambda parts:self.edit.setPlainText(json.dumps(parts)))
        self.section.measured.connect(lambda length:self.statusBar().showMessage(f"{length:.6g} m"))
        form.addRow(modes)
        form.addRow(self.section)
        self.edit = W.QPlainTextEdit()
        form.addRow("XY rings (m)",self.edit)
        self.state = W.QComboBox()
        self.state.addItems(["review","approved","empty"])
        form.addRow("Status",self.state)
        self.save = W.QPushButton("Apply section")
        form.addRow(self.save)
        self.save.clicked.connect(self.apply)
        self.tree.currentItemChanged.connect(self.select)
        body.setSizes([180,650,330])

    def open(self):
        folder = W.QFileDialog.getExistingDirectory(self,"Open or create project")
        if not folder:
            return False
        if ".bluntcloud" in Path(folder).resolve().parts:
            self.statusBar().showMessage("Choose the project folder outside private storage.")
            return False
        self.project = Path(folder)
        self.files.setRootIndex(self.file_filter.mapFromSource(self.file_model.setRootPath(str(self.project))))
        self.files.setVisible(True)
        return self.refresh()

    def refresh(self):
        self.tree.clear()
        root = W.QTreeWidgetItem([self.project.name or str(self.project)])
        self.tree.addTopLevelItem(root)
        root.setExpanded(True)
        self.setWindowTitle(f"Blunt-Cloud · {root.text(0)}")
        self.recipe = {}
        self.section.load([])
        self.edit.clear()
        self.renderer.RemoveAllViewProps()
        self.cloud_preview = np.empty((0,3))
        self.mappers.clear()
        try:
            with catalog(self.project) as db:
                if not db.execute("select 1 from revisions limit 1").fetchone():
                    self.vtk.GetRenderWindow().Render()
                    self.statusBar().showMessage("Project ready. Import a point cloud.")
                    return True
                self.revision,raw = current(db)
                has_mesh = db.execute("select 1 from meshes where revision=?",(self.revision,)).fetchone()
            self.recipe = json.loads(raw)
            if "cloud" in self.recipe:
                info,points = load_cloud(self.project)
                root.addChild(W.QTreeWidgetItem([info["filename"]]))
                self.cloud_preview = np.array(points[::max(1,(len(points)+499999)//500000)],dtype=np.float32)
                self.plot(self.cloud_preview)
            for i,s in enumerate(self.recipe.get("sections",[])):
                item = W.QTreeWidgetItem([f"{s['z']:.4g} m · {s['status']}"])
                item.setData(0,QtCore.Qt.UserRole,i)
                root.addChild(item)
            if has_mesh:
                root.addChild(W.QTreeWidgetItem(["HEX8 volume"]))
                self.preview.unlink(missing_ok=True)
                self.run("preview",str(self.preview))
            self.setWindowTitle(f"Blunt-Cloud · {self.project.name}")
        except (ValueError,OSError) as exc:
            self.statusBar().showMessage(str(exc))
            return False
        self.vtk.GetRenderWindow().Render()
        return True

    def plot(self,points, surface=False):
        vertices = vtkPoints()
        vertices.SetData(numpy_to_vtk(np.ascontiguousarray(points,dtype=np.float32),deep=True))
        data = vtkPolyData()
        data.SetPoints(vertices)
        glyph = vtkVertexGlyphFilter()
        glyph.SetInputData(data)
        mapper = vtkPolyDataMapper()
        if surface:
            n = len(points)
            faces = vtkCellArray()
            faces.SetData(numpy_to_vtkIdTypeArray(np.arange(0,n+1,4,dtype=np.int64),deep=True),
                          numpy_to_vtkIdTypeArray(np.arange(n,dtype=np.int64),deep=True))
            data.SetPolys(faces)
            mapper.SetInputData(data)
        else:
            mapper.SetInputConnection(glyph.GetOutputPort())
        self.mappers.append(mapper)
        actor = vtkActor()
        actor.SetMapper(mapper)
        if surface:
            actor.GetProperty().SetColor(.4,.8,.72)
            actor.GetProperty().SetOpacity(.65)
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()

    def select(self,item):
        self.section.load([])
        self.edit.clear()
        if item is None or (i:=item.data(0,QtCore.Qt.UserRole)) is None:
            return
        s = self.recipe["sections"][i]
        self.plane.SetOrigin(0,0,s["z"])
        for mapper in self.mappers:
            mapper.RemoveAllClippingPlanes()
            if self.clip.isChecked():
                mapper.AddClippingPlane(self.plane)
        self.vtk.GetRenderWindow().Render()
        self.edit.setPlainText(json.dumps(s["polygons"]))
        self.state.setCurrentText(s["status"])
        self.section.load(json.loads(self.edit.toPlainText()))
        if len(self.cloud_preview):
            band = self.cloud_preview[np.abs(self.cloud_preview[:,2]-s["z"]) <= self.recipe.get("thickness",0)/2]
            dots = QtGui.QPainterPath()
            for x,y,_ in band[::max(1,(len(band)+4999)//5000)]:
                dots.moveTo(float(x),-float(y))
                dots.lineTo(float(x)+1e-7,-float(y))
            self.scene.addPath(dots,QtGui.QPen(QtGui.QColor("#999999"),0)).setZValue(-1)
        self.section.fitInView(self.scene.itemsBoundingRect(),QtCore.Qt.KeepAspectRatio)

    def apply(self):
        item = self.tree.currentItem()
        if item is None or (i:=item.data(0,QtCore.Qt.UserRole)) is None:
            return
        try:
            recipe = dict(self.recipe,sections=self.recipe["sections"].copy())
            recipe["sections"][i] = dict(recipe["sections"][i],polygons=json.loads(self.edit.toPlainText()),
                                         status=self.state.currentText())
            revise(self.project,recipe,self.revision)
            self.refresh()
        except (ValueError,TypeError) as exc:
            self.statusBar().showMessage(str(exc))

    def import_file(self):
        if self.project is None and not self.open():
            return
        path,_ = W.QFileDialog.getOpenFileName(self,"Point cloud","","Point clouds (*.pcd *.ply *.xyz *.txt)")
        if path:
            unit,ok = W.QInputDialog.getItem(self,"Source unit","Unit",["m","cm","mm"],editable=False)
            if ok:
                self.run("import",path,unit)

    def generate_volume(self):
        if not self.recipe.get("sections"):
            self.statusBar().showMessage("Use Create sections first, then review each section before generating the volume.")
            return
        for i, section in enumerate(self.recipe["sections"]):
            if section["status"] not in ("approved", "empty"):
                root = self.tree.topLevelItem(0)
                for row in range(root.childCount()):
                    item = root.child(row)
                    if item.data(0, QtCore.Qt.UserRole) == i:
                        self.tree.setCurrentItem(item)
                        break
                self.statusBar().showMessage("Review the selected rings, choose approved or empty, then click Apply section.")
                return
        self.run("generate")

    def propose(self):
        self.run("propose",*[str(p.value()) for p in self.params])

    def export(self):
        path,_ = W.QFileDialog.getSaveFileName(self,"Export","","Volume (*.vtu *.inp);;Sections (*.dxf);;Surface (*.ply *.stl)")
        if path:
            options = []
            if Path(path).suffix.lower() in {".stl",".ply"}:
                if W.QMessageBox.question(self,"Export surface","Export without units and groups?") != W.QMessageBox.Yes:
                    return
                options.append("--accept-loss")
            self.run("export",path,*options)

    def run(self,*args):
        if self.project is None:
            self.statusBar().showMessage("Open a project first")
            return
        self.job = args[0]
        prefix = ["--cli"] if getattr(sys,"frozen",False) else ["-m","bluntcloud"]
        for action in self.actions:
            action.setEnabled(False)
        self.save.setEnabled(False)
        self.cancel.setEnabled(True)
        self.statusBar().showMessage(args[0]+"…")
        self.worker.start(sys.executable,[*prefix,str(self.project),*args])

    def worker_error(self,error):
        if error == QtCore.QProcess.FailedToStart:
            self.restore_actions()
            self.statusBar().showMessage("Could not start the processing worker.")

    def restore_actions(self):
        for action in self.actions:
            action.setEnabled(True)
        self.cancel.setEnabled(False)
        self.save.setEnabled(True)
    def finished(self,code,status):
        self.restore_actions()
        message = bytes(self.worker.readAllStandardError()).decode(errors="replace")
        self.worker.readAllStandardOutput()
        if self.job == "preview":
            if not code and self.preview.exists():
                faces = np.load(self.preview,allow_pickle=False)
                if not len(faces):
                    self.statusBar().showMessage("The approved sections contain no occupied cells.")
                    return
                self.plot(faces.reshape(-1,3),surface=True)
                self.vtk.GetRenderWindow().Render()
                self.statusBar().showMessage(f"HEX8 volume visible ({len(faces):,} preview faces)")
                return
        elif not code:
            if not self.refresh():
                return
            if self.job == "import" and "cloud" in self.recipe:
                info = self.recipe["cloud"]
                self.statusBar().showMessage(f"Imported {info['count']:,} points from {info['filename']}")
                return
        self.statusBar().showMessage(message.strip() or ("Completed" if not code else "Job interrupted"))

    def closeEvent(self,event):
        if self.worker.state() != QtCore.QProcess.NotRunning:
            self.worker.kill()
            self.worker.waitForFinished(5000)
        self.vtk.Finalize()
        super().closeEvent(event)


def main():
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.English))
    W.QApplication.setAttribute(QtCore.Qt.AA_DontUseNativeDialogs)
    app = W.QApplication(sys.argv)
    window = Window()
    window.show()
    window.vtk.Initialize()
    sys.exit(app.exec())
