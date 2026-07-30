#!/usr/bin/env python3
"""Raise the Vigor -> max HP curve in regulation.bin so a levelled character is
effectively unkillable while drilling parry timing.

For practice only: the point is to survive long enough to learn a boss's timing,
not to play the game this way.

The curve lives in CalcCorrectGraph row 100, which is identified from the data
rather than from a hard-coded row id: it is the only row whose x thresholds are
Elden Ring's stat breakpoints 1/25/40/60/99 AND whose y values are the shipped HP
values 300/800/1450/1900/2100. Both halves have to match, so a future patch that
renumbers rows makes this fail loudly instead of writing to the wrong row.

The row's five 'stageMaxGrowVal' floats are the HP at each breakpoint.

The values keep the shipped curve's shape - strictly increasing, no two breakpoints
equal - and only scale it up. A first attempt set all five to a flat 30000 and the
game crashed the moment a character loaded, which is exactly where max HP is computed
from this row. Two things were wrong with that attempt and it does not matter which
one bit: 30000 may overflow something downstream, and a flat curve makes every
segment's slope zero, which is a degenerate input to whatever interpolates between
breakpoints. Staying monotonic and under 10000 avoids both.

That crash is also the strongest evidence available that this really is the player's
HP row: nothing else in the load path was touched.

Install path matters. Writing regulation.bin over the copy in the game directory is
rejected: the game aborts a minute in with `movl $0xdeadba, 0`. Serving the same
bytes through an me3 package is accepted. Measured both ways, same profile, same
save; the only difference was the install path.
"""
import struct
import sys

import elden_ring_regulation as R

PARAM_NAME = "CalcCorrectGraph"
ROW_TABLE_OFF = 0x40
ROW_ENTRY_LEN = 24          # id u32 | pad u32 | data_offset u64 | name_offset u64
STAGE_X_OFF = 0             # stageMaxVal0..4
STAGE_Y_OFF = 20            # stageMaxGrowVal0..4
VIGOR_X = [1.0, 25.0, 40.0, 60.0, 99.0]
VIGOR_Y = [300.0, 800.0, 1450.0, 1900.0, 2100.0]
# Overridable on the command line so a bisect does not need a source edit.
HP_CURVE = [3000.0, 5000.0, 7000.0, 8500.0, 9999.0]


def find_hp_row(param):
    row_count, = struct.unpack_from("<H", param, 0x0A)
    hits = []
    for i in range(row_count):
        rid, _pad, doff, _noff = struct.unpack_from(
            "<IIQQ", param, ROW_TABLE_OFF + i * ROW_ENTRY_LEN)
        x = struct.unpack_from("<5f", param, doff + STAGE_X_OFF)
        y = struct.unpack_from("<5f", param, doff + STAGE_Y_OFF)
        if list(x) == VIGOR_X and list(y) == VIGOR_Y:
            hits.append((rid, doff))
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one Vigor/HP row, found {len(hits)}: "
                         f"{[h[0] for h in hits]}. Refusing to patch.")
    return hits[0]


def main():
    src, dst = sys.argv[1], sys.argv[2]
    curve = [float(v) for v in sys.argv[3].split(",")] if len(sys.argv) > 3 else HP_CURVE
    if len(curve) != 5:
        raise SystemExit("curve needs exactly 5 comma-separated values")
    bnd, meta = R.unpack(src)
    bnd = bytearray(bnd)
    entry = next(e for e in R.bnd4_entries(bnd) if PARAM_NAME in e["name"])
    base = entry["data_off"]
    param = bnd[base:base + entry["size"]]

    rid, doff = find_hp_row(param)
    before = struct.unpack_from("<5f", param, doff + STAGE_Y_OFF)
    struct.pack_into("<5f", bnd, base + doff + STAGE_Y_OFF, *curve)
    after = struct.unpack_from("<5f", bnd, base + doff + STAGE_Y_OFF)
    print(f"CalcCorrectGraph row {rid}: {[round(v) for v in before]} -> "
          f"{[round(v) for v in after]}")

    out = R.pack(bytes(bnd), meta)
    open(dst, "wb").write(out)

    # Gate: the file we just wrote must decode back to exactly the bytes we intended.
    check, _ = R.unpack(dst)
    if check != bytes(bnd):
        raise SystemExit("roundtrip mismatch - not installing")
    print(f"wrote {dst} ({len(out):,} bytes), roundtrip OK")


if __name__ == "__main__":
    main()
