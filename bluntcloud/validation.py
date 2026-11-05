"""Topology and quality checks for axis-aligned HEX8 from the structured mesher."""
from collections import defaultdict

import numpy as np


def quality(mesh):
    if not len(mesh.cells):
        return {"components":0, "min_jacobian":None, "max_aspect_ratio":None}
    if mesh.cells.min()<0 or mesh.cells.max()>=len(mesh.points):
        raise ValueError("Node reference out of range")
    parent = list(range(len(mesh.cells)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    from .domain import FACES
    faces = {}
    min_jac = float("inf")
    max_aspect = 1.
    for index,row in enumerate(mesh.cells):
        corners = mesh.points[row]
        lengths = np.array([corners[1,0]-corners[0,0],corners[3,1]-corners[0,1],
                            corners[4,2]-corners[0,2]])
        if not np.isfinite(lengths).all() or min(lengths)<=0 or len(set(row))!=8:
            raise ValueError(f"Degenerate cell {index}")
        min_jac = min(min_jac,float(lengths.prod()/8))
        max_aspect = max(max_aspect,float(max(lengths)/min(lengths)))
        for face in FACES:
            key = tuple(sorted(row[i] for i in face))
            if key in faces:
                parent[root(index)] = root(faces.pop(key))
            else:
                faces[key] = index
    # Each vertex link of a closed quad surface must be a single cycle.
    links = defaultdict(list)
    directed = set()
    for quad in mesh.boundary:
        for i,v in enumerate(quad):
            a,b = quad[i-1],quad[(i+1)%4]
            if (v,b) in directed:
                raise ValueError(f"Non-manifold edge at node {v}")
            directed.add((v,b))
            links[v].append((a,b))
    if any((b,a) not in directed for a,b in directed):
        raise ValueError("Open boundary surface")
    for v,edges in links.items():
        following = dict(edges)
        first = cursor = edges[0][0]
        for _ in range(len(edges)):
            cursor = following.pop(cursor,None)
            if cursor is None:
                raise ValueError(f"Point-only contact at node {v}")
        if cursor != first or following:
            raise ValueError(f"Non-manifold boundary at node {v}")
    return {"components":len({root(i) for i in range(len(parent))}),
            "min_jacobian":min_jac,"max_aspect_ratio":max_aspect}
