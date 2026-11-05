"""Managed survey imports. Binary payloads stay on disk."""
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import tempfile

import numpy as np
from plyfile import PlyData
from shapely import MultiPoint

from .application import catalog, current, revise

CHUNK = 65536


def pcd_chunks(file):
    header = {}
    while True:
        line = file.readline(8192)
        if not line or len(line) == 8192:
            raise ValueError("Incomplete PCD header")
        fields = line.decode("ascii").split()
        if not fields or fields[0].startswith("#"):
            continue
        header[fields[0].upper()] = fields[1:]
        if fields[0].upper() == "DATA":
            break
    names = header["FIELDS"]
    counts = list(map(int, header.get("COUNT", ["1"] * len(names))))
    columns = []
    indices = {}
    offset = 0
    for i,(name,kind,size,count) in enumerate(zip(names,header["TYPE"],header["SIZE"],counts, strict=True)):
        if count < 1:
            raise ValueError("Invalid PCD COUNT")
        dtype = "<" + {"F":"f","U":"u","I":"i"}[kind] + size
        columns.append((f"field{i}", dtype, (count,)))
        indices[name] = (i,offset,count)
        offset += count
    axes = [indices[key] for key in "xyz"]
    if any(count != 1 for _,_,count in axes):
        raise ValueError("PCD coordinates must be scalar fields")
    remaining = int(header["POINTS"][0])
    mode = header["DATA"][0]
    while remaining > 0:
        n = min(CHUNK,remaining)
        if mode == "binary":
            rows = np.fromfile(file,dtype=np.dtype(columns),count=n)
            xyz = np.column_stack([rows[f"field{i}"][:,0] for i,_,_ in axes])
        elif mode == "ascii":
            rows = list(itertools.islice(file,n))
            xyz = np.loadtxt(rows,usecols=[col for _,col,_ in axes],ndmin=2)
        else:
            raise ValueError(f"Unsupported PCD variant: {mode}")
        if len(xyz) != n:
            raise ValueError("Truncated PCD payload")
        yield xyz
        remaining -= n
    if file.read(1):
        raise ValueError("PCD payload exceeds the declared point count")


def chunks(file, suffix):
    if suffix == ".pcd":
        yield from pcd_chunks(file)
    elif suffix == ".ply":
        header = PlyData.read(file.name)
        if "face" in header:
            raise ValueError("This PLY contains faces. Select a point cloud.")
        points = header["vertex"]
        for start in range(0,points.count,CHUNK):
            yield np.column_stack([points[key][start:start+CHUNK] for key in "xyz"])
    elif suffix in {".xyz",".txt"}:
        while lines := list(itertools.islice(file,CHUNK)):
            points = np.loadtxt(lines,ndmin=2)
            if points.shape[1] != 3:
                raise ValueError("Expected three columns: X Y Z")
            yield points
    else:
        raise ValueError("Unsupported input format")


def import_cloud(project, source, unit):
    scale = {"m":1., "mm":.001, "cm":.01}[unit]
    project, source = Path(project), Path(source)
    project.mkdir(parents=True,exist_ok=True)
    with catalog(project) as db:
        expected = db.execute("select coalesce(max(id),0) from revisions").fetchone()[0]
    size = source.stat().st_size
    if shutil.disk_usage(project).free < 2*1024**3 + size:
        raise ValueError("Insufficient disk space to import the source")
    directory = project / "clouds"
    directory.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=directory) as staging:
        raw = Path(staging) / "source"
        shutil.copyfile(source,raw)
        with raw.open("rb") as file:
            digest = hashlib.file_digest(file,"sha256").hexdigest()
        target = directory / (digest + "-" + unit + source.suffix.lower())
        count = 0
        with raw.open("rb") as file, (Path(staging)/"points").open("wb") as out:
            for points in chunks(file,source.suffix.lower()):
                xyz = np.asarray(points,dtype="<f8")
                if not xyz.size or not np.isfinite(xyz).all():
                    raise ValueError("Coordinates must be present and finite")
                if not count:
                    origin = xyz[0].copy()
                ((xyz-origin)*scale).tofile(out)
                count += len(xyz)
        if not count:
            raise ValueError("Empty point cloud")
        metadata = dict(hash=digest,folder=target.name,unit=unit,origin=origin.tolist(),
                        count=count,filename=source.name)
        if not target.exists():
            os.rename(staging,target)
        revise(project,{"cloud":metadata},expected)
    return metadata


def load_cloud(project):
    with catalog(project) as db:
        metadata = json.loads(current(db)[1]).get("cloud")
        if metadata is None:
            raise ValueError("Import a point cloud first")

    directory = (Path(project)/"clouds").resolve()
    path = (directory/metadata["folder"]/"points").resolve()
    if not path.is_relative_to(directory):
        raise ValueError("Source path is outside the project")
    return metadata,np.memmap(path,mode="r",dtype="<f8",shape=(metadata["count"],3))


def propose(project, base, roof, spacing, thickness, step):
    with catalog(project) as db:
        expected = current(db)[0]
    metadata, points = load_cloud(project)
    if not all(np.isfinite([base,roof,spacing,thickness,step])) or min(spacing,thickness,step)<=0 or roof<=base:
        raise ValueError("Invalid section parameters")
    if (roof-base)/spacing > 10000:
        raise ValueError("Too many sections")
    sections = []
    for z in np.arange(base+spacing/2,roof,spacing):
        samples = []
        count = 0
        for start in range(0,len(points),CHUNK):
            block = points[start:start+CHUNK]
            band = block[(block[:,2]>=z-thickness/2)&(block[:,2]<z+thickness/2),:2]
            count += len(band)
            if count > 500000:
                raise ValueError("Too many points in the band. Reduce its thickness.")
            if len(band):
                samples.append(band)
        polygons = []
        if count >= 3:
            hull = MultiPoint(np.concatenate(samples)).convex_hull
            if hull.geom_type == "Polygon":
                polygons.append({"outer":list(hull.exterior.coords)[:-1],"holes":[]})
        sections.append(dict(z=float(z),status="review",polygons=polygons,samples=count))
    if not sections:
        raise ValueError("No sample heights within the specified extent")
    return revise(project,dict(cloud=metadata,extent=[base,roof],step=step,thickness=thickness,
                               spacing=spacing,proposal="convex-hull",sections=sections), expected)




