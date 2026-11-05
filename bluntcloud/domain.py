"""Structured HEX8 mesh in local metres. Input rings use local XY coordinates."""
from dataclasses import dataclass
from math import ceil, floor, isfinite

import numpy as np
from shapely import contains_xy
from shapely.geometry import MultiPolygon, Polygon


CORNERS = ((0,0,0), (1,0,0), (1,1,0), (0,1,0),
           (0,0,1), (1,0,1), (1,1,1), (0,1,1))
FACES = ((3,2,1,0), (4,5,6,7), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7))


@dataclass(frozen=True)
class VolumeMesh:
    points: np.ndarray
    cells: np.ndarray
    boundary: np.ndarray
    layers: np.ndarray
    volume: float


def mesh(recipe):
    if not recipe.get("sections"):
        raise ValueError("Create sections and review their rings before generating a volume.")
    if "step" not in recipe:
        raise ValueError("The section recipe is missing its XY grid spacing (step).")
    step = float(recipe["step"])
    base, roof = map(float, recipe["extent"])
    sections = recipe["sections"]
    levels = np.asarray([s["z"] for s in sections], dtype=np.float64)
    if not isfinite(step) or step <= 0 or not levels.size or not np.isfinite(levels).all():
        raise ValueError("Grid spacing and sample heights must be finite; spacing must be positive")
    if not (isfinite(base) and isfinite(roof) and base < roof and
            base <= levels[0] and levels[-1] <= roof and (np.diff(levels) > 0).all()):
        raise ValueError("Sample heights must increase within the specified base and roof")
    edges = np.r_[base, levels[:-1] + np.diff(levels)/2, roof]
    nodes, cells, boundary, layers = {}, [], {}, []
    volume = 0.0
    candidates = 0
    for k, section in enumerate(sections):
        parts = section["polygons"]
        if section["status"] == "empty" and not parts:
            continue
        if section["status"] != "approved" or not parts:
            raise ValueError(f"Section {k} requires material review")
        polygons = [Polygon(p["outer"], p.get("holes", [])) for p in parts]
        shape = MultiPolygon(polygons)
        if shape.is_empty or not shape.is_valid or any(p.area <= 0 for p in polygons):
            raise ValueError(f"Section {k} contains invalid rings")
        for polygon in polygons:
            x0,y0,x1,y1 = polygon.bounds
            xs = range(floor(x0/step), ceil(x1/step))
            ys = range(floor(y0/step), ceil(y1/step))
            candidates += len(xs)*len(ys)
            if candidates > 1_000_000:
                raise ValueError("The grid exceeds one million candidate cells. Increase the grid spacing.")
            count = 0
            for i in xs:
                mask = contains_xy(polygon, (i+.5)*step, (np.arange(ys.start,ys.stop)+.5)*step)
                for j in np.flatnonzero(mask) + ys.start:
                    row = [nodes.setdefault((i+di,int(j)+dj,k+dk), len(nodes))
                           for di,dj,dk in CORNERS]
                    cells.append(row)
                    layers.append(k)
                    for face in FACES:
                        oriented = tuple(row[v] for v in face)
                        key = tuple(sorted(oriented))
                        if key in boundary:
                            del boundary[key]
                        else:
                            boundary[key] = oriented
                    count += 1
            if not count:
                raise ValueError(f"Section {k} loses a component at this resolution")
            volume += count * step**2 * (edges[k+1]-edges[k])
    points = [(i*step,j*step,edges[k]) for i,j,k in nodes]
    return VolumeMesh(np.asarray(points,dtype=np.float64).reshape(-1,3),
                      np.asarray(cells,dtype=np.int64).reshape(-1,8),
                      np.asarray(list(boundary.values()),dtype=np.int64).reshape(-1,4),
                      np.asarray(layers,dtype=np.int64), float(volume))
