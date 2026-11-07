"""Copy the vanilla game files the other tools read into work/ (git-ignored: they belong to Warhorse).

Usage: py -I tools/extract_refs.py

Writes:
  work/extracted/Libs/Tables/...   every table from Data/Tables.pak (tools/build.py checks item ids against them)
  work/blender_ref/                the crossbow skeleton/skin and handgonne files tools/blender_make_skin.py imports
The recipe book images (work/ref_images/*.png) are not extracted here; see docs/BUILDING.md.
"""
import glob
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kcd2paths import GAME_DIR  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(GAME_DIR, "Data")
BLENDER_REF = {
    "objects/manmade/weapons/crossbows/crossbow.chr",
    "objects/manmade/weapons/crossbows/crossbow_medium_b.skin",
    "objects/manmade/weapons/crossbows/crossbow_medium_b_m01.mtl",
    "objects/manmade/weapons/firearms/hand_cannon.chr",
    "objects/manmade/weapons/firearms/hand_cannon_a.skin",
    "objects/manmade/weapons/firearms/hand_cannon_a.cgf",
    "objects/manmade/weapons/firearms/hand_cannon_a.cgfm",
    "objects/manmade/weapons/firearms/hand_cannon_a.mtl",
}


def extract_tables():
    out = os.path.join(ROOT, "work", "extracted")
    with zipfile.ZipFile(os.path.join(DATA, "Tables.pak")) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            dst = os.path.join(out, *info.filename.replace("\\", "/").split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(z.read(info))
    print("tables ->", out)


def extract_blender_ref():
    out = os.path.join(ROOT, "work", "blender_ref")
    os.makedirs(out, exist_ok=True)
    left = set(BLENDER_REF)
    for pak in sorted(glob.glob(os.path.join(DATA, "*Objects*.pak"))):
        with zipfile.ZipFile(pak) as z:
            for info in z.infolist():
                name = info.filename.replace("\\", "/").lower()
                if name in left:
                    with open(os.path.join(out, os.path.basename(name)), "wb") as f:
                        f.write(z.read(info))
                    left.discard(name)
        if not left:
            break
    print("blender refs ->", out, "| missing:", sorted(left) or "none")


if __name__ == "__main__":
    extract_tables()
    extract_blender_ref()
