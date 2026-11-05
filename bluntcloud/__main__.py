import argparse
import json
import errno
import os
import sys
from pathlib import Path

from .application import catalog, generate, read_mesh, revise


def main():
    os.environ["LANGUAGE"] = "en"
    parser = argparse.ArgumentParser(prog="bluntcloud")
    parser.add_argument("project", type=Path)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("sections").add_argument("recipe", type=Path)
    imp = commands.add_parser("import")
    imp.add_argument("source", type=Path)
    imp.add_argument("unit", choices=["m","cm","mm"])
    section = commands.add_parser("propose")
    for parameter in ("base","roof","spacing","thickness","step"):
        section.add_argument(parameter,type=float)
    grid = commands.add_parser("grid-volume")
    for parameter in ("base","roof","spacing","step"):
        grid.add_argument(parameter,type=float)
    grid.add_argument("--min-points",type=int,default=1)
    grid.add_argument("--full-height",action="store_true")
    grid.add_argument("--fill",action="store_true")
    restore = commands.add_parser("restore-grid")
    restore.add_argument("revision",type=int)
    restore.add_argument("expected",type=int)
    commands.add_parser("generate")
    commands.add_parser("inspect")
    commands.add_parser("grids")
    commands.add_parser("recipe")
    commands.add_parser("undo")
    commands.add_parser("redo")
    commands.add_parser("preview").add_argument("destination",type=Path)
    export = commands.add_parser("export")
    export.add_argument("destination", type=Path)
    export.add_argument("--accept-loss", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "import":
            from .cloud import import_cloud
            result = import_cloud(args.project,args.source,args.unit)
        elif args.action == "grid-volume":
            from .automatic import grid_volume
            result = {"revision":grid_volume(args.project,args.base,args.roof,args.spacing,args.step,
                                               args.min_points,args.fill,args.full_height)}
        elif args.action == "grids":
            from .application import saved_grids
            result = saved_grids(args.project)
        elif args.action == "restore-grid":
            from .application import restore_variant
            result = {"revision":restore_variant(args.project,args.revision,args.expected)}
        elif args.action == "propose":
            from .cloud import propose
            result = {"revision": propose(args.project,args.base,args.roof,args.spacing,args.thickness,args.step)}
        elif args.action in {"undo","redo"}:
            from .application import navigate
            result = {"revision":navigate(args.project,args.action)}
        elif args.action == "preview":
            import numpy as np
            with catalog(args.project) as db:
                surface = read_mesh(db)
                stride = max(1,(len(surface.boundary)+99999)//100000)
                with args.destination.open("xb") as file:
                    np.save(file,surface.points[surface.boundary[::stride]].astype("float32"))
            result = {"stride":stride}
        elif args.action == "recipe":
            from .application import current
            with catalog(args.project) as db:
                result = json.loads(current(db)[1])
        elif args.action == "sections":
            result = {"revision": revise(args.project, json.loads(args.recipe.read_text("utf-8-sig")))}
        elif args.action == "generate":
            result = {"revision": generate(args.project)}
        elif args.action == "inspect":
            with catalog(args.project) as db:
                from .validation import quality
                mesh = read_mesh(db)
                result = {**quality(mesh), "nodes": len(mesh.points), "cells": len(mesh.cells),
                          "faces": len(mesh.boundary), "volume_m3": float(mesh.volume)}
        else:
            from .adapters import export
            export(args.project, args.destination, args.accept_loss)
            result = {"file": str(args.destination)}
        print(json.dumps(result))
    except OSError as exc:
        name = errno.errorcode.get(exc.errno, "IO_ERROR")
        parser.exit(2, f"File operation failed ({name}): {exc.filename or args.project}\n")
    except (ValueError, TypeError, KeyError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()




