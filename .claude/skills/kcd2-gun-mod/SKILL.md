---
name: kcd2-gun-mod
description: Recipe for building a firearm (e.g. a sniper rifle) in Kingdom Come Deliverance II on top of a crossbow. It aims and reloads like a crossbow, but has its own model, fires a bullet, and plays a gunshot sound and muzzle smoke only for that gun. Every step here has been tested in game. Use when making or changing a gun mod for KCD2, or a weapon that needs a new model on a crossbow skeleton.
---

# KCD2 gun mod on a crossbow base

All of this was tested in game on KCD2 1.5.x while building the **Mystery Handgonne** mod (modid `mystery_handgonne`, November 2026); the full source is in this repository. Each point records **what was tried and what happened**, because many approaches look like they should work and don't.

## Overall shape

| Part | Approach that works | File |
| --- | --- | --- |
| Item | PTF `item__<modid>.xml`: copy a vanilla crossbow row (e.g. `crossbowMediumNormal01`, Class 14, goat's foot) and change `Id`, `Name`, `UIName`, `UIInfo`, `Model` | `Data/Libs/Tables/item/item__<modid>.xml` |
| Model | Your own `.cdf` = **vanilla** `crossbow.chr` + attachment `Arrow` (vanilla) + gun body as **`CA_SKIN`** | `Data/Objects/<path>/<gun>.cdf` |
| Gun body | `.skin` with **every** vertex weighted to bone `Asset_Crossbow` | `Data/Objects/<path>/<gun>.skin` |
| Bullet | New `Ammo` row with `Type="2"` (Bolt), and `Model/ShortModel/LongModel` pointing at your own `.cgf` whose material is Nodraw | `item__<modid>.xml` + `<round>.cgf` + `<round>.mtl` |
| Sound + smoke | Override `crossbow.animevents`: keep the vanilla events, then add your events with `model="objects/<path>/<gun>.cdf"` | `Data/Animations/assets/crossbows/crossbow.animevents` |
| Name | `text_ui_items__<modid>.xml` packed as `Localization/English_xml.pak` | |

Example `.cdf`:

```xml
<CharacterDefinition>
  <Model File="objects/manmade/weapons/crossbows/crossbow.chr" Material="objects/characters/nodraw" />
  <AttachmentList>
    <Attachment Type="CA_BONE" AName="Arrow" Rotation="0.99999994,0,0,0" Position="0,0,0" BoneName="Crossbow_arrow" Flags="0" />
    <Attachment Type="CA_SKIN" AName="my_gun" Binding="objects/weapons/my_mod/my_gun.skin" Material="objects/weapons/my_mod/my_gun.mtl" Flags="0" />
  </AttachmentList>
</CharacterDefinition>
```

Example sound + smoke event (add one set to each of the 5 shot animations in the file, and **keep the vanilla `c_w_crossbow_shot` event**):

```xml
<event name="audio_trigger" time="0.0025" endTime="0.0025" parameter="c_f_firearm_shot" bone="Crossbow_trigger_end" offset="0,0,0" dir="0,0,0" model="objects/weapons/my_mod/my_gun.cdf" />
<event name="effect" time="0.0025" endTime="0.34" parameter="firearms.hand_cannon.frontParticleEmit" bone="Asset_Crossbow" offset="0,<muzzle y>,<muzzle z>" dir="0,0,0" model="objects/weapons/my_mod/my_gun.cdf" />
```

The 5 shot animations are `crossbow_shot.caf`, `crossbow_palisade_lean_shoot.caf`, `crossbow_horse_shot_over.caf`, `crossbow_stealth_shot.caf` and `crossbow_shot_over.caf`. Copy each `time` from the vanilla file.

## Rules and what was tested

### Model
- ❌ **`CA_BONE` + `.cgf` (static mesh hung on a bone):** the game hides the weapon's CA_BONE attachments until the first load, so the gun vanishes every time it's drawn. Moving it to a different bone doesn't help either.
- ✅ **`CA_SKIN`:** shows the moment the gun is drawn, the same way vanilla crossbows do.
- ❌ **A skeleton from another weapon (e.g. `hand_cannon.chr`):** it's missing the bones the crossbow system needs, so it doesn't fire and the model stands upright.
- ❌ **Copying `crossbow.chr` under a new name to get your own `.chrparams`/`.animevents`:** the engine never applies chrparams to a copied `.chr`, even one that points at the vanilla animevents. It gets no animations, so no events and no sound.
- ✅ Use vanilla `crossbow.chr` only. Set the cdf's Material to `objects/characters/nodraw` so the crossbow skeleton itself isn't drawn.

### Axes and positions in crossbow.chr (measured from the game files)
- `Asset_Crossbow` is the root bone, at the origin with no rotation. Forward is **+Y** (the bow sits at y +0.2..+0.46), up is +Z.
- The stock the hand animations grip spans **y −0.35..+0.13, z −0.014..+0.057** (trigger grip around y −0.15). Build the stock/grip of your gun to match this, or the hands float.
- `Crossbow_arrow` is at **(0, 0.138, 0.060)**, which is **where the game places the loaded round, right on the sight line**.
- `Crossbow_trigger_end` is at (0, −0.152, −0.009).
- A model imported from another weapon may lie on a different axis. Vanilla handgonne `hand_cannon_a` is long along Z, so it has to be rotated X −90° (+Z → +Y).

### Bullet
- A crossbow only loads ammo whose `Type` matches the class's `ammo_class` (class 10/14/15 = `2` Bolt; vanilla `shot_ball` is `3` and won't load). Give your new ammo `Type="2"`.
- The flying projectile and the loaded round both come from the ammo's `Model/ShortModel/LongModel`. Damage comes from `AttackSmash/Stab/Slash` (copying the lead ball's `AttackSmash=250` gives the same damage).
- ❌ Setting `Position/RelPosition` on attachment `Arrow` does nothing: the game always snaps the round onto bone `Crossbow_arrow`.
- ❌ `Material=` on the `Ammo` row (which works for black arrows) **isn't used on the loaded round**.
- ❌ A box covering the round blocks the sights, because the round sits on the sight line.
- ✅ Make your own `.cgf` for the round whose own `.mtl` uses `Shader="Nodraw"`. The round is then invisible both loaded and in flight, like a real bullet. (Dropped on the ground it's invisible too.)
- A weapon remembers what it has loaded (`keep_loaded`), so to switch ammo you must fire once first.

### Sound and smoke
- The crossbow shot sound comes from `crossbow.animevents` (an `audio_trigger` on the weapon skeleton). `Animations.img` holds no events. `AnimEvents.xml` is just a list for the audio team.
- ✅ An `.animevents` file in a mod pak **overrides** the vanilla one.
- ✅ The event's **`model` field limits it to characters loaded from that cdf**. It has to be the full path including `objects/` (e.g. `objects/weapons/my_mod/my_gun.cdf`). ❌ Without `objects/` it doesn't match.
- Gunshot sound: `c_f_firearm_shot`. Handgonne muzzle smoke: `firearms.hand_cannon.frontParticleEmit`, put on bone `Asset_Crossbow` with `offset` at your gun's muzzle (in model coordinates).
- Not yet tested: the crossbow's `c_w_crossbow_shot` probably still plays under the gunshot. To cut it out, give that event a `model` for each vanilla crossbow cdf instead of `model=""`.
- ⚠️ **Conflicts:** any other mod that overrides `crossbow.animevents` will clash. Their changes have to be merged into the same file.

### Reload speed, alchemy and text (tested)
- Reload speed of one gun only: weapon rows have no buff field and the reload speed belongs to the crossbow class, so add a buff (`buff_params="rls*4"`, `Cpp:Constant`, class 12) and bind it to the gun from Lua with `ItemManager.AddOnEquipBuff(item, buffId, true)` (find the gun with `player.inventory:FindItem(classId)`, script at `Scripts/mods/<modid>.lua`, start from `UIAction.RegisterEventSystemListener(obj, "System", "OnGameplayStarted", fn)`).
- ❌ **A new weapon class id (PTF `weapon_class__<modid>.xml`, e.g. id 40) is not accepted**: the item drops into Miscellaneous and cannot be equipped or loaded. The only missile classes are 9 bow (Arrow), 10/14/15 crossbows (Bolt) and 13 rifle (Ball + Shotgun, handgonne animations). So a crossbow-based gun **cannot get its own ammo type**: it will also take vanilla bolts. Moving the gun to class 13 (hand_cannon.chr, Ball ammo) does work technically and brings the native gun sound/smoke/perks, but it also brings the handgonne hold/aim/reload; for a rifle that should aim like a crossbow that was rejected in testing.
- To remove the goat's foot lever and roughly halve the reload: use `Class="10"` (light crossbow, cocked by hand). The lever is a class-wide `loading_item_first` of class 14.
- Flatter trajectory: raise `Power` (1200 worked well). Projectile speed follows Power, and so does damage.
- Alchemy recipe: PTF `Libs/Tables/minigame/AlchemyRecipe__<modid>.xml`, plus a `Document` row (`RecipeId`, `Type="2"`) to learn it from. **The recipe book images are tied to the RecipeId**: `Libs/UI/Textures/Books/Recipes/<RecipeId>_ui.dds` and `Libs/UI/Textures/Books/Products/<RecipeId>_ui.dds`. If they're missing the page shows an "img" placeholder.
- Forgeable at the smithy (pattern from the Toxic's More Sketches mod): PTF `minigame/BlacksmithRecipes__<modid>.xml` (`Category="Other"`, `WorkpieceId="axe"`, `MinSkillLevel`, `PerkId`), a hidden perk in `rpg/perk__<modid>.xml` + `rpg/perk_script__<modid>.xml`, and a sketch `Document` with `BlacksmithRecipeId`. One recipe can have **several `BlacksmithRecipeProduct`s with different `MinimalQuality`** (the forging score, as in vanilla `basic_sword`), so a higher score gives a stronger version of the gun. Reference Power values: light crossbow 165–230, medium 300–380, heavy 480–550, vanilla firearms 620–655.
- ❌ **Don't add `ui/ExtraRewards` rows without `DlcId`/`ProsId`**: the game froze while loading the save. Every vanilla row is gated by `DlcId` (from `dlc.xml`) or `ProsId`. Lua has no "add item to inventory by id", but `player.inventory:MoveItemOfClass(targetInventoryId, classId, count)` can move items from the bag into another inventory, and `stash:GetMasterInventory()` gives a stash's inventory id.
- ✅ **Putting items in the player's home stash (Lua, tested):**
  - Every level (trosecko, kutnohorsko, klaster) has one entity of class `Stash` named `stash[Chest/playerMasterChest_<guid>]` (layer `Main/_script/playerStash`). It is the shared inventory behind all of the player's home stashes.
  - Find it with `System.GetEntitiesByClass("Stash")` and `e:GetName()`. Its inventory id is `e:GetInventoryToOpen()`.
  - Create the item straight in it with `e.inventory:CreateItem(classId, 1, 1)` (as vanilla `ItemUtils.CreateInvItem`). This put both starter items in the home stash on the first try.
  - Fallback: create in the bag with `player.inventory:CreateItem`, then `player.inventory:MoveItemOfClass(inv, classId, 1, true)` (as vanilla `ItemUtils.GiveItem`).
  - Guard it with a hidden perk so it runs once per save.
  - Vanilla ownership test: `EntityModule.GetInventoryOwner(inv) == player.this.id`.
  - ❌ `ItemManager.CreateItem(id, 1, 1)` threw a Lua error for Document items (sketch, recipe book). Use `Inventory:CreateItem`.
  - ❌ `System.GetEntitiesByClass("AnimStash")` threw: `AnimStash.lua` is only the script file name, the entity class is `Stash`.
  - Vanilla Lua for reference: unzip `Data/Scripts.pak`.
- ✅ **Console commands from a mod:** `System.AddCCommand("my_cmd", 'MyMod:Cmd("%1")', "help text")` in `Scripts/mods/<modid>.lua`. `%1` is the first argument; treat an empty or literal `%1` as "no argument". The console needs the game launched with `-devmode`.
- ❌ **Never remove a perk definition that saves may already hold**: the save can freeze on load.
- Text in a language the game doesn't support (e.g. Thai via another mod) doesn't work in recipe books, which use the gothic font. Stick to English.
- Item icon: 64×64 `Libs/UI/Textures/Icons/Items/<IconId>_icon.dds` (rc preset `UiIcon`, `/mipmaps=0`), drawn as a dark silhouette on transparency.

## Tools

| Tool | Notes |
| --- | --- |
| Blender **4.3** (portable is fine) | Blender 5.x dropped COLLADA, which the toolkit uses for both import and export |
| [KCD2 Blender Toolkit](https://github.com/LuneMods/KCD2-Blender-Toolkit) | Two addons: `io_KCD2_Blender_Toolkit` (imports .skin/.cgf) and `io_bcry_exporter` (KCD2 build of BCry) |
| `rc.exe` | From **KCD2 Modding Tools** (free on Steam, ~15 GB): `<Steam>\steamapps\common\KCD2Mod\Tools\rc\rc.exe` |
| 7-Zip | Opens `.pak` files (zip) to pull out reference models and tables |

### Blender → .skin (scripts in this repository's `tools/`)
- `tools/blender_make_skin.py`: imports `crossbow_medium_b.skin` (for the armature) and the gun mesh, rotates/moves it, triangulates, weights everything to `Asset_Crossbow`, adds an export node and exports straight into the mod. Run with `blender.exe -b --python tools/blender_make_skin.py`.
- `tools/blender_make_round.py`: builds the Nodraw round `.cgf` + `.mtl`.
- `tools/meshbox.py` / `tools/bones.py`: read a model's axes/bbox and skeleton bone positions directly from the game files, so you don't have to guess from screenshots.
- `tools/build.py`: packs the mod (skipping `.dae/.blend/.rcdone/.log`) and checks XML, UUID clashes and model paths.

### Gotchas found by running it
- After importing, delete the importers' collections (e.g. `crossbow_medium_b.skin`), or BCry exports them as extra nodes.
- An export node is a collection named `<name>.<type>` under `cry_export_nodes`. A mesh whose parent is an armature gets type `skin` automatically.
- Use `bpy.ops.bcry.export_to_game(filepath=".../<name>.dae")`: the output lands in that `.dae`'s folder. BCry runs rc.exe in the background, so in `-b` mode you must wait for the file to appear before Blender exits.
- BCry material naming: `<node>__<index>__<name>__<physics>` (e.g. `my_round__01__round__physNone`). The cgf looks up `<node>.mtl` next to itself.
- A mesh imported from `.cgf` may sit offset from the bbox stored in the mesh chunk (the cgf node transform gets applied). Measure again after importing.
- `.skin`/`.cgf` hold only one mesh. Triangulate before exporting.

## Installing and testing
- The mod folder name may only use lowercase letters and `_`. Add the modid to `Mods/mod_order.txt`.
- **Close the game before copying files into `Mods/<modid>`** (the game locks the pak). Never copy while the game is starting up: a pak replaced mid-load froze it before the main menu.
- Launch with `-devmode` for the console. Spawn items with your own console command (see above) or with the `cheat` mod: `cheat_add_item any:<name> bulk:true`, `cheat_add_item exact:<ammo> amount:30`.
- Search `kcd.log` for `[Mod]` and `<modid>` to see whether the mod loaded and how many item rows were read.
- Crossbow controls: quick-access slots 1–4 (add the item with "Attach to belt" in the inventory first), left click = load/fire, hold right click = aim.
