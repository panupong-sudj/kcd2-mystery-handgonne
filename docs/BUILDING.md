# Building from source

Everything runs on Windows with KCD2 and the free **KCD2 Modding Tools** installed from Steam.

## What you need

| Tool | Used for | Notes |
| --- | --- | --- |
| Kingdom Come: Deliverance II | Vanilla references, testing | |
| KCD2 Modding Tools (Steam) | `Tools/rc/rc.exe` compiles textures and models; `Tools/SteamWorkshopUploader` | |
| Python 3 (`py` launcher) | `tools/build.py`, `tools/extract_refs.py`, `tools/bones.py`, `tools/meshbox.py` | Standard library only |
| Blender **4.3** (portable is fine) | Model, textures, icon, recipe images | Blender 5.x dropped COLLADA, which the toolkit needs |
| [KCD2 Blender Toolkit](https://github.com/LuneMods/KCD2-Blender-Toolkit) | Two addons: `io_KCD2_Blender_Toolkit` (import) and `io_bcry_exporter` (export) | Copy both to `%APPDATA%\Blender Foundation\Blender\4.3\scripts\addons` and enable them |

The tools find the game and the Modding Tools in the usual Steam library folders (`tools/kcd2paths.py`). To point them elsewhere, set `KCD2_GAME_DIR` and `KCD2_MODDING_TOOLS_DIR`.

## 1. Extract the vanilla references (once)

```bash
py -I tools/extract_refs.py
```

This fills `work/extracted/` (all tables, used to check item ids) and `work/blender_ref/` (crossbow skeleton and skin, handgonne files). `work/` is git-ignored because these files belong to the game.

## 2. Pack the mod

```bash
py -I tools/build.py
```

This writes `publish/mystery_handgonne/`, which holds:

- `mod.manifest`;
- `Data/mystery_handgonne.pak`;
- `Localization/English_xml.pak`.

It also checks that:

- every XML file parses;
- no new item id collides with a vanilla one;
- every model path resolves to the mod or a game pak.

Source files (`.tif`, `.blend`, `.dae`) are left out of the paks.

## 3. Install and test

1. **Close the game.**
2. Copy `publish/mystery_handgonne` to `<KCD2>/Mods/mystery_handgonne`.
3. If `<KCD2>/Mods/mod_order.txt` exists, add `mystery_handgonne` to it.
4. Start the game. In `kcd.log` (game folder), look for:
   - `[Mod]` lines;
   - `Table 'item' is patched by 'item__mystery_handgonne'`;
   - the mod's own lines starting with `[mystery_handgonne]`.
5. Start with `-devmode` to use the console commands (see the README).

## Rebuilding the assets

Only needed if you change the model or images. The compiled results are already in `mod/`.

Each of these is a separate command. Run them from the repository root, replacing `<Blender 4.3>` with your Blender folder:

1. The gun body (`mod/.../mystery_handgonne.skin`):

   ```bash
   "<Blender 4.3>/blender.exe" -b --python tools/blender_make_skin.py
   ```

2. Textures (`_diff`/`_spec`/`_ddna` `.tif` + `.dds`):

   ```bash
   "<Blender 4.3>/blender.exe" -b --python tools/make_textures.py
   ```

3. The invisible round (`mystery_handgonne_round.cgf` + Nodraw `.mtl`):

   ```bash
   "<Blender 4.3>/blender.exe" -b --python tools/blender_make_round.py
   ```

4. The 64×64 inventory icon:

   ```bash
   "<Blender 4.3>/blender.exe" -b --python tools/make_icon.py
   ```

5. The alchemy book images for recipe 7101:

   ```bash
   "<Blender 4.3>/blender.exe" -b --python tools/make_recipe_images.py
   ```

`blender_make_skin.py` keeps the hand-written `mystery_handgonne.mtl` (textures and shader settings) even if BCry writes its own material during export.

**Recipe images need PNG copies of three vanilla textures** in `work/ref_images/`. Export them from `Data/IPL_GameData.pak` with any DDS-capable image editor:

| Vanilla file in `IPL_GameData.pak` | Save as |
| --- | --- |
| `Libs/UI/Textures/Books/Recipes/54_ui.dds` | `recipe54_waterbase.png` |
| `Libs/UI/Textures/Books/Recipes/25_ui.dds` | `recipe25_oilbase.png` |
| `Libs/UI/Textures/Books/Products/54_ui.dds` | `product54.png` |

### Measuring instead of guessing

- `py -I tools/bones.py work/blender_ref/crossbow.chr` prints every bone's bind position and axes.
- `py -I tools/meshbox.py objects/manmade/weapons/crossbows/crossbow_medium_b.skin` prints mesh bounding boxes straight from the game paks.

Measured crossbow skeleton facts:

- `Asset_Crossbow` is the root, at the origin with no rotation. Forward is **+Y** and up is **+Z**.
- `Crossbow_arrow` is at (0, 0.138, 0.06). The game snaps the loaded round there, on the sight line.
- `Crossbow_trigger_end` is at (0, −0.152, −0.009).
- The hand animations grip the stock at y −0.35..+0.13, z −0.014..+0.057.

## Doing the model by hand in Blender

`tools/blender_make_skin.py` does all of this headless. To do it in the GUI instead (for example with a different gun mesh):

1. **Start clean:** open a new scene and delete the cube, camera and light.
2. **Import the crossbow:** use the toolkit's "Import KCD2 Skin" on `work/blender_ref/crossbow_medium_b.skin`. You get the crossbow armature, whose root bone is `Asset_Crossbow`, and its mesh.
3. **Import your gun.** Then:
   - keep one LOD;
   - delete proxy and slot empties;
   - rotate it so the muzzle points **+Y**, the same way as the crossbow's bow;
   - place the stock where the crossbow stock is;
   - **Ctrl+A → All Transforms**.
4. **Delete the crossbow mesh.** Keep the armature.
5. **Make it one mesh with one material:** `.skin` holds one mesh and one visible material. Join with **Ctrl+J**, then triangulate in Edit Mode (select all, **Ctrl+T**).
6. **Weight it to `Asset_Crossbow`:**
   - In Edit Mode, select all vertices.
   - Add a vertex group named exactly **`Asset_Crossbow`**, weight 1.0, **Assign**. Delete any other vertex groups.
   - In Object Mode, select the mesh, then shift-select the armature: **Ctrl+P → Armature Deform** (no automatic weights).
7. **Add the export node:**
   - Name the object, for example `my_gun`.
   - BCry Exporter tab → **Add Export Node** with the same name. Because the parent is an armature, it becomes `my_gun.skin` under `cry_export_nodes`.
   - Delete the importers' own collections, or BCry exports them too.
8. **Export:**
   - BCry Exporter → **Find The Resource Compiler** → choose `rc.exe` (first time only).
   - Use **Export to CryEngine** and point the file path at `mod/<modid>/Data/Objects/<path>/my_gun.dae`.
   - The `.dae` is intermediate: rc.exe turns it into `my_gun.skin` next to it. Use the full export, not `export_to_game_quick`.

Notes from the toolkit docs:

- Sharp-edge data is lost on export. Add supporting edges if shading breaks.
- BCry names materials `<node>__<index>__<name>__<physics>`.
- A `.cgf` looks up `<node>.mtl` next to itself.
