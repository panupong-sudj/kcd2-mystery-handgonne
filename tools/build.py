"""Pack mod/<modid>/ into an installable folder under publish/<modid>/ (not in git) and sanity-check it.

Usage: py -I tools/build.py [modid] [game_dir]

Checks (all read-only against the game):
  - every .xml/.cdf in the mod parses
  - new item Ids do not collide with any vanilla item Id
  - every Model/HolsterModel/Binding path resolves to a file in the mod or in a game pak
"""
import glob
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kcd2paths  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODID = sys.argv[1] if len(sys.argv) > 1 else "mystery_handgonne"
GAME = sys.argv[2] if len(sys.argv) > 2 else kcd2paths.GAME_DIR
SRC = os.path.join(ROOT, "mod", MODID)
OUT = os.path.join(ROOT, "publish", MODID)
VANILLA_ITEMS = os.path.join(ROOT, "work", "extracted", "Libs", "Tables", "item")

errors = []

# Blender/BCry export the .skin straight into the mod folder and leave their working files next to it.
SKIP_EXT = (".blend", ".blend1", ".dae", ".rcdone", ".log", ".glb", ".bak", ".tif", ".tiff")


def files_under(base):
    for path in glob.glob(os.path.join(base, "**", "*"), recursive=True):
        if os.path.isfile(path) and not path.lower().endswith(SKIP_EXT):
            yield path, os.path.relpath(path, base).replace("\\", "/")


def write_pak(src_dir, pak_path):
    os.makedirs(os.path.dirname(pak_path), exist_ok=True)
    # Stored (no compression), same as the working glock mod.
    with zipfile.ZipFile(pak_path, "w", zipfile.ZIP_STORED) as z:
        for path, rel in sorted(files_under(src_dir), key=lambda t: t[1]):
            z.write(path, rel)
    return pak_path


def check_xml():
    for path, rel in files_under(SRC):
        if rel.endswith((".xml", ".cdf", ".manifest")):
            try:
                ET.parse(path)
            except ET.ParseError as e:
                errors.append(f"XML parse error in {rel}: {e}")


def check_ids():
    vanilla = set()
    for f in glob.glob(os.path.join(VANILLA_ITEMS, "item*.xml")):
        vanilla.update(re.findall(r'\bId="([0-9a-fA-F-]{36})"', open(f, encoding="utf-8", errors="ignore").read()))
    seen = set()
    for path, rel in files_under(os.path.join(SRC, "Data", "Libs", "Tables")):
        for el in ET.parse(path).iter():
            i = el.get("Id")
            if not i:
                continue
            if i.lower() in {v.lower() for v in vanilla}:
                errors.append(f"{rel}: Id {i} ({el.get('Name')}) collides with a vanilla item")
            if i in seen:
                errors.append(f"{rel}: Id {i} used twice")
            seen.add(i)
    return seen


def game_object_paths():
    names = set()
    for p in glob.glob(os.path.join(GAME, "Data", "*.pak")):
        # Models live under Objects/ in both the Objects and the Characters paks (e.g. recipe books).
        if "Objects" not in os.path.basename(p) and "Characters" not in os.path.basename(p):
            continue
        names.update(n.lower() for n in zipfile.ZipFile(p).namelist())
    return names


def check_paths():
    known = game_object_paths()
    known.update(rel.lower() for _, rel in files_under(os.path.join(SRC, "Data")))

    def exists(p):
        p = p.replace("\\", "/").lower()
        if not p.startswith("objects/"):
            p = "objects/" + p
        return p in known

    for path, rel in files_under(os.path.join(SRC, "Data")):
        if rel.startswith("Libs/Tables/item/"):
            for el in ET.parse(path).iter():
                for attr in ("Model", "HolsterModel", "ShortModel", "LongModel", "InquiverModel"):
                    v = el.get(attr)
                    if v and not exists(v):
                        errors.append(f"{rel}: {el.get('Name')}.{attr} -> {v} not found")
        elif rel.endswith(".cdf"):
            for el in ET.parse(path).iter():
                for attr in ("File", "Binding", "GeometryFilepath"):
                    v = el.get(attr)
                    if v and not exists(v):
                        errors.append(f"{rel}: {attr} -> {v} not found")


def main():
    check_xml()
    if errors:
        return finish()
    ids = check_ids()
    check_paths()
    if errors:
        return finish()

    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    shutil.copy2(os.path.join(SRC, "mod.manifest"), OUT)
    write_pak(os.path.join(SRC, "Data"), os.path.join(OUT, "Data", f"{MODID}.pak"))
    loc_root = os.path.join(SRC, "Localization")
    for lang_dir in sorted(glob.glob(os.path.join(loc_root, "*_xml"))):
        write_pak(lang_dir, os.path.join(OUT, "Localization", os.path.basename(lang_dir) + ".pak"))

    print(f"built {OUT}")
    for path, rel in files_under(OUT):
        print(f"  {rel}  ({os.path.getsize(path)} bytes)")
        if rel.endswith(".pak"):
            for n in zipfile.ZipFile(path).namelist():
                print(f"      {n}")
    print("item ids:", ", ".join(sorted(ids)))
    return finish()


def finish():
    for e in errors:
        print("ERROR:", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
