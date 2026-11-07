"""Build mystery_handgonne.skin (the gun body) in Blender 4.3 (KCD2 Toolkit + BCry Exporter) without the GUI.

Usage: <Blender 4.3>/blender.exe -b --python tools/blender_make_skin.py

Source model: "Henry Lever-Action Rifle" by Zverev Kirill, CC BY 4.0 (source/henry_rifle/CREDITS.md),
glTF in source/henry_rifle/henry/. TARGET picks the vanilla skeleton the gun is skinned to:
  "crossbow"  (used): weapon class 10 item on crossbow.chr, aims and reloads like a crossbow
  "handgonne" (tried and dropped: the handgonne aiming did not work for this gun): class 13 item on
              hand_cannon.chr
Steps:
  - import the skeleton's armature from a vanilla .skin (bone names must match the .chr)
  - import the rifle glTF, keep only the parts using material "rifle" (drops the cartridge box/bullets props)
  - cm -> m, turn 180 deg about Z (muzzle +Y, up +Z), then placement() for the TARGET
  - join, triangulate, weight every vertex to the skeleton's root bone, parent to the armature
  - export as a .skin export node straight into the mod
"""
import math
import os
import shutil
import sys
import time

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "work", "blender_ref")
SRC = os.path.join(ROOT, "source", "henry_rifle", "henry", "scene.gltf")
WORK = os.path.join(ROOT, "work", "blender")
IMPORT_DIR = os.path.join(WORK, "import")  # the toolkit writes .dae/.glb next to what it imports
OUT_DIR = os.path.join(ROOT, "mod", "mystery_handgonne", "Data", "Objects", "weapons", "mystery_handgonne")
NAME = "mystery_handgonne"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kcd2paths import RC  # noqa: E402
KEEP_MATERIAL = "rifle"
TARGET = "crossbow"
MUZZLE_SRC = (0.0, 0.498, 0.1835)  # barrel tip in the turned/scaled rifle (muzzle +Y, up +Z)

if TARGET == "crossbow":
    SKELETON_SKIN, SKELETON_MTL, ROOT_BONE = "crossbow_medium_b.skin", "crossbow_medium_b_m01.mtl", "Asset_Crossbow"
    # Placement against crossbow.chr (tools/bones.py, measured profiles): rifle sight line z ~0.205, wrist
    # z ~0.07..0.15; crossbow aim line = bolt on Crossbow_arrow z 0.060, grip z -0.014..+0.057, trigger_end
    # y -0.152. A rifle's sights sit higher above its grip than a crossbow's bolt, so both cannot match; the
    # sight line goes onto the bolt line (dz -0.14), the barrel sits where the left hand holds the crossbow and
    # the wrist ~5 cm under the right hand; dy +0.03 puts the wrist over the trigger grip. (Pitching it -7 deg
    # to line the sights up on screen made shots stray.)
    # Sighting in, from aiming screenshots 1084 px tall:
    #   z -0.14: rear aperture on screen centre, front sight 159 px above, real point of impact 249 px above.
    #   z -0.08 (+6 cm, assuming the rear sight 0.26 m from the eye): the rear sight sat right in front of the eye
    #            and the gun filled the screen. The rear sight's width on screen (~180 px) puts it only ~0.12 m
    #            from the eye.
    # With the rear sight ~0.12 m and the front ~0.57 m away: the shot flies along the bore (12-13 deg above the
    # screen centre, the same as the sight line's tilt), and the sight line passes ~2.5 cm under the eye.
    # Raising the gun 2.5 cm puts the eye on the sight line, so front post and rear aperture line up on the point
    # of impact.
    #   z -0.115: the rear sight and receiver sit right over the point of impact, so the target is hidden.
    #   (Sliding it 12 cm forward was the wrong fix: the user wants it a little lower, not further away.)
    #   z -0.13: between the clear view of -0.14 and the blocked view of -0.115.
    OFFSET = (0.0, 0.03, -0.13)

    def placement():
        return Matrix.Translation(OFFSET)
else:
    SKELETON_SKIN, SKELETON_MTL, ROOT_BONE = "hand_cannon_a.skin", "hand_cannon_a.mtl", "Asset_Hand_Cannon"
    # Placement against hand_cannon.chr: root at the origin, barrel along +Z, muzzle bone hand_cannon_barrel at
    # z 0.561, touch hole hand_cannon_candle at y -0.021 (top of the gun is -Y), butt bone at z -0.425 (0.99 m,
    # same as the Henry). +90 deg about X sends +Y -> +Z and +Z -> -Y; the shift puts the barrel on the axis and
    # the muzzle on hand_cannon_barrel.
    BARREL_SHIFT = (0.0, 0.1835, 0.561 - 0.498)

    def placement():
        return Matrix.Translation(BARREL_SHIFT) @ Matrix.Rotation(math.radians(90), 4, "X")


def log(*a):
    print("[make_skin]", *a, flush=True)


def set_rc_path():
    from io_bcry_exporter.configuration import Configuration
    if Configuration.rc_path != RC:
        Configuration.rc_path = RC
        Configuration.save()
    log("rc_path", Configuration.rc_path)


MUZZLE = tuple(placement() @ Vector(MUZZLE_SRC))  # crossbow: smoke offset in crossbow.animevents; handgonne: on hand_cannon_barrel


def import_sources():
    os.makedirs(IMPORT_DIR, exist_ok=True)
    for f in (SKELETON_SKIN, SKELETON_MTL):
        shutil.copy2(os.path.join(REF, f), IMPORT_DIR)
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.import_scene.kcd2_skin(filepath=os.path.join(IMPORT_DIR, SKELETON_SKIN))
    skeleton_objs = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=SRC)
    rifle_objs = set(bpy.data.objects) - skeleton_objs

    armature = next(o for o in skeleton_objs if o.type == "ARMATURE")
    parts = [o for o in rifle_objs if o.type == "MESH" and o.data.materials and o.data.materials[0].name == KEEP_MATERIAL]

    # Bake each part's world matrix (glTF parent empties) plus our fix into its mesh data.
    fix = placement() @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Scale(0.01, 4)
    for p in parts:
        p.data = p.data.copy()  # glTF may share mesh data between objects
        p.data.transform(fix @ p.matrix_world)
        p.parent = None
        p.matrix_world = Matrix.Identity(4)

    for o in list(bpy.data.objects):
        if o not in parts and o is not armature:
            bpy.data.objects.remove(o, do_unlink=True)
    # Drop the importers' own collections: BCry would treat them as extra export nodes.
    for o in parts + [armature]:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        bpy.context.scene.collection.objects.link(o)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)

    with bpy.context.temp_override(active_object=parts[0], selected_editable_objects=parts, object=parts[0]):
        bpy.ops.object.join()
    gun = parts[0]
    log("armature", armature.name, "bones", len(armature.data.bones), "| gun parts joined, verts", len(gun.data.vertices))
    return armature, gun


def prepare_gun(armature, gun):
    me = gun.data
    while len(me.materials) > 1:
        me.materials.pop(index=len(me.materials) - 1)
    me.materials[0].name = NAME + "__01__gun__physNone"
    while len(me.uv_layers) > 1:
        me.uv_layers.remove(me.uv_layers[-1])

    bm = bmesh.new()
    bm.from_mesh(me)
    for f in bm.faces:
        f.material_index = 0
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()

    gun.vertex_groups.clear()
    vg = gun.vertex_groups.new(name=ROOT_BONE)
    vg.add(range(len(me.vertices)), 1.0, "REPLACE")

    gun.parent = armature
    gun.matrix_parent_inverse = armature.matrix_world.inverted()
    mod = gun.modifiers.new("Armature", "ARMATURE")
    mod.object = armature
    gun.name = NAME
    me.name = NAME

    xs = [v.co for v in me.vertices]
    lo = [min(c[i] for c in xs) for i in range(3)]
    hi = [max(c[i] for c in xs) for i in range(3)]
    log("bbox min", [round(v, 3) for v in lo], "max", [round(v, 3) for v in hi], "materials", [m.name for m in me.materials],
        "uv", [u.name for u in me.uv_layers], "muzzle", [round(v, 3) for v in MUZZLE])


def export(gun):
    for o in bpy.context.scene.objects:
        o.select_set(o == gun)
    bpy.context.view_layer.objects.active = gun
    bpy.ops.bcry.add_cry_export_node(node_type="skin", node_name=NAME)
    log("export nodes", [c.name for c in bpy.data.collections])

    os.makedirs(WORK, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, NAME + ".blend"))
    os.makedirs(OUT_DIR, exist_ok=True)
    skin = os.path.join(OUT_DIR, NAME + ".skin")
    if os.path.exists(skin):
        os.remove(skin)
    # The gun's .mtl is hand-written (textures, Illum params); BCry may write its own <node>.mtl, so keep ours.
    mtl = os.path.join(OUT_DIR, NAME + ".mtl")
    kept_mtl = open(mtl, "rb").read() if os.path.isfile(mtl) else None
    bpy.ops.bcry.export_to_game(filepath=os.path.join(OUT_DIR, NAME + ".dae"))
    # BCry runs rc.exe in the background; keep Blender alive until the .skin appears.
    for _ in range(180):
        if os.path.isfile(skin) and os.path.getsize(skin) > 0:
            time.sleep(2)
            break
        time.sleep(1)
    if kept_mtl is not None:
        with open(mtl, "wb") as f:
            f.write(kept_mtl)
    log("out dir", sorted(os.listdir(OUT_DIR)))


set_rc_path()
arm, g = import_sources()
prepare_gun(arm, g)
export(g)
skin = os.path.join(OUT_DIR, NAME + ".skin")
log("RESULT", "OK" if os.path.isfile(skin) else "NO SKIN", skin)
sys.exit(0 if os.path.isfile(skin) else 1)
