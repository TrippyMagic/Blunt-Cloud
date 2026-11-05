"""Build an orthogonal grid variant from observed point occupancy."""
from collections import defaultdict
from math import ceil

import numpy as np
from shapely import box, union_all
from shapely.geometry import Polygon

from .application import catalog, current, publish_variant
from .cloud import CHUNK, load_cloud


def grid_volume(project, base, roof, spacing, step, min_points=1, fill=False, full_height=False):
    with catalog(project) as db:
        expected = current(db)[0]
    cloud, points = load_cloud(project)
    if full_height:
        base = float(np.min(points[:,2]))
        roof = float(np.max(points[:,2]))
        if base == roof:
            base, roof = base-spacing/2, roof+spacing/2
    if (not np.isfinite([base, roof, spacing, step]).all() or
            roof <= base or min(step, spacing) <= 0 or min_points < 1):
        raise ValueError("Check the clipping heights, grid spacing and minimum point count")
    depth = ceil((roof-base)/spacing)
    if depth > 10000:
        raise ValueError("Increase Z spacing or reduce the clipping range")
    counts = defaultdict(int)
    for start in range(0, len(points), CHUNK):
        block = points[start:start+CHUNK]
        sample = block[(block[:,2] >= base) & (block[:,2] <= roof)]
        if not len(sample):
            continue
        indices = np.floor((sample-[0,0,base])/[step,step,spacing])
        if np.max(np.abs(indices)) >= 2**52:
            raise ValueError("Grid indices exceed coordinate precision")
        indices[:,2] = np.clip(indices[:,2], 0, depth-1)
        keys, hits = np.unique(indices.astype(np.int64),axis=0,return_counts=True)
        for key, n in zip(keys.tolist(),hits.tolist()):
            counts[tuple(key)] += n
        if len(counts) > 1_000_000:
            raise ValueError("Too many occupied cells. Increase the spacing.")
    layers = defaultdict(list)
    for (x,y,k), hits in counts.items():
        if hits >= min_points:
            layers[k].append((x,y))
    if not layers:
        raise ValueError("No occupied cells meet the clipping and point-count settings")
    edges = [base + i*spacing for i in range(depth)] + [roof]
    sections = []
    for k in range(depth):
        polygons = []
        if k in layers:
            # Dissolve in integer space so neighbouring squares share exact edges.
            xy = np.array(layers[k])
            shape = union_all(box(xy[:,0],xy[:,1],xy[:,0]+1,xy[:,1]+1))
            parts = [shape] if shape.geom_type == "Polygon" else list(shape.geoms)
            if fill:
                shape = union_all([Polygon(p.exterior) for p in parts])
                parts = [shape] if shape.geom_type == "Polygon" else shape.geoms
            for part in parts:
                polygons.append({"outer":(np.asarray(part.exterior.coords)[:-1]*step).tolist(),
                                 "holes":[(np.asarray(h.coords)[:-1]*step).tolist() for h in part.interiors]})
        sections.append({"z":(edges[k]+edges[k+1])/2,"polygons":polygons,
                         "status":"approved" if polygons else "empty"})
    recipe = dict(cloud=cloud, extent=[base,roof], step=step, spacing=spacing,
                  min_points=min_points, full_height=full_height, layer_edges=edges, fill=fill,
                  proposal="point-occupancy", sections=sections)
    return publish_variant(project,expected,recipe)
