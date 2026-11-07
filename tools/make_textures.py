"""Convert the rifle's glTF metal/roughness textures to KCD2's spec/gloss set and compile them to .dds.

Usage: <Blender 4.3>/blender.exe -b --python tools/make_textures.py

KCD2 (CryEngine Illum shader) wants:
  <name>_diff  albedo; metal parts must be black (their colour lives in the specular map)
  <name>_spec  specular colour: 0.04 (4% reflectance) for non-metal, the base colour for metal
  <name>_ddna  normal map in RGB + gloss (1 - roughness) in alpha
glTF metallicRoughness: G = roughness, B = metallic. Writes .tif sources next to the mod's model and runs rc.exe
with the matching preset; tools/build.py skips the .tif files so only the .dds go into the pak.
"""
import os
import sys
import subprocess

import bpy
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "source", "henry_rifle", "henry", "textures")
OUT_DIR = os.path.join(ROOT, "mod", "mystery_handgonne", "Data", "Objects", "weapons", "mystery_handgonne")
NAME = "mystery_handgonne"
SRC = "rifle"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kcd2paths import RC  # noqa: E402


def log(*a):
    print("[make_textures]", *a, flush=True)


def load(name, colorspace):
    img = bpy.data.images.load(os.path.join(TEX, name))
    img.colorspace_settings.name = colorspace
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(h, w, 4), (w, h)


def save_tif(arr, size, path, colorspace):
    w, h = size
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=True, float_buffer=False)
    img.colorspace_settings.name = colorspace
    img.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "TIFF"
    img.save()
    log("wrote", path)


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)


# Read everything as raw numbers ("Non-Color") and do the colour maths ourselves.
base, size = load(f"{SRC}_baseColor.png", "Non-Color")
mr, _ = load(f"{SRC}_metallicRoughness.png", "Non-Color")
nrm, _ = load(f"{SRC}_normal.png", "Non-Color")
rough = mr[..., 1:2]
metal = mr[..., 2:3]

diff = base.copy()
diff[..., :3] = base[..., :3] * (1.0 - metal)
diff[..., 3] = 1.0

spec = base.copy()
spec[..., :3] = lin_to_srgb(0.04 * (1.0 - metal) + srgb_to_lin(base[..., :3]) * metal)
spec[..., 3] = 1.0

ddna = nrm.copy()
ddna[..., 3] = 1.0 - rough[..., 0]

jobs = [("diff", diff, "Albedo"), ("spec", spec, "Reflectance"), ("ddna", ddna, "NormalsWithSmoothness")]
for suffix, arr, preset in jobs:
    tif = os.path.join(OUT_DIR, f"{NAME}_{suffix}.tif")
    save_tif(arr, size, tif, "Non-Color")
    r = subprocess.run([RC, tif, f"/preset={preset}", "/refresh"], capture_output=True, text=True)
    log("rc", suffix, "exit", r.returncode, (r.stdout + r.stderr).strip().splitlines()[-3:])
log("out dir", sorted(f for f in os.listdir(OUT_DIR) if f.startswith(NAME)))
