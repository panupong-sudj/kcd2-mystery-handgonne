"""Build mystery_handgonne_round.cgf: the loaded round / flying projectile, drawn with a Nodraw material.

Usage: <Blender 4.3>/blender.exe -b --python tools/blender_make_round.py

Why: the game snaps the loaded round onto bone Crossbow_arrow (on the sight line, above our barrel) and
ignores attachment offsets, and it also ignores the Ammo row's Material for the loaded round. So the round's
own .cgf must carry the invisible material. BCry names the material library after the export node and writes
<node>.mtl next to the .cgf; this script then rewrites that .mtl with Shader="Nodraw".
"""
import os
import sys
import time

import bmesh
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work", "blender")
OUT_DIR = os.path.join(ROOT, "mod", "mystery_handgonne", "Data", "Objects", "weapons", "mystery_handgonne")
NAME = "mystery_handgonne_round"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kcd2paths import RC  # noqa: E402
RADIUS = 0.004  # 8 mm, rifle-bullet sized; it is never drawn anyway

MTL = """<Material MtlFlags="524544">
 <SubMaterials>
  <Material Name="round" MtlFlags="525312" Shader="Nodraw" GenMask="0" SurfaceType="" MatTemplate="" Diffuse="1,1,1" Specular="0,0,0" Opacity="1" Shininess="10">
   <Textures />
  </Material>
 </SubMaterials>
</Material>
"""


def log(*a):
    print("[make_round]", *a, flush=True)


from io_bcry_exporter.configuration import Configuration
if Configuration.rc_path != RC:
    Configuration.rc_path = RC
    Configuration.save()

bpy.ops.wm.read_homefile(use_empty=True)
me = bpy.data.meshes.new(NAME)
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=RADIUS)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.to_mesh(me)
bm.free()
obj = bpy.data.objects.new(NAME, me)
bpy.context.scene.collection.objects.link(obj)
mat = bpy.data.materials.new(NAME + "__01__round__physNone")
me.materials.append(mat)

for o in bpy.context.scene.objects:
    o.select_set(o == obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.bcry.add_cry_export_node(node_type="cgf", node_name=NAME)
log("export nodes", [c.name for c in bpy.data.collections])

os.makedirs(WORK, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, NAME + ".blend"))
cgf = os.path.join(OUT_DIR, NAME + ".cgf")
if os.path.exists(cgf):
    os.remove(cgf)
bpy.ops.bcry.export_to_game(filepath=os.path.join(OUT_DIR, NAME + ".dae"))
for _ in range(180):  # BCry runs rc.exe in the background
    if os.path.isfile(cgf) and os.path.getsize(cgf) > 0:
        time.sleep(2)
        break
    time.sleep(1)

mtl = os.path.join(OUT_DIR, NAME + ".mtl")
log("generated mtl", open(mtl).read() if os.path.isfile(mtl) else None)
with open(mtl, "w", encoding="ascii") as f:
    f.write(MTL)
log("out dir", sorted(os.listdir(OUT_DIR)))
log("RESULT", "OK" if os.path.isfile(cgf) else "NO CGF", cgf)
sys.exit(0 if os.path.isfile(cgf) else 1)
