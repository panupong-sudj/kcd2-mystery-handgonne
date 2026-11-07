"""Render the inventory icon for the rifle and compile it for KCD2.

Usage: <Blender 4.3>/blender.exe -b --python tools/make_icon.py

KCD2 item icons are 64x64 BC7 .dds (rc.exe preset UiIcon) named <IconId>_icon in Libs/UI/Textures/Icons/Items,
drawn as dark ink silhouettes on transparency. Renders the rifle side-on, laid diagonally (stock bottom-left,
muzzle top-right), flat dark colour, at 4x size then lets Blender's filter downsample, writes a .tif and runs rc.
"""
import math
import os
import sys
import subprocess

import bpy
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "source", "henry_rifle", "henry", "scene.gltf")
OUT_DIR = os.path.join(ROOT, "mod", "mystery_handgonne", "Data", "Libs", "UI", "Textures", "Icons", "Items")
ICON_ID = "mystery_handgonne"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kcd2paths import RC  # noqa: E402
SIZE = 64
INK = (0.08, 0.07, 0.06)  # near-black, slightly warm like the vanilla ink icons


def log(*a):
    print("[make_icon]", *a, flush=True)


bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
parts = [o for o in bpy.data.objects if o.type == "MESH" and o.data.materials and o.data.materials[0].name == "rifle"]
for o in list(bpy.data.objects):
    if o.type == "MESH" and o not in parts:
        bpy.data.objects.remove(o, do_unlink=True)

# Same orientation as the skin (muzzle +Y), then tilt 35 deg so the rifle runs corner to corner in a side view.
fix = Matrix.Rotation(math.radians(35), 4, "X") @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Scale(0.01, 4)
pts = []
for p in parts:
    p.data = p.data.copy()
    p.data.transform(fix @ p.matrix_world)
    p.parent = None
    p.matrix_world = Matrix.Identity(4)
    pts += [v.co.copy() for v in p.data.vertices]
lo = Vector([min(v[i] for v in pts) for i in range(3)])
hi = Vector([max(v[i] for v in pts) for i in range(3)])
centre = (lo + hi) / 2
span = max(hi.y - lo.y, hi.z - lo.z)

# Orthographic camera on +X looking at -X: screen right = +Y (muzzle), screen up = +Z.
cam_data = bpy.data.cameras.new("icon_cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = span * 1.08
cam = bpy.data.objects.new("icon_cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = (centre.x + 2.0, centre.y, centre.z)
cam.rotation_euler = (math.radians(90), 0, math.radians(90))
bpy.context.scene.camera = cam

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "FLAT"
scene.display.shading.color_type = "SINGLE"
scene.display.shading.single_color = INK
scene.display.shading.show_object_outline = False
scene.render.film_transparent = True
scene.view_settings.view_transform = "Standard"
scene.render.resolution_x = SIZE
scene.render.resolution_y = SIZE
scene.render.resolution_percentage = 100
scene.render.filter_size = 1.5
scene.render.image_settings.file_format = "TIFF"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "8"

os.makedirs(OUT_DIR, exist_ok=True)
tif = os.path.join(OUT_DIR, f"{ICON_ID}_icon.tif")
scene.render.filepath = tif
bpy.ops.render.render(write_still=True)
log("rendered", tif, "span", round(span, 3))

r = subprocess.run([RC, tif, "/preset=UiIcon", "/mipmaps=0", "/refresh"], capture_output=True, text=True)  # vanilla icons have no mips
log("rc exit", r.returncode, (r.stdout + r.stderr).strip().splitlines()[-2:])
# A PNG copy to look at outside the game.
png = os.path.join(ROOT, "work", "blender", f"{ICON_ID}_icon_preview.png")
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = scene.render.resolution_y = 256
scene.render.filepath = png
bpy.ops.render.render(write_still=True)
log("out", sorted(os.listdir(OUT_DIR)), "preview", png)
