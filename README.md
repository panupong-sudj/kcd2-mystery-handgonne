# Mystery Handgonne: a KCD2 gun mod (source)

> *"A strangely shaped gun that seems to have fallen out of another age."*

A lever-action rifle for **Kingdom Come: Deliverance II**, built on the game's crossbow system with official modding only: XML tables, Lua and the KCD2 Modding Tools. No binary hooks.

This repository is the **development source**: mod files, the scripts that build the model, textures and icon, and notes on what worked and what didn't. The packaged mod for players is published on the Steam Workshop. Build output (`publish/`) is not kept in git.

## What the mod does

- **Aiming:** the gun aims like a crossbow, through the rifle's own iron sights. The bullet flies flat and fast.
- **Gunshot and smoke:** a gunshot sound and muzzle smoke play for this gun only. Vanilla crossbows are unchanged.
- **Reload:** four times faster than a crossbow, only while this gun is equipped. The goat's-foot lever is hidden.
- **Forging:** smith it from a sketch. The forging score decides which version you get:

  | Forging score | Version | Power |
  | --- | --- | --- |
  | 20+ | Crude | 700 |
  | 50+ | Standard | 950 |
  | 75+ | Masterwork | 1200 |

- **Cartridges:** brew them at the alchemy bench. The recipe is like lead shot gunpowder, but with an oil base. One brew gives 20–40.
- **Thunderous Blast:** the perk works with this gun.
- **Starter recipes:** the sketch and the recipe book are placed in the player's home stash, once per save.
- **Console commands:** see below.

## Console commands

Launch the game with `-devmode` (Steam → game Properties → Launch Options), then open the console with `~`.

| Command | Adds to your bag |
| --- | --- |
| `mystery_handgonne_gun [crude\|standard\|masterwork]` | One gun. The default is masterwork. |
| `mystery_handgonne_ammo [count]` | Cartridges. The default is 40. |
| `mystery_handgonne_recipes` | The gun sketch and the cartridge recipe book. |
| `mystery_handgonne_materials [times]` | Smithing materials for one forging, and alchemy ingredients (including oil) for one brew, multiplied by `times`. |
| `mystery_handgonne_all` | Masterwork gun, 40 cartridges, both recipes and one set of materials. |

## Repository layout

```
mod/mystery_handgonne/        the mod source (packed into paks by tools/build.py)
  mod.manifest
  Data/Libs/Tables/...        PTF tables: items, buff, perks, alchemy + smithing recipes
  Data/Objects/weapons/...    .cdf, .skin, round .cgf, materials, textures (.tif sources + compiled .dds)
  Data/Animations/...         crossbow.animevents override (gunshot + smoke, filtered to this gun)
  Data/Scripts/mods/...       Lua: reload buff, Thunderous Blast, starter recipes, console commands
  Localization/English_xml/   item names and descriptions
source/henry_rifle/           source 3D model (CC BY 4.0, see CREDITS.md)
tools/                        build, model, texture, icon and recipe-image scripts
docs/                         DEVLOG (how it was made), BUILDING, RELEASE, Workshop description
.claude/skills/               Claude Code skills with the tested recipe (kcd2-gun-mod, kcd2-blender)
work/   (git-ignored)         vanilla game files extracted for reference, Blender temp files
publish/ (git-ignored)        build output, ready to install or upload
```

## Building

The short version is below. Details are in [docs/BUILDING.md](docs/BUILDING.md).

```bash
py -I tools/extract_refs.py
```

```bash
py -I tools/build.py
```

The first command copies the vanilla references into `work/`. The second packs `mod/mystery_handgonne/` into `publish/mystery_handgonne/`. Copy that folder into `<KCD2>/Mods/` **while the game is closed**.

## Building your own gun on this

Start with [.claude/skills/kcd2-gun-mod/SKILL.md](.claude/skills/kcd2-gun-mod/SKILL.md). It lists every piece of the crossbow-based gun, what was tested, and which tempting approaches fail. Then read [docs/DEVLOG.md](docs/DEVLOG.md) for the reasoning and the dead ends.

When you reuse this code for your own mod:

- generate new UUIDs for every item, buff and perk;
- pick a new modid;
- change the `model=` filter in `crossbow.animevents` to your own `.cdf` path.

## Credits and license

- **Gun model:** [Henry Lever-Action Rifle](https://sketchfab.com/3d-models/henry-lever-action-rifle-98000c9642354a65b3203f76403128db) by **Zverev Kirill**, licensed [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/). It was re-oriented and scaled to the KCD2 crossbow skeleton, merged into one mesh, and its textures were re-baked. See [source/henry_rifle/CREDITS.md](source/henry_rifle/CREDITS.md).
- **Mod author:** panupong-sudj.
- **Code and mod data:** MIT, see [LICENSE](LICENSE). The 3D model and textures derived from it stay under CC BY 4.0. Files copied or adapted from the game remain the property of Warhorse Studios / PLAION and are included only as needed for the mod to work, as is usual for KCD2 mods. That covers the vanilla crossbow animevents events, the alchemy step texts and the recipe images.
- Thanks to the authors of the [KCD2 Blender Toolkit](https://github.com/LuneMods/KCD2-Blender-Toolkit) and of Toxic's More Sketches, whose recipe pattern the forging follows.
