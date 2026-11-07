"""Print the bind pose of every bone in a CryEngine skeleton (.chr) from a local file.

Usage: py -I tools/bones.py <file.chr>

Reads the CompiledBones layout by name: each bone stores DefaultW2B and DefaultB2W (Matrix34, row-major)
right before its 256-byte name, so we find the names and read the 48 bytes in front of each.
Position is the B2W translation; the axes show where the bone's local X/Y/Z point in model space.
"""
import re
import struct
import sys

data = open(sys.argv[1], "rb").read()
for m in re.finditer(rb"([A-Za-z][A-Za-z0-9_ ]{2,})\x00", data):
    name = m.group(1).decode()
    start = m.start()
    # name field is 256 bytes; the B2W matrix sits in the 48 bytes before it
    if start < 96:
        continue
    b2w = struct.unpack_from("<12f", data, start - 48)
    if not all(abs(v) < 100 for v in b2w):
        continue
    rows = [b2w[0:4], b2w[4:8], b2w[8:12]]
    # columns of the rotation part are the bone's local axes in model space
    if any(abs(sum(r[c] ** 2 for r in rows) - 1) > 0.02 for c in range(3)):
        continue
    pos = (rows[0][3], rows[1][3], rows[2][3])
    ax = lambda c: "(" + ",".join(f"{rows[i][c]:+.2f}" for i in range(3)) + ")"
    print(f"{name:28s} pos=({pos[0]:+.3f},{pos[1]:+.3f},{pos[2]:+.3f})  X={ax(0)} Y={ax(1)} Z={ax(2)}")
