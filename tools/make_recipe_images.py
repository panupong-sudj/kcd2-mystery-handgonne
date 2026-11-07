"""Make the alchemy book images for the cartridge recipe (RecipeId 7101) from the vanilla lead shot ones.

Usage: <Blender 4.3>/blender.exe -b --python tools/make_recipe_images.py

The recipe page shows Libs/UI/Textures/Books/Recipes/<RecipeId>_ui.dds (1024x1024 illustration) and
Products/<RecipeId>_ui.dds (256x256 product). Our recipe is lead shot gunpowder boiled in oil, so starting from
vanilla recipe 54 (water base) we:
  - copy the oil symbol (upright triangle) in the top-left corner from vanilla recipe 25 (an oil-base recipe)
  - flip the water symbol on the cauldron upside down (water = downward triangle, oil = upward triangle)
  - recolour the blue water in the cauldron and the pouring pot to oil yellow, like recipe 25's oil
  - darken the product pouch so it reads as a different powder
Sources are PNG copies of the vanilla .dds in work/ref_images. Writes .tif and compiles them with rc (preset Ui).
"""
import os
import sys
import subprocess

import bpy
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "work", "ref_images")
OUT = os.path.join(ROOT, "mod", "mystery_handgonne", "Data", "Libs", "UI", "Textures", "Books")
RECIPE_ID = 7101
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kcd2paths import RC  # noqa: E402


def log(*a):
    print("[make_recipe_images]", *a, flush=True)


def load(name):
    img = bpy.data.images.load(os.path.join(REF, name))
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    # Blender stores rows bottom-up; flip so [y, x] matches image coordinates (y down) used below.
    return px.reshape(h, w, 4)[::-1].copy()


def save(arr, path, preview):
    h, w = arr.shape[:2]
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=True)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(np.clip(arr[::-1], 0, 1).astype(np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "TIFF"
    img.save()
    img.filepath_raw = preview  # PNG copy to look at outside the game
    img.file_format = "PNG"
    img.save()
    r = subprocess.run([RC, path, "/preset=Ui", "/mipmaps=0", "/refresh"], capture_output=True, text=True)
    log("wrote", path, "rc exit", r.returncode)


def recolour_water(img, x0, y0, x1, y1):
    """Blue water pixels in the box -> oil yellow, keeping their brightness (wave lines stay lighter)."""
    box = img[y0:y1, x0:x1]
    r, g, b = box[..., 0], box[..., 1], box[..., 2]
    water = (b > r + 0.08) & (b > g - 0.02)
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    oil = np.stack([lum * 1.25, lum * 1.0, lum * 0.35], axis=-1)
    box[..., :3] = np.where(water[..., None], oil, box[..., :3])
    return int(water.sum())


recipe = load("recipe54_waterbase.png")
oil_ref = load("recipe25_oilbase.png")

# 1. corner symbol: oil triangle from recipe 25 (same layout, same background)
recipe[20:165, 20:235] = oil_ref[20:165, 20:235]
# 2. symbol on the cauldron: erase the water triangle's dark ink (paint it cauldron grey), then copy only the
#    dark ink of recipe 25's oil triangle (its cauldron sits 58 px higher on the page). Flipping the whole box
#    left a visible seam through the flames.
#    The ink is the same dark brown as the page and the flame outlines, so only pixels near the triangle's
#    edges count (corners measured from 4x crops of both images).
def near_edges(shape, corners, width=5.0):
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float32)
    d = np.full(shape, 1e9, np.float32)
    for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
        vx, vy = bx - ax, by - ay
        t = np.clip(((xx - ax) * vx + (yy - ay) * vy) / (vx * vx + vy * vy), 0, 1)
        d = np.minimum(d, np.hypot(xx - (ax + t * vx), yy - (ay + t * vy)))
    return d < width


def dark(a):
    return a[..., :3].mean(axis=-1) < 0.42


WATER_TRI = [(478, 546), (586, 546), (531, 610)]  # recipe 54, on the cauldron
OIL_TRI = [(470, 555), (565, 555), (516, 494)]  # recipe 25, on its cauldron
dx = round(sum(p[0] for p in WATER_TRI) / 3 - sum(p[0] for p in OIL_TRI) / 3)
dy = round(sum(p[1] for p in WATER_TRI) / 3 - sum(p[1] for p in OIL_TRI) / 3)

erase = near_edges(recipe.shape[:2], WATER_TRI) & dark(recipe)
body = recipe[440:620, 470:590]
body = body[(body[..., :3].mean(axis=-1) > 0.42) & (np.ptp(body[..., :3], axis=-1) < 0.08)]
recipe[..., :3] = np.where(erase[..., None], np.median(body[:, :3], axis=0), recipe[..., :3])

copy = near_edges(oil_ref.shape[:2], OIL_TRI) & dark(oil_ref)
ys, xs = np.nonzero(copy)
recipe[ys + dy, xs + dx, :3] = oil_ref[ys, xs, :3]
log("cauldron symbol: erased", int(erase.sum()), "px, drew", len(ys), "px, offset", dx, dy)
# 3. water -> oil in the big cauldron and in the pouring pot (incl. the drip)
n = recolour_water(recipe, 430, 440, 620, 515) + recolour_water(recipe, 140, 520, 340, 610)
log("recoloured water pixels", n)
os.makedirs(os.path.join(OUT, "Recipes"), exist_ok=True)
PREVIEW = os.path.join(ROOT, "work", "blender")
save(recipe, os.path.join(OUT, "Recipes", f"{RECIPE_ID}_ui.tif"), os.path.join(PREVIEW, f"recipe{RECIPE_ID}_preview.png"))

product = load("product54.png")
rgb = product[..., :3]
pouch = (rgb[..., 0] > rgb[..., 2] + 0.08)  # the brown/orange pouch, not the white frame or the cork outline
lum = rgb.mean(axis=-1)
dark = np.stack([lum * 0.45, lum * 0.42, lum * 0.38], axis=-1)
product[..., :3] = np.where(pouch[..., None], dark, rgb)
os.makedirs(os.path.join(OUT, "Products"), exist_ok=True)
save(product, os.path.join(OUT, "Products", f"{RECIPE_ID}_ui.tif"), os.path.join(PREVIEW, f"product{RECIPE_ID}_preview.png"))
log("done")
