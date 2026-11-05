"""Portable project storage and one-time migration of legacy project folders."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3


def storage(project):
    root = Path(project).resolve()
    private = root / ".bluntcloud"
    private.mkdir(parents=True, exist_ok=True)
    if private.resolve() != private:
        raise ValueError("The private project directory must be inside the project")
    legacy = root / "project.sqlite"
    if not legacy.is_file():
        return private
    # Inspect read-only before relocating any files belonging to an older project.
    with closing(sqlite3.connect(legacy.as_uri()+"?mode=ro", uri=True)) as db:
        tables = {r[0] for r in db.execute("select name from sqlite_master where type='table'")}
        if not {"revisions","meshes","history"} <= tables:
            return private
        if db.execute("pragma user_version").fetchone()[0] != 1:
            raise ValueError("Unsupported legacy project version")
        folders = {json.loads(row[0]).get("cloud",{}).get("folder")
                   for row in db.execute("select recipe from revisions")}
    if (private/"project.sqlite").exists():
        raise ValueError("Both legacy and private project catalogs exist. Open a single project.")
    if any(Path(str(legacy)+suffix).exists() for suffix in ("-journal","-wal","-shm")):
        raise ValueError("Close the legacy project and recover any pending SQLite transaction first")
    for folder in sorted(f for f in folders if f):
        old = root/"clouds"/folder
        new = private/"clouds"/folder
        if (Path(folder).name != folder or old.resolve().parent != root/"clouds" or
                new.resolve() != private/"clouds"/folder):
            raise ValueError("Invalid managed cloud path")
        new.mkdir(parents=True, exist_ok=True)
        for name in ("source","points"):
            source, target = old/name, new/name
            if source.is_symlink() or target.is_symlink():
                raise ValueError("Unexpected link in managed cloud storage")
            if source.is_file() and not target.exists():
                source.rename(target)
            elif not target.is_file() or source.exists():
                raise ValueError("Missing or conflicting managed cloud file during migration")
        if old.is_dir() and not any(old.iterdir()):
            old.rmdir()
    legacy.rename(private/"project.sqlite")
    if (root/"clouds").is_dir() and not any((root/"clouds").iterdir()):
        (root/"clouds").rmdir()
    return private
