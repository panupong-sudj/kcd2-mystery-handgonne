---
name: kcd2-blender
description: Drive Blender through the Blender MCP server (tools such as execute_blender_code, look, get_scene_info) to import KCD2 models with the KCD2 Blender Toolkit and export .skin/.cgf with BCry Exporter for the mystery_handgonne mod. Use when working on a weapon model in Blender, e.g. turning the gun mesh into a .skin bound to crossbow.chr.
---

# KCD2 models in Blender via MCP

Blender MCP ("MCP for Blender", PyPI `mcp-for-blender`, formerly `blender-mcp`, repo ahujasid/blender-mcp) connects Claude to a running Blender through an addon socket on `localhost:9876`. Everything is done by running bpy in the live Blender. The KCD2 Blender Toolkit (LuneMods/KCD2-Blender-Toolkit) supplies the importers and the KCD2 build of BCry Exporter.

## Before starting

1. Check that the MCP is connected: call `get_addon_status`. If the tool is missing, the server isn't registered in this session. Setup is below.
2. If it says it can't connect, Blender isn't open, or the server isn't running in Blender. Ask the user to press `N` in the 3D Viewport, open the **MCP for Blender** tab and click **Start MCP Server** (or **Connect to Claude**).
3. Check that both addons are present before importing anything:
   ```python
   import bpy, addon_utils
   print(bpy.app.version_string)
   print([m.__name__ for m in addon_utils.modules() if 'kcd2' in m.__name__.lower() or 'bcry' in m.__name__.lower()])
   print(hasattr(bpy.ops.import_scene, 'kcd2_skin'), hasattr(bpy.ops.bcry, 'export_to_game_quick'))
   ```
   The toolkit targets Blender **4.3**. Other versions may not work (Blender 5.x dropped COLLADA, which both the toolkit's import and export use).

### Installed on this machine (2026-11-07)

- Blender **4.3.2 portable**: `D:\Tools\blender-4.3.2-windows-x64\blender.exe`. Use this one. Blender 5.2 in `C:\Program Files\Blender Foundation` doesn't work with the toolkit.
- `io_KCD2_Blender_Toolkit` + `io_bcry_exporter` in `%APPDATA%\Blender Foundation\Blender\4.3\scripts\addons`, both enabled (saved in userpref). The importers have been tested and work.
- The MCP addon must be installed into **4.3** too. If `uvx mcp-for-blender setup` only installs it into 5.2, copy `blender_mcp.py` into the folder above and enable it.
- `rc.exe` comes from KCD2 Modding Tools (Steam): `<Steam>\steamapps\common\KCD2Mod\Tools\rc\rc.exe`. It's already set in BCry (`%APPDATA%\Blender Foundation\Blender\4.3\config\bcry.cfg`).
- The whole workflow is scripted in `tools/blender_make_skin.py` (`blender.exe -b --python tools/blender_make_skin.py`), which handles all the gotchas below. Use it as the reference when doing it through MCP.
- Gotchas found by actually running it: (1) after importing, delete the importers' collections (`crossbow_medium_b.skin`, `shadowproxy_*.cgf`), or BCry exports them as extra nodes; (2) BCry runs rc.exe in the background, so in `-b` mode you have to wait for the `.skin` to appear before Blender exits; (3) the mesh imported from `.cgf` sits ~6.7 cm further along the barrel than the bbox in the cgf mesh chunk.
- Smoke test without the GUI: `blender.exe -b --python <script.py>`.

### MCP setup (one time, done by the user)

- Fastest: `uvx mcp-for-blender setup` (needs uv: `winget install --id=astral-sh.uv -e`). It picks up Claude Code / Claude Desktop, installs the addon and enables it.
- Manual: `claude mcp add blender uvx mcp-for-blender`, then `uvx mcp-for-blender install-addon`, then enable **Interface: MCP for Blender** under Edit → Preferences → Add-ons.
- After that, fully restart the Claude app (on Windows, quit it from the system tray too) so the tools load. Run only one MCP server for Blender at a time.
- If the app can't find `uvx` (`spawn uvx ENOENT`), use the full path to `uvx.exe` or `cmd /c uvx mcp-for-blender`.

## Tools

| Tool | Use |
| --- | --- |
| `execute_blender_code` | Runs Python in Blender. This is the main tool. Read results through `print()`. |
| `get_scene_info` | Summarises the objects in the scene. Use it to check names, parents, modifiers, vertex groups and materials. |
| `look` | Takes a picture from the viewport, camera or several angles, in solid/wireframe/xray. Use it to check the barrel points along +Y and the mesh sits where the hand holds the crossbow. |
| `get_addon_status` | Shows the Blender and addon versions. |

`search_assets`, `import_asset` and `generate_3d` (Poly Haven, Sketchfab and other generators) aren't used in this project.

## Rules

- **Save first:** `bpy.ops.wm.save_mainfile()` before any big change. `execute_blender_code` runs whatever it is given, and undo may not cover it.
- **Work in small pieces:** run one step per call and verify it with `get_scene_info` or `look` before the next.
- **Never assume an object name:** names come out of import with suffixes such as `.001`. Find them from `bpy.data.objects` every time.
- **Mode:** most `bpy.ops` calls need Object Mode and a correct selection/active object. Prefer writing data directly (`obj.vertex_groups`, `obj.modifiers`, `obj.parent`) over `bpy.ops` where possible.
- **Don't touch user settings:** don't change preferences or addons the user didn't ask for. Telemetry is off by default; if asked, use `disable_telemetry`.

## Project facts (measured with tools/meshbox.py and tools/bones.py)

- Front of the crossbow is **+Y** (the bow is at y ≈ +0.2..+0.46). It's long along Y and flat along Z.
- `crossbow.chr`: bone `Asset_Crossbow` is the root, at the origin with no rotation. `Crossbow_arrow` is at (0, 0.138, 0.060), where the bolt/ball sits.
- `hand_cannon_a.cgf` is long along **Z** (−0.43..+0.56), with the metal barrel at +Z. To lie along the crossbow, rotate **X −90°** (+Z → +Y).
- `.skin` / `.cgf` hold only 1 mesh and 1 material shown in game. Triangulate before export.
- Weapon CA_BONE attachments are hidden by the game until the weapon is loaded, so the gun body must be a **CA_SKIN**.
- The crossbow stock the hands grip spans y −0.35..+0.13, z −0.014..+0.057, so model the gun's grip/stock in that range (the placeholder handgonne is raised 3 cm).
- Don't put anything solid around `Crossbow_arrow` (0, 0.138, 0.06): it's on the sight line. The loaded round is made invisible with `mystery_handgonne_round.cgf` (Nodraw) instead.
- Everything learned about the gun mod as a whole (cdf, ammo, animevents with a `model` filter) is in the **kcd2-gun-mod** skill.

Reference files are already extracted to `<repo>\work\blender_ref\` (`crossbow_medium_b.skin`, `hand_cannon_a.cgf` + `.cgfm`, `.mtl`, `crossbow.chr`).
The step-by-step guide for doing it by hand is in `docs/BLENDER_GUIDE.md`.

## Workflow: make the gun into a .skin bound to Asset_Crossbow

Run one step per `execute_blender_code` call. Paths use `r"..."`.

1. **New scene + save .blend** (BCry exports next to the .blend file)
   ```python
   import bpy
   bpy.ops.wm.read_homefile(use_empty=True)
   bpy.ops.wm.save_as_mainfile(filepath=r"<repo>\work\blender\mystery_handgonne.blend")
   ```
2. **Import the crossbow armature + the handgonne**
   ```python
   import bpy
   ref = r"<repo>\work\blender_ref"
   bpy.ops.import_scene.kcd2_skin(filepath=ref + r"\crossbow_medium_b.skin")
   bpy.ops.import_scene.kcd2_cgf(filepath=ref + r"\hand_cannon_a.cgf")
   for o in bpy.data.objects: print(o.name, o.type, o.parent.name if o.parent else None, [v.name for v in getattr(o, 'vertex_groups', [])][:5])
   ```
   Then check with `get_scene_info`: the armature has `Asset_Crossbow`, and see how many meshes the handgonne has (keep only LOD0, the one with the most vertices).
3. **Clean up:** delete the crossbow mesh (keep the armature), the handgonne LOD1+, and any Empty slots/proxies that came with it.
4. **Rotate and apply:** the handgonne mesh `rotation_euler.x -= radians(90)`, then apply transforms (select only that object, `bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)`).
   - Check with `look` (angles, xray): the barrel points to +Y and the wooden stock goes back toward −Y.
5. **Single mesh, single material, triangulate:** join the parts (`bpy.ops.object.join()`). Leave 1 material slot. Triangulate through bmesh (`bmesh.ops.triangulate`).
6. **Weight to the bone:** delete the old vertex groups, create `Asset_Crossbow`, `vg.add(range(len(me.vertices)), 1.0, 'REPLACE')`. Set `obj.parent = armature` (keep the world matrix) and add an Armature modifier (`object = armature`).
7. **Rename + export node:** `obj.name = "mystery_handgonne"`. Select only this mesh, then `bpy.ops.bcry.add_cry_export_node(node_type='skin', node_name='mystery_handgonne')`. Check that the collection `cry_export_nodes/mystery_handgonne.skin` exists and contains the mesh.
8. **rc.exe:** BCry needs the path to `rc.exe`. If it isn't set yet, ask the user to click **Find The Resource Compiler** in the BCry Exporter tab. Don't guess the path.
9. **Save + export straight into the mod:** `bpy.ops.wm.save_mainfile()` then
   ```python
   bpy.ops.bcry.export_to_game(filepath=r"<repo>\mod\mystery_handgonne\Data\Objects\weapons\mystery_handgonne\mystery_handgonne.dae")
   ```
   BCry puts its output in the folder of `filepath` (the `.dae` is an intermediate file; RC turns it into `mystery_handgonne.skin` next to it). Don't use `export_to_game_quick`, which writes next to the .blend. `tools/build.py` skips `.dae/.rcdone/.blend/.log` so they don't end up in the pak. If it fails, read the error in the System Console or in the `print` output.
10. **Hand off to the mod (done by me outside Blender):** write a `.cdf` with `crossbow.chr` + `CA_SKIN` + material `objects/manmade/weapons/firearms/hand_cannon_a.mtl` + attachment `Arrow` at `Position="0,0.45,0"`, then `py -I tools/build.py` and install (the game must be closed).

## Operator names (from the toolkit source)

- Import: `bpy.ops.import_scene.kcd2_skin`, `bpy.ops.import_scene.kcd2_cgf`, `bpy.ops.import_scene.kcd2_collada`
- BCry: `bpy.ops.bcry.add_cry_export_node(node_type=..., node_name=...)` (types: cgf, cga, chr, skin), `bpy.ops.bcry.export_to_game` (opens a dialog), `bpy.ops.bcry.export_to_game_quick` (exports to the .blend's folder), `bpy.ops.bcry.find_rc`
- An export node is a collection named `<name>.<type>` under the `cry_export_nodes` collection. A mesh whose parent is an armature gets type `skin` automatically.
