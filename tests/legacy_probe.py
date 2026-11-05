"""Run from the repository root with python -m tests.legacy_probe."""
import numpy as np
import shapely
from shapely.geometry import box
from Polygons2FEM import make_mesh


def probe(origin,side,step,levels):
    z = np.asarray(levels)
    polygon = box(origin,origin,origin+side,origin+side)
    _,nodes,cells = make_mesh(step,step,origin,origin,origin+side,origin+side,z,
                              {level:polygon for level in z})
    xyz = nodes[:,1:].astype(np.float64)
    rows = cells[:,1:].astype(int)-1
    points = xyz[rows]
    volumes = np.linalg.det(np.stack([points[:,i]-points[:,0] for i in (1,3,4)],axis=1))
    print("numpy",np.__version__,"shapely",shapely.__version__,"nodes",len(nodes),
          "positions",len(np.unique(xyz,axis=0)),"zero volume",int((volumes==0).sum()))

if __name__ == "__main__":
    probe(0,1,.2,[.1,.3,.5])
    probe(1e6,.1,.01,[0,.1])
