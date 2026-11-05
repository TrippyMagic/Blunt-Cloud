"""Revision-controlled local section projects."""
import hashlib
import io
import json
import sqlite3
from contextlib import closing, contextmanager

import numpy as np

from .domain import VolumeMesh, mesh
from .storage import storage


@contextmanager
def catalog(project):
    path = storage(project)
    with closing(sqlite3.connect(path / "project.sqlite")) as db, db:
        version = db.execute("pragma user_version").fetchone()[0]
        if version not in (0, 1):
            raise ValueError(f"Unknown project version: {version}")
        db.execute("create table if not exists revisions(id integer primary key, recipe text not null)")
        db.execute("create table if not exists meshes(revision integer primary key, digest text, data blob)")
        db.execute("pragma user_version=1")
        db.execute("create table if not exists history(revision integer primary key, previous integer, redo integer)")
        db.execute("create table if not exists variants(revision integer primary key)")
        yield db


def revise(project, recipe, expected=None):
    payload = json.dumps(recipe, allow_nan=False, sort_keys=True)
    with catalog(project) as db:
        db.execute("begin immediate")
        previous = db.execute("select max(id) from revisions").fetchone()[0]
        if expected is not None and (previous or 0) != expected:
            raise ValueError("The project changed during the operation")
        return append_revision(db,payload,previous,None)


def append_revision(db,payload,previous,redo):
    revision = db.execute("insert into revisions(recipe) values (?)",(payload,)).lastrowid
    db.execute("insert into history values (?,?,?)",(revision,previous,redo))
    return revision


def navigate(project, direction):
    with catalog(project) as db:
        db.execute("begin immediate")
        head = current(db)[0]
        history = db.execute("select previous,redo from history where revision=?",(head,)).fetchone()
        target = history[0 if direction == "undo" else 1] if history else None
        if target is None:
            raise ValueError("No further history available")
        payload = db.execute("select recipe from revisions where id=?",(target,)).fetchone()[0]
        older = db.execute("select previous,redo from history where revision=?",(target,)).fetchone()
        if direction == "undo":
            return append_revision(db,payload,older[0] if older else None,head)
        return append_revision(db,payload,head,older[1] if older else None)


def current(db):
    row = db.execute("select id,recipe from revisions order by id desc limit 1").fetchone()
    if not row:
        raise ValueError("The project has no sections")
    return row


def generate(project):
    with catalog(project) as db:
        revision, recipe = current(db)
    data = validated_payload(json.loads(recipe))
    with catalog(project) as db:
        db.execute("begin immediate")
        if current(db)[0] != revision:
            raise ValueError("The input revision changed during meshing")
        store_mesh(db, revision, data)
    return revision


def validated_payload(recipe):
    result = mesh(recipe)
    from .validation import quality
    quality(result)
    stream = io.BytesIO()
    np.savez(stream, **vars(result))
    return stream.getvalue()


def store_mesh(db, revision, data):
    db.execute("insert or replace into meshes values (?,?,?)",
               (revision, hashlib.sha256(data).hexdigest(), data))


def publish_variant(project, expected, recipe):
    data = validated_payload(recipe)
    with catalog(project) as db:
        db.execute("begin immediate")
        if current(db)[0] != expected:
            raise ValueError("The project changed during automatic generation")
        revision = append_revision(db, json.dumps(recipe, allow_nan=False), expected, None)
        store_mesh(db, revision, data)
        db.execute("insert into variants values (?)",(revision,))
        return revision


def read_mesh(db):
    revision, _ = current(db)
    row = db.execute("select digest,data from meshes where revision=?", (revision,)).fetchone()
    if not row:
        raise ValueError("Generate a mesh for the current revision first")
    digest, data = row
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("Mesh integrity check failed")
    with np.load(io.BytesIO(data), allow_pickle=False) as arrays:
        return VolumeMesh(**{name: arrays[name] for name in VolumeMesh.__annotations__})





def saved_grids(project):
    with catalog(project) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute("""select id, json_extract(recipe,'$.cloud.filename') as source,
            json_extract(recipe,'$.step') as xy, json_extract(recipe,'$.spacing') as z,
            json_extract(recipe,'$.extent[0]') as base, json_extract(recipe,'$.extent[1]') as roof,
            json_extract(recipe,'$.min_points') as minimum, json_extract(recipe,'$.fill') as filled
            from variants join revisions on id=revision order by id desc""")
        return [dict(row) for row in rows]


def restore_variant(project, target, expected):
    with catalog(project) as db:
        db.execute("begin immediate")
        head, _ = current(db)
        if head != expected:
            raise ValueError("The project changed before variant selection")
        row = db.execute("select r.recipe from revisions r join variants v on v.revision=r.id where r.id=?",
                         (target,)).fetchone()
        if not row:
            raise ValueError("Unknown saved grid variant")
        revision = append_revision(db, row[0], head, None)
        copied = db.execute("insert into meshes select ?,digest,data from meshes where revision=?",
                            (revision,target))
        if copied.rowcount != 1:
            raise ValueError("Missing saved grid mesh")
        return revision
