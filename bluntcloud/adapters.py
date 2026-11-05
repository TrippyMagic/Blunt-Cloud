"""Local geometry exports with read-back before atomic publication."""
from pathlib import Path
import json
import os
import tempfile

import ezdxf
import meshio
import numpy as np

from .application import catalog, current, read_mesh


def export(project, destination, accept_loss=False):
    target = Path(destination).resolve()
    if target.is_relative_to(Path(project).resolve()):
        raise ValueError("Save the exported file outside the project directory")
    ext = target.suffix.lower()
    if ext not in {".dxf", ".vtu", ".inp", ".ply", ".stl"}:
        raise ValueError("Unknown export format")
    if ext in {".ply", ".stl"} and not accept_loss:
        raise ValueError("Use --accept-loss to export without groups and units")
    with catalog(project) as db:
        db.execute("begin immediate")
        result = read_mesh(db)
        if not len(result.cells):
            raise ValueError("Empty volume")
        fd, name = tempfile.mkstemp(dir=target.parent, suffix=ext)
        os.close(fd)
        tmp = Path(name)
        try:
            if ext == ".dxf":
                doc = ezdxf.new("R2013")
                doc.units = 6
                rings = []
                for k, section in enumerate(json.loads(current(db)[1])["sections"]):
                    for p, polygon in enumerate(section["polygons"]):
                        for h, ring in enumerate([polygon["outer"], *polygon.get("holes", [])]):
                            layer = f"S{k}_P{p}_R{h}"
                            doc.layers.add(layer)
                            doc.modelspace().add_lwpolyline(ring, close=True, dxfattribs={
                                "layer": layer, "elevation": section["z"]})
                            rings.append((ring, section["z"]))
                doc.saveas(tmp)
                loaded = list(ezdxf.readfile(tmp).modelspace())
                if len(loaded) != len(rings):
                    raise ValueError("DXF ring count mismatch")
                for entity, (ring,z) in zip(loaded, rings):
                    if not entity.closed or entity.dxf.elevation != z or not np.allclose(
                            entity.get_points("xy"), ring, atol=1e-9, rtol=0):
                        raise ValueError("DXF ring verification failed")
            else:
                write_mesh(tmp, ext, result)
            os.replace(tmp, target)
        finally:
            tmp.unlink(missing_ok=True)


def write_mesh(path, ext, mesh):
    points = mesh.points
    data = {}
    if ext in {".inp", ".vtu"}:
        kind, cells = "hexahedron", mesh.cells
        data = ({"cell_data": {"layer": [mesh.layers]}} if ext == ".vtu" else
                {"cell_sets": {f"LAYER_{k}": [np.flatnonzero(mesh.layers == k)]
                               for k in np.unique(mesh.layers)}})
    elif ext == ".ply":
        kind, cells = "quad", mesh.boundary.astype(np.int32)
    else:
        kind = "triangle"
        cells = np.concatenate((mesh.boundary[:,[0,1,2]], mesh.boundary[:,[0,2,3]]))
    output = meshio.Mesh(points, [(kind, cells)], **data)
    options = {"binary": True} if ext == ".stl" else {}
    output.write(path, **options)
    check = meshio.read(path)
    actual = check.get_cells_type(kind)
    if actual.shape != cells.shape or not np.allclose(
            check.points[actual], points[cells], atol=1e-9, rtol=1e-7 if ext == ".stl" else 1e-12):
        raise ValueError("Exported geometry differs from the project")
    if ext == ".stl":
        triangles = check.points[actual]
        if np.any(np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],
                                          triangles[:,2]-triangles[:,0]), axis=1) == 0):
            raise ValueError("STL conversion produced degenerate triangles")
