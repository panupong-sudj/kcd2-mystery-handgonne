# Development log

How the Mystery Handgonne was built, in the order things were tried. Every result here comes from testing in the real game (KCD2 1.5.x, November 2026). Many approaches look like they should work and don't, so the dead ends are kept.

The tested recipe without the history is in [.claude/skills/kcd2-gun-mod/SKILL.md](../.claude/skills/kcd2-gun-mod/SKILL.md).

## 0. The idea and the constraints

**Goal:** a single-shot rifle in KCD2. Use a crossbow as the base weapon and replace its model with a gun.

**Why a crossbow:**

- It can be raised to aim.
- Its load → fire cycle is one shot at a time, like a bolt-action or lever-action rifle, so no magazine system is needed.

**Why not the vanilla handgonne:**

- It is lit by hand.
- Its hold and its ~20 s reload don't fit a rifle.

**Out of scope:**

- **New animation sets:** no evidence anyone has done this in KCD2.
- **Multi-round magazines and full-auto:** no table field supports them.
- **Binary hooking (ASI/C++):** the KCD2 EULA (section 5) forbids reverse engineering. Only official channels were used: XML/PTF tables, Lua, KCD2 Modding Tools.

## 1. Survey of the game files

The first step was extracting `Data/Tables.pak` and reading every crossbow, bolt and handgonne row.

### Loading mechanics

How a weapon loads lives in `item/weapon_class.xml`, not in the item row. The item points at a class:

| Class | Weapon | Loading |
| --- | --- | --- |
| 10 | Light crossbow | Cocked by hand, ~1.8 s plus ~1 s to place the bolt |
| 14 | Medium crossbow | Goat's-foot lever, ~5 s |
| 15 | Heavy crossbow | Windlass, ~9 s |
| 13 | Rifle (handgonne) | Ammo classes Ball and Shotgun, ~20 s reload |

Every weapon in a class loads the same way. Timings come from `animation/anim_fragment_events.xml`.

### Ammo

- Ammo `Type` must match the class `ammo_class`: 1 Arrow, 2 Bolt, 3 Ball, 4 Shotgun.
- The flying model comes from the ammo row: `Model`, `ShortModel`, `LongModel`.

### Sound and smoke

The handgonne item row has no extra attributes. Its sound and smoke live in animation event files:

| Effect | Where it is defined |
| --- | --- |
| Crossbow shot sound | `crossbow.animevents`: `c_w_crossbow_shot` on the weapon skeleton |
| Handgonne gunshot | `male.animevents` (the character's animation): `c_f_firearm_shot` |
| Handgonne smoke | `hand_cannon.animevents`: effect `firearms.hand_cannon.frontParticleEmit` |

### Models and reload buffs

- Every crossbow model is a `.cdf` on one skeleton, `crossbow.chr`, plus a single `.skin`. The skeleton animates the string and bow, so it is not a static mesh.
- The only reload-speed buff is `perk_salva` (`rls*1.2`, timed).

## 2. Milestone 1: swap the model

Three test items were copies of the medium crossbow:

- **A:** vanilla model, as a control.
- **B:** the vanilla handgonne model.
- **C:** our own `.cdf` with a static mesh on bone `Asset_Crossbow`.

Results:

- **A** worked: the PTF row loads and the item can be spawned.
- **B** did not fire, and the gun stood upright. Another weapon's skeleton lacks the crossbow bones.
- **C** worked once the mesh was rotated X −90° (+Z → +Y), because crossbow forward is +Y. It still fired bolts with the crossbow sound.

## 3. Milestone 2: bullet, gunshot, smoke

This milestone took eight rounds of testing. In order:

1. **A new ammo row with `Type="2"` (Bolt) and lead-ball damage:** the crossbow loads it, and it flies as a ball with lead-ball damage. ✅
2. **The model was invisible until the first load:** the game hides a weapon's `CA_BONE` attachments until it is loaded, to hide the bolt. Moving the mesh to another bone didn't help. **Fix: make the gun a `CA_SKIN`** (a `.skin` with every vertex weighted to `Asset_Crossbow`). It then shows when drawn. ✅
3. **A copied skeleton (`m2_gun.chr` + own `.chrparams` + own `.animevents`):** completely silent. The engine never applies chrparams to a copied `.chr`, even one pointing at the vanilla animevents, so it gets no animations and no events. ❌ Use vanilla `crossbow.chr`.
4. **Overriding `Animations/assets/crossbows/crossbow.animevents` in the mod pak:**
   - The override is loaded. ✅
   - An event's `model` field limits it to characters loaded from that `.cdf`, as long as it is the full path with `objects/`. ✅
   - Without `objects/` it matches nothing. ❌
   - The result: gunshot and smoke on our gun only, and vanilla crossbows unchanged.
5. **The loaded round sat on top of the barrel:**
   - The game snaps it to bone `Crossbow_arrow` at (0, 0.138, 0.06) and ignores `Position`/`RelPosition`. ❌
   - A receiver box hiding it blocked the sights. ❌
   - `Material=` on the ammo row is ignored for the loaded round. ❌
   - **Fix:** the ammo uses our own tiny `.cgf` whose `.mtl` is `Shader="Nodraw"`. The round is invisible loaded and in flight, like a real bullet. ✅

## 4. Milestone 3: the real gun

**Model:** the Henry lever-action rifle by Zverev Kirill (CC BY 4.0). `tools/blender_make_skin.py`:

1. keeps the rifle parts only;
2. converts cm → m and turns it 180° about Z;
3. offsets it onto the crossbow skeleton;
4. joins, triangulates, weights everything to `Asset_Crossbow`, and exports with BCry.

`tools/make_textures.py` converts glTF metal/roughness to the CryEngine diff/spec/ddna set.

**Sighting in:** the rifle's sight line is ~5 cm higher above the grip than the crossbow's, so hands and sights can't both match.

| Try | Result |
| --- | --- |
| Line the sights up with the crossbow aim line | Close, and the reference for the rest. |
| Pitch the gun −7° to line up the sights on screen | ❌ Shots strayed badly. |
| Raise it 6 cm | ❌ Filled the screen (eye distance misjudged). |
| Raise it 2.5 cm | ❌ The gun covered the target. |
| `OFFSET = (0, 0.03, -0.13)` | ✅ Clear view, sights where the bullet goes. |

**Flat trajectory:** no table holds projectile speed or gravity. Speed, and with it damage (`RangedWpnSpeedToAttack`), follows weapon `Power`. Power 1200 (handgonne: 620) makes the shot drop very little. ✅

**Reload:**

- `Class="10"` (light crossbow) removes the goat's-foot lever and shortens the animation. The lever is class 14's class-wide `loading_item_first`.
- A buff `rls*4` (`Cpp:Constant`, buff class 12) is bound to each gun item from Lua with `ItemManager.AddOnEquipBuff(item, buff, true)`. It is active only while that gun is equipped.

**Thunderous Blast:** the perk is C++ and only reacts to real firearms (class 13). The Lua hooks `Player.OnAction`:

- `crossbow_prepare` = aiming;
- `crossbow_execute` while aiming with this gun = a shot.

On the first shot in a fight, if the player has the perk, it applies the perk's own debuff to nearby enemies who are in combat.

**Text:** English only. Thai text, via a font mod, broke in recipe books, which use the gothic font. Newlines in item text are not rendered.

**Icon:** `tools/make_icon.py` renders a 64×64 dark silhouette, compiled with rc preset `UiIcon`.

## 5. Ammo type: can bolts be kept out?

Two attempts:

1. **A new weapon class id 40 with a new ammo class 5:** ❌ The engine rejects unknown class ids. The item fell into Miscellaneous and could not be used.
2. **Class 13 (rifle) on `hand_cannon.chr` with Ball ammo:** works technically and brings native gun sound, smoke and perks. ❌ But it also brings the handgonne hold, aim and reload, and the aiming did not suit this gun.

**Decision:** stay on class 10 and accept that crossbow bolts also fit.

## 6. Alchemy: the cartridge recipe

- Recipe 7101 is a copy of vanilla recipe 54 (lead-shot gunpowder): same ingredients and steps.
- The first version produced vanilla lead balls. With the same base and steps, the brew matched recipe 54 first. ❌ Switching the base to **Oil** made it unique. ✅ Step 2 has its own text ("You will need oil, …").
- Yields were raised to 20/25/30/40 by quality (vanilla 3/5/7/10).
- Recipe book images are tied to the RecipeId:
  - `Libs/UI/Textures/Books/Recipes/<id>_ui.dds` (1024²);
  - `Libs/UI/Textures/Books/Products/<id>_ui.dds` (256²).
  - Without them the page shows an "img" placeholder.
- `tools/make_recipe_images.py` makes them from recipes 54 and 25: oil symbol, oil-yellow liquid, darker powder.

## 7. Smithing: forge it

- The pattern comes from Toxic's More Sketches:
  - a `BlacksmithRecipes__<modid>.xml` row (`WorkpieceId="axe"`, `MinSkillLevel` 12);
  - a hidden "knows recipe" perk with a `perk_script` entry;
  - a sketch `Document` with `BlacksmithRecipeId`.
- One recipe has three products by `MinimalQuality` (the forging score, as in vanilla `basic_sword`): Crude 700, Standard 950, Masterwork 1200.
- The recipe page's stats block only knows melee damage, so Power is written in the description.
  - `Category="Axe"` gives the gold header but an empty stats block and moves the recipe into the axe tab.
  - **Decision: `Category="Other"`.**

## 8. Giving the starter recipes

Goal: put the sketch and the recipe book in the player's home stash, the way DLC items arrive.

1. **`ui/ExtraRewards` rows with no `DlcId`/`ProsId`:** ❌ The game froze while loading the save. Every vanilla row is gated by one of the two.
2. **Removing a perk definition that saves already held:** ❌ Also a freeze on load. **Never remove a perk that may be in saves.**
3. **Lua, round 1:** searched `GetEntitiesByClass("AnimStash")` with an owner check. ❌ Lua error. `AnimStash.lua` is only the script file; the entity class is `Stash`.
4. **Lua, round 2:**
   - Every level has a `Stash` entity named `stash[Chest/playerMasterChest_<guid>]`, the shared inventory behind all home stashes. Found ✅.
   - `ItemManager.CreateItem` then threw for Document items. ❌
5. **Lua, round 3:** `e.inventory:CreateItem(class, 1, 1)` on the master chest, as in vanilla `ItemUtils.CreateInvItem`. ✅ Both items appear in the home stash. A hidden perk marks the save so it runs once.

## 9. Release prep

- **Rename:** the development working name was replaced everywhere by modid `mystery_handgonne`.
  - Item, buff and perk GUIDs did not change, so existing saves keep their guns.
  - The early test items (Milestone 1) were removed.
  - The model was re-exported under the new names.
- **Console commands:** registered from Lua with `System.AddCCommand`.
- **Workshop uploader:** KCD2 Modding Tools ships `Tools/SteamWorkshopUploader`. The modid must match `^[a-z_]+$`.

## References used

- [modding.wiki: Adding a custom weapon (KCD2)](https://modding.wiki/en/kingdomcomedeliverance2/mod-development/disciplines/3d/Addingcustomweapon)
- [Deep Silver: Modding in KCD2](https://www.deepsilver.com/games/kingdom-come-deliverance-ii/news/modding-in-kingdom-come-deliverance-2)
- [KCD2 Development Guide (benjaminfoo)](https://github.com/benjaminfoo/kcd2-development-guide), [KCD Coding Guide](https://github.com/benjaminfoo/KCD-Coding-Guide)
- [KCD2 Lua ScriptBind docs (tkhquang)](https://tkhquang.github.io/KCD2Tools/script_bind/script_bind_2025_01_14/). The same docs ship with KCD2 Modding Tools.
- [KCD2 Blender Toolkit](https://github.com/LuneMods/KCD2-Blender-Toolkit)
- Mods studied:
  - [Kriegsmesser](https://nexusmods.com/kingdomcomedeliverance2/mods/1819) (custom weapon);
  - [Fast Salvo](https://www.nexusmods.com/kingdomcomedeliverance2/mods/353) (`rls` buff);
  - [Bohemian Slayer](https://www.nexusmods.com/kingdomcomedeliverance2/mods/2393) (firearm timing);
  - Toxic's More Sketches (smithing recipes).
- [KCD2 EULA](https://store.steampowered.com//eula/1771300_eula_0): section 5 forbids reverse engineering, which is why this mod uses only tables and Lua.

## Lessons worth repeating

- **Testing:** test in the real game, not the editor. Read `kcd.log`: `[Mod]` lines, and your own `System.LogAlways` lines.
- **Installing:** never copy a pak into `Mods/` while the game is running or starting. A pak replaced mid-load froze the game before the menu.
- **Lua reference:** when you need a Lua API, read the vanilla scripts in `Data/Scripts.pak` and the script_bind docs in KCD2 Modding Tools (`Tools/modding/docs/script_bind`) before guessing.
- **Measuring:** measure from the game files (`tools/bones.py`, `tools/meshbox.py`) instead of estimating from screenshots.
