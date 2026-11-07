# Releasing to the Steam Workshop

The Workshop gets the **built** mod (`publish/mystery_handgonne/`), never this repository.

## Checklist

1. **Version:** bump `<version>` in `mod/mystery_handgonne/mod.manifest`.
2. **Build:** run `py -I tools/build.py`. It must finish with no errors.
3. **Test:** install the build into `<KCD2>/Mods/` **with the game closed**, then check in game:
   - draw, aim, reload, fire;
   - gunshot and smoke;
   - forge the sketch;
   - brew the cartridges;
   - starter recipes in the home stash on a fresh save;
   - console commands.
4. **Cover image:** use a 16:9 or 1:1 image under 1 MB. An in-game screenshot of the gun firing works best. The current covers are cropped from a firing screenshot into `publish/workshop_cover_16x9.jpg` (1920×1080) and `publish/workshop_cover_1x1.jpg` (1024×1024). Like the build, they are not in git.
5. **Upload:** open `<Steam>/steamapps/common/KCD2Mod/Tools/SteamWorkshopUploader/SteamWorkshopUploader.exe` (part of KCD2 Modding Tools) and fill in:

   | Field | Value |
   | --- | --- |
   | Path to mod folder | `publish/mystery_handgonne` |
   | Path to mod cover image | the cover image |
   | Mod name | Mystery Handgonne |
   | Description | paste [workshop_description.txt](workshop_description.txt) (Steam BBCode) |
   | Tags | Weapons, Combat, Alchemy, Models, Audio |

   The uploader reads `mod.manifest` and refuses a modid that doesn't match `^[a-z_]+$`.
6. **Publish:** after uploading, use **Open in Steam Client** to check the Workshop page, then set its visibility to Public there. The first upload asks you to accept the Steam Workshop legal agreement.

## Notes

- **Ids:** item, buff and perk GUIDs must never change between releases. Saves store them.
- **Perks:** never remove a perk definition that saves may hold. Loading such a save froze the game in testing.
- **Local copies:** a local copy in `Mods/mystery_handgonne` and the subscribed Workshop copy have the same modid. Keep only one of them enabled.
