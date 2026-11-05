"""Build inventory and corresponding application source alongside the binaries."""
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
bundle = root / "dist" / "BluntCloud"
notices = bundle / "licenses"
notices.mkdir(exist_ok=True)
packages = {}
for package in metadata.distributions():
    name = package.metadata["Name"]
    packages[name] = package.version
    for entry in package.files or []:
        if any("license" in part.lower() or part.lower().startswith("copying") for part in entry.parts):
            source = Path(package.locate_file(entry))
            if source.is_file() and ".." not in entry.parts:
                path = notices / name / entry
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(source.read_bytes())

with zipfile.ZipFile(bundle/"application-source.zip","w",zipfile.ZIP_DEFLATED) as archive:
    for folder in ("bluntcloud","tests","packaging","docs","specs"):
        for path in (root/folder).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                archive.write(path,path.relative_to(root))
    for pattern in ("*.py","*.ui","README*","LICENSE*","uv.lock","pyproject.toml"):
        for path in root.glob(pattern):
            archive.write(path,path.name)
dlls = {}
for pattern in ("*.dll","*.pyd"):
    for lib in bundle.rglob(pattern):
        with lib.open("rb") as data:
            dlls[str(lib.relative_to(bundle))] = hashlib.file_digest(data,"sha256").hexdigest()
(bundle/"inventory.json").write_text(json.dumps({"packages":packages,"native_sha256":dlls},indent=2))
