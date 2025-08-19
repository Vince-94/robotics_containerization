from setuptools import setup, Extension
from Cython.Build import cythonize
from pathlib import Path
import shutil
import zipfile


# Project root
ROOT = Path(__file__).parent.resolve()
SRC_DIR = ROOT / "src"
BUILD_C_DIR = ROOT / "build"
LIB_DIR = ROOT / "install"


# Collect all Python sources inside src/ (except __init__.py)
ext_modules = []
for py_file in SRC_DIR.rglob("*.py"):
    if py_file.name == "__init__.py":
        continue

    # Module name = relative path from SRC_DIR, with dots instead of /
    rel_path = py_file.relative_to(ROOT).with_suffix("")
    module_name = ".".join(rel_path.parts)

    ext_modules.append(
        Extension(
            name=module_name,
            sources=[str(py_file)],
        )
    )

setup(
    name="robotics_container",
    ext_modules=cythonize(
        ext_modules,
        compiler_directives={"language_level": "3"},
        build_dir=str(ROOT / "build"),  # where .c files go
    ),
    # compiled .so will be placed under --build-lib destination
    script_args=["build_ext", f"--build-lib={LIB_DIR}"],  # place .so in lib/
    zip_safe=False,
)

# Remove build directory if it exists
if BUILD_C_DIR.exists():
    shutil.rmtree(BUILD_C_DIR)


#! Compress the build directory to a tar.gz file
# Create dist folder
DIST_DIR = ROOT / "dist"
DIST_DIR.mkdir(exist_ok=True)

# Zip filename (optionally include arch or python tag)
zip_name = f"robotics_container.zip"
zip_path = DIST_DIR / zip_name

print(f"Creating ZIP archive (excluding src/) -> {zip_path}")

with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in ROOT.rglob("*"):
        # skip directories in the iteration (we only add files)
        if path.is_dir():
            continue
        # compute relative path from project root
        try:
            rel = path.relative_to(ROOT)
        except Exception:
            continue
        # skip the .git/ directory entirely
        if rel.parts and rel.parts[0] == ".git":
            continue
        # skip the .gitignore file
        if rel.parts and rel.parts[0] == ".gitignore":
            continue
        # skip the src/ directory entirely
        if rel.parts and rel.parts[0] == "src":
            continue
        # skip this current script
        if rel.parts and rel.parts[0] == "setup_cython.py":
            continue
        # Optionally skip the dist/ zip itself if rerun
        if rel.parts and rel.parts[0] == "dist" and path == zip_path:
            continue
        # Add file preserving relative path
        zf.write(path, arcname=str(rel))

print("ZIP creation complete.")
print(f"Archive located at: {zip_path}")
