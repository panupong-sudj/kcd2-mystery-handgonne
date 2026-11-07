"""Print the bounding box of every mesh chunk in CryEngine geometry files (.cgf/.skin/.chr) read from the game paks.

Usage: py -I tools/meshbox.py <path inside Objects pak> [...]
  e.g. py -I tools/meshbox.py objects/manmade/weapons/firearms/hand_cannon_a.cgf

Tells which axis a model is long along, so an attachment's RelRotation can be worked out
instead of guessed from screenshots.
"""
import glob
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kcd2paths import GAME_DIR as GAME  # noqa: E402
MESH_CHUNK = 0x1000


def find(path):
    want = path.lower().replace("\\", "/")
    for p in sorted(glob.glob(os.path.join(GAME, "Data", "*.pak"))):
        if "Objects" not in os.path.basename(p):
            continue
        z = zipfile.ZipFile(p)
        for n in z.namelist():
            if n.lower().replace("\\", "/") == want:
                return z.read(n)
    raise SystemExit(f"not found in paks: {path}")


def mesh_boxes(data):
    if data[:4] != b"CrCh":
        raise SystemExit(f"unknown header {data[:4]!r}")
    _ver, count, table = struct.unpack_from("<III", data, 4)
    for i in range(count):
        ctype, cver, cid, _size, off = struct.unpack_from("<HHIII", data, table + i * 16)
        if ctype != MESH_CHUNK:
            continue
        nverts = struct.unpack_from("<i", data, off + 8)[0]
        streams = 16 * 8 if cver >= 0x802 else 16
        box = off + 7 * 4 + streams * 4 + 4 * 4
        mn = struct.unpack_from("<3f", data, box)
        mx = struct.unpack_from("<3f", data, box + 12)
        yield cid, cver, nverts, mn, mx


def positions(data):
    """Yield vertex positions from position data streams (type 0), full or half floats."""
    _ver, count, table = struct.unpack_from("<III", data, 4)
    for i in range(count):
        ctype, _cver, _cid, _size, off = struct.unpack_from("<HHIII", data, table + i * 16)
        if ctype != DATA_STREAM_CHUNK:
            continue
        _flags, stype, n, esize = struct.unpack_from("<iiii", data, off)
        if stype != 0:
            continue
        base = off + 24
        for v in range(n):
            if esize == 12:
                yield struct.unpack_from("<3f", data, base + v * 12)
            elif esize == 8:
                yield struct.unpack_from("<3e", data, base + v * 8)


def width_along(data, axis, across, slices=6):
    """Width on `across` axis in slices along `axis`: the wide end of a crossbow is its prod, i.e. the front."""
    pts = list(positions(data))
    if not pts:
        return None
    lo = min(p[axis] for p in pts)
    hi = max(p[axis] for p in pts)
    step = (hi - lo) / slices
    out = []
    for s in range(slices):
        a, b = lo + s * step, lo + (s + 1) * step
        xs = [p[across] for p in pts if a <= p[axis] <= b]
        out.append((a, b, (max(xs) - min(xs)) if xs else 0.0))
    return out


DATA_STREAM_CHUNK = 0x1016

for path in sys.argv[1:]:
    print(path)
    data = find(path)
    slices = width_along(data, 1, 0)
    if slices:
        print("  width on X per slice along Y:")
        for a, b, w in slices:
            print(f"    Y {a:+.3f}..{b:+.3f}  width {w:.3f}")
    for cid, cver, nverts, mn, mx in mesh_boxes(data):
        size = [b - a for a, b in zip(mn, mx)]
        longest = "XYZ"[size.index(max(size))]
        fmt = lambda v: "(" + ", ".join(f"{c:+.3f}" for c in v) + ")"
        print(f"  mesh chunk {cid} v{cver:#x} verts={nverts} min={fmt(mn)} max={fmt(mx)} size={fmt(size)} longest={longest}")
