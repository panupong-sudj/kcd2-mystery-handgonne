"""Where the game and the KCD2 Modding Tools are installed.

Set the environment variables KCD2_GAME_DIR and/or KCD2_MODDING_TOOLS_DIR to point at them. Otherwise the usual
Steam library folders below are tried in order.
"""
import os

STEAM_LIBRARIES = [
    r"C:\Program Files (x86)\Steam",
    r"C:\SteamLibrary",
    r"D:\SteamLibrary",
    r"E:\SteamLibrary",
    r"F:\SteamLibrary",
]


def _find(env, folder, must_contain):
    path = os.environ.get(env)
    if path:
        return path
    for lib in STEAM_LIBRARIES:
        candidate = os.path.join(lib, "steamapps", "common", folder)
        if os.path.exists(os.path.join(candidate, must_contain)):
            return candidate
    return os.path.join(STEAM_LIBRARIES[0], "steamapps", "common", folder)


# The game itself ("Kingdom Come: Deliverance II"): must hold Data/*.pak.
GAME_DIR = _find("KCD2_GAME_DIR", "KingdomComeDeliverance2", os.path.join("Data", "Tables.pak"))
# "KCD2 Modding Tools" (free on Steam): rc.exe, the Steam Workshop uploader, script_bind docs.
MODDING_TOOLS_DIR = _find("KCD2_MODDING_TOOLS_DIR", "KCD2Mod", os.path.join("Tools", "rc", "rc.exe"))
RC = os.path.join(MODDING_TOOLS_DIR, "Tools", "rc", "rc.exe")
