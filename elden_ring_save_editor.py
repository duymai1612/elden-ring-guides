#!/usr/bin/env python3
"""
Elden Ring save editor (PC / offline).

Edits an Elden Ring save file (ER0000.sl2, or Seamless Co-op ER0000.co2) directly:
  - list characters (name / level / spendable runes)
  - list held inventory items with quantities
  - set spendable runes
  - set quantity of an item you already own (max 999)
  - add a NEW goods/consumable/material item (weapons/armor are NOT supported here)

Base Elden Ring PC saves are a plaintext BND4 container. The slots are NOT
AES-encrypted; the only integrity guard is a 16-byte MD5 checksum in front of
each block, which this tool recomputes after every edit. (Verified against
ClayAmore/ER-Save-Lib, BenGrn/EldenRingSaveCopier, jtesta/souls_givifier -
souls_givifier states explicitly: "Elden Ring doesn't use encryption".)

SAFETY
  * Close the game and stay OFFLINE (Easy Anti-Cheat will ban online edits).
  * A timestamped .bak backup is written before any change.
  * The tool validates that its structural model matches your file before it
    trusts any offset, and re-validates the written file afterwards. It refuses
    to write if anything looks off, rather than risk corrupting the save.

No third-party dependencies. Python 3.8+.
"""

import argparse
import hashlib
import os
import shutil
import struct
import sys
import time

# ---------------------------------------------------------------------------
# Verified layout constants (PC ER0000.sl2 / .co2)
# ---------------------------------------------------------------------------
CHECKSUM_LEN = 0x10          # 16-byte MD5 in front of each block
SLOT_DATA_LEN = 0x280000     # character-slot body size
SLOT_STRIDE = 0x280010       # checksum(0x10) + data(0x280000)
FIRST_SLOT_CHECKSUM = 0x300  # checksum of slot 0
FIRST_SLOT_DATA = 0x310      # body of slot 0
NUM_CHAR_SLOTS = 10

PC_MAGIC = b"BND4"
PS_MAGIC = bytes([0xCB, 0x01, 0x9C, 0x2C])

# PlayerGameData field offsets (relative to the PGD start inside a slot body).
PGD_STATS_OFF = 0x34         # 8 consecutive u32: vigor,mind,end,str,dex,int,fai,arc
PGD_LEVEL_OFF = 0x60
PGD_RUNES_OFF = 0x64
PGD_RUNES_MEMORY_OFF = 0x68
PGD_NAME_OFF = 0x94          # UTF-16LE, up to 16 chars (after runes_memory + buildup fields)
PGD_NAME_LEN = 32
LEVEL_STAT_BIAS = 79         # invariant: sum(8 stats) == level + 79
MAX_LEVEL = 713
# PGD always sits after the fixed 0x1400-entry gaitem map (>= ~0xA000 bytes),
# so anything before this floor is inside the item map, never PlayerGameData.
PGD_SCAN_FLOOR = 0x8000

# EquipInventoryData (held inventory) geometry.
INV_COMMON_CAP = 2688        # 0xA80 held common items
INV_KEY_CAP = 384            # 0x180 held key items
ITEM_RECORD_LEN = 12         # gaitem_handle u32 | quantity u32 | index u32
MAX_ITEM_QTY = 999

# gaitem-handle high nibble -> category
GAITEM_WEAPON = 0x8
GAITEM_ARMOR = 0x9
GAITEM_ACCESSORY = 0xA
GAITEM_GOODS = 0xB
GAITEM_AOW = 0xC
GOODS_HANDLE_MASK = 0xB0000000       # goods handle    = mask | item_id
TALISMAN_HANDLE_MASK = 0xA0000000    # talisman handle = mask | item_id
ITEM_ID_MASK = 0x0FFFFFFF

# Item name tables (param id -> display name). Seeded with a few verified goods;
# the full set (2000+ goods, 155 talismans) is merged from elden_ring_items.json
# if that file sits next to this script. Goods and talismans both use a
# deterministic gaitem handle, so both can be added by this tool.
KNOWN_GOODS = {
    190: "Rune Arc",
    150: "Furlcalling Finger Remedy",
    2919: "Lord's Rune",
    2050: "Grace Mimic",
    8000: "Stonesword Key",
}
KNOWN_TALISMANS = {}
KNOWN_GOODS_BY_NAME = {v.lower(): k for k, v in KNOWN_GOODS.items()}
KNOWN_TALISMANS_BY_NAME = {}


def _load_item_db():
    """Merge the full goods + talisman name tables from elden_ring_items.json
    (shipped next to this script) if present. Falls back to the built-ins."""
    import json
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(here, "elden_ring_items.json"),
                 os.path.join(os.getcwd(), "elden_ring_items.json")):
        if not os.path.isfile(cand):
            continue
        try:
            with open(cand, encoding="utf-8") as fh:
                data = json.load(fh)
        except (ValueError, OSError):
            return
        for sid, name in data.get("goods", {}).items():
            KNOWN_GOODS[int(sid)] = name
            KNOWN_GOODS_BY_NAME[name.lower()] = int(sid)
        for sid, name in data.get("talismans", {}).items():
            KNOWN_TALISMANS[int(sid)] = name
            KNOWN_TALISMANS_BY_NAME[name.lower()] = int(sid)
        return


_load_item_db()


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------
def u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


def put_u32(buf, off, val):
    struct.pack_into("<I", buf, off, val & 0xFFFFFFFF)


def slot_checksum_off(slot):
    return FIRST_SLOT_CHECKSUM + slot * SLOT_STRIDE


def slot_data_off(slot):
    return FIRST_SLOT_DATA + slot * SLOT_STRIDE


def slot_is_empty(buf, slot):
    """A never-written slot has an all-zero stored checksum."""
    off = slot_checksum_off(slot)
    return buf[off:off + CHECKSUM_LEN] == b"\x00" * CHECKSUM_LEN


def compute_slot_md5(buf, slot):
    off = slot_data_off(slot)
    return hashlib.md5(bytes(buf[off:off + SLOT_DATA_LEN])).digest()


def stored_slot_md5(buf, slot):
    off = slot_checksum_off(slot)
    return bytes(buf[off:off + CHECKSUM_LEN])


def refresh_slot_checksum(buf, slot):
    off = slot_checksum_off(slot)
    buf[off:off + CHECKSUM_LEN] = compute_slot_md5(buf, slot)


# ---------------------------------------------------------------------------
# Loading / validation
# ---------------------------------------------------------------------------
def load_save(path):
    with open(path, "rb") as fh:
        buf = bytearray(fh.read())
    if buf[:4] == PS_MAGIC:
        raise SystemExit("This looks like a PlayStation save (different format). "
                         "This tool only supports the PC .sl2/.co2 save.")
    if buf[:4] != PC_MAGIC:
        raise SystemExit("Not a PC Elden Ring save: missing 'BND4' magic at offset 0.")
    min_len = slot_data_off(NUM_CHAR_SLOTS - 1) + SLOT_DATA_LEN
    if len(buf) < min_len:
        raise SystemExit(f"File too small ({len(buf)} bytes) to hold 10 character slots.")
    return buf


def validate_slot(buf, slot):
    """Non-empty slot must have stored MD5 == computed MD5. Proves our offset
    model is correct for this file before we trust it for editing."""
    if slot_is_empty(buf, slot):
        return True
    return stored_slot_md5(buf, slot) == compute_slot_md5(buf, slot)


def require_valid_slot(buf, slot):
    if slot < 0 or slot >= NUM_CHAR_SLOTS:
        raise SystemExit(f"Slot must be 0..{NUM_CHAR_SLOTS - 1}.")
    if slot_is_empty(buf, slot):
        raise SystemExit(f"Slot {slot} is empty (no character).")
    if not validate_slot(buf, slot):
        raise SystemExit(
            f"Slot {slot} checksum does not match the expected layout.\n"
            "The tool will not edit a file it cannot model safely "
            "(unknown game version, already-modified, or corrupt save).")


def get_slot(buf, slot):
    off = slot_data_off(slot)
    return buf[off:off + SLOT_DATA_LEN]


# ---------------------------------------------------------------------------
# PlayerGameData location (runes / level / name)
# ---------------------------------------------------------------------------
def _plausible_name(slot, pgd):
    """A real PGD has a non-empty UTF-16LE character name at +0x94; a random
    region inside the gaitem map will not."""
    raw = bytes(slot[pgd + PGD_NAME_OFF:pgd + PGD_NAME_OFF + PGD_NAME_LEN])
    try:
        name = raw.decode("utf-16-le")
    except UnicodeDecodeError:
        return False
    return len(name.split("\x00", 1)[0].strip()) >= 1


def find_pgd(slot):
    """Locate PlayerGameData via the invariant: the 8 core stats sum to
    level + 79. PGD sits after the fixed-size gaitem map, so we skip the early
    region and require a plausible character name to rule out a coincidental
    stat-pattern match inside the item map (which would make set-rune write to
    the wrong offset)."""
    scan_end = min(len(slot) - (PGD_NAME_OFF + PGD_NAME_LEN), 0x20000)
    for o in range(PGD_SCAN_FLOOR, scan_end):
        stats = struct.unpack_from("<8I", slot, o + PGD_STATS_OFF)
        if any(s < 1 or s > 99 for s in stats):
            continue
        level = u32(slot, o + PGD_LEVEL_OFF)
        if level < 1 or level > MAX_LEVEL:
            continue
        if sum(stats) != level + LEVEL_STAT_BIAS:
            continue
        # Secondary sanity: max HP is a plausible positive value.
        if not (0 < u32(slot, o + 0x0C) <= 60000):
            continue
        if not _plausible_name(slot, o):
            continue
        return o
    return None


def read_character_name(slot, pgd):
    raw = bytes(slot[pgd + PGD_NAME_OFF:pgd + PGD_NAME_OFF + PGD_NAME_LEN])
    try:
        name = raw.decode("utf-16-le").split("\x00", 1)[0]
    except UnicodeDecodeError:
        name = ""
    return name.strip()


def character_summary(buf, slot):
    if slot_is_empty(buf, slot) or not validate_slot(buf, slot):
        return None
    data = get_slot(buf, slot)
    pgd = find_pgd(data)
    if pgd is None:
        return None
    return {
        "name": read_character_name(data, pgd),
        "level": u32(data, pgd + PGD_LEVEL_OFF),
        "runes": u32(data, pgd + PGD_RUNES_OFF),
    }


# ---------------------------------------------------------------------------
# Held-inventory location
# ---------------------------------------------------------------------------
def _record(slot, base, idx):
    off = base + idx * ITEM_RECORD_LEN
    return u32(slot, off), u32(slot, off + 4), u32(slot, off + 8)  # handle, qty, index


def _handle_valid(handle, quantity):
    if handle == 0:
        return False
    if (handle >> 28) & 0xF not in (GAITEM_WEAPON, GAITEM_ARMOR, GAITEM_ACCESSORY,
                                    GAITEM_GOODS, GAITEM_AOW):
        return False
    return 1 <= quantity <= MAX_ITEM_QTY


def find_held_inventory(slot, start_hint=0):
    """Find EquipInventoryData (held) by its exact 2688-common / 384-key geometry.
    Returns dict with the struct start and the field offsets, or None."""
    common_bytes = INV_COMMON_CAP * ITEM_RECORD_LEN      # 0x7E00
    key_count_rel = 4 + common_bytes                     # 0x7E04
    key_bytes = INV_KEY_CAP * ITEM_RECORD_LEN            # 0x1200
    next_equip_rel = key_count_rel + 4 + key_bytes       # 0x9008
    next_acq_rel = next_equip_rel + 4                    # 0x900C
    struct_len = next_acq_rel + 4                        # 0x9010

    scan_end = len(slot) - struct_len
    for p in range(max(0, start_hint), scan_end):
        common_count = u32(slot, p)
        if common_count < 1 or common_count > INV_COMMON_CAP:
            continue
        h0, q0, _ = _record(slot, p + 4, 0)
        if not _handle_valid(h0, q0):
            continue
        # The record just past the used count should be empty (array not packed).
        if common_count < INV_COMMON_CAP:
            he, _, _ = _record(slot, p + 4, common_count)
            if he != 0:
                continue
        key_count = u32(slot, p + key_count_rel)
        if key_count > INV_KEY_CAP:
            continue
        next_equip = u32(slot, p + next_equip_rel)
        next_acq = u32(slot, p + next_acq_rel)
        if next_equip >= 0x100000 or next_acq >= 0x100000:
            continue
        return {
            "start": p,
            "common_off": p + 4,
            "common_count": common_count,
            "key_count_off": p + key_count_rel,
            "next_equip_off": p + next_equip_rel,
            "next_acq_off": p + next_acq_rel,
        }
    return None


def resolve_inventory(buf, slot):
    data = get_slot(buf, slot)
    pgd = find_pgd(data)
    hint = pgd if pgd is not None else 0
    inv = find_held_inventory(data, start_hint=hint)
    if inv is None:
        raise SystemExit(
            f"Could not locate the held inventory in slot {slot}. "
            "Aborting rather than guessing.")
    return data, inv


def iter_items(data, inv):
    for i in range(inv["common_count"]):
        handle, qty, idx = _record(data, inv["common_off"], i)
        if handle == 0:
            continue
        cat = (handle >> 28) & 0xF
        item_id = handle & ITEM_ID_MASK
        yield i, handle, qty, idx, cat, item_id


def describe_item(cat, item_id):
    if cat == GAITEM_GOODS:
        return KNOWN_GOODS.get(item_id, f"Goods #{item_id}")
    if cat == GAITEM_ACCESSORY:
        return KNOWN_TALISMANS.get(item_id, f"Talisman #{item_id}")
    if cat == GAITEM_WEAPON:
        return "Weapon (handle-referenced)"
    if cat == GAITEM_ARMOR:
        return "Armor (handle-referenced)"
    if cat == GAITEM_AOW:
        return "Ash of War (handle-referenced)"
    return f"Unknown cat {cat:#x}"


# ---------------------------------------------------------------------------
# Safe write
# ---------------------------------------------------------------------------
def backup_file(path):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dst = f"{path}.bak-{stamp}"
    n = 1
    while os.path.exists(dst):
        dst = f"{path}.bak-{stamp}-{n}"
        n += 1
    shutil.copy2(path, dst)
    return dst


def commit(path, buf, edited_slots, assume_yes):
    for slot in edited_slots:
        refresh_slot_checksum(buf, slot)

    print("\nAbout to write changes to:", path)
    if not assume_yes:
        ans = input("Type 'yes' to proceed (a .bak backup will be made first): ").strip().lower()
        if ans != "yes":
            raise SystemExit("Aborted, no changes written.")

    bak = backup_file(path)
    print("Backup written:", bak)
    with open(path, "wb") as fh:
        fh.write(buf)

    verify = load_save(path)
    for slot in edited_slots:
        if not validate_slot(verify, slot):
            raise SystemExit(
                "Post-write verification FAILED for slot "
                f"{slot}. Restore from backup: {bak}")
    print("Write verified: checksums valid for edited slot(s).")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_selftest(args):
    buf = load_save(args.file)
    ok = True
    for slot in range(NUM_CHAR_SLOTS):
        if slot_is_empty(buf, slot):
            print(f"slot {slot}: empty")
            continue
        good = validate_slot(buf, slot)
        ok = ok and good
        print(f"slot {slot}: checksum {'OK' if good else 'MISMATCH'}")
    print("\nModel matches file." if ok else "\nWARNING: model mismatch, do not edit this file.")
    return 0 if ok else 1


def cmd_list(args):
    buf = load_save(args.file)
    print(f"{'slot':>4}  {'name':<20} {'level':>5} {'runes':>12}")
    for slot in range(NUM_CHAR_SLOTS):
        s = character_summary(buf, slot)
        if s is None:
            print(f"{slot:>4}  {'<empty>':<20}")
        else:
            print(f"{slot:>4}  {s['name']:<20} {s['level']:>5} {s['runes']:>12}")


def cmd_list_items(args):
    buf = load_save(args.file)
    require_valid_slot(buf, args.slot)
    data, inv = resolve_inventory(buf, args.slot)
    print(f"held inventory (used common slots: {inv['common_count']})")
    print(f"{'idx':>4}  {'qty':>4}  {'item_id':>8}  name")
    shown = 0
    for i, handle, qty, _, cat, item_id in iter_items(data, inv):
        if args.goods_only and cat != GAITEM_GOODS:
            continue
        print(f"{i:>4}  {qty:>4}  {item_id:>8}  {describe_item(cat, item_id)}")
        shown += 1
    print(f"({shown} items listed)")


def cmd_set_rune(args):
    buf = load_save(args.file)
    require_valid_slot(buf, args.slot)
    if args.value < 0 or args.value > 0xFFFFFFFF:
        raise SystemExit("Rune value out of range (0..4294967295).")
    off = slot_data_off(args.slot)
    data = get_slot(buf, args.slot)
    pgd = find_pgd(data)
    if pgd is None:
        raise SystemExit(f"Could not locate character data in slot {args.slot}.")
    old = u32(data, pgd + PGD_RUNES_OFF)
    put_u32(buf, off + pgd + PGD_RUNES_OFF, args.value)
    print(f"slot {args.slot}: runes {old} -> {args.value}")
    commit(args.file, buf, [args.slot], args.yes)


def _match_item_id(args):
    if args.item_id is not None:
        return args.item_id
    if args.name is not None:
        key = args.name.lower()
        if key in KNOWN_GOODS_BY_NAME:
            return KNOWN_GOODS_BY_NAME[key]
        if key in KNOWN_TALISMANS_BY_NAME:
            return KNOWN_TALISMANS_BY_NAME[key]
        raise SystemExit(f"Unknown item name '{args.name}'. Use --item-id instead.")
    return None


def _resolve_add_target(args):
    """Pick (item_id, handle_mask, category) for add-item. Goods and talismans
    both use a deterministic handle; choose by --talisman or by name table."""
    if args.name is not None:
        key = args.name.lower()
        if args.talisman:
            if key not in KNOWN_TALISMANS_BY_NAME:
                raise SystemExit(f"Unknown talisman name '{args.name}'. Use --item-id.")
            return KNOWN_TALISMANS_BY_NAME[key], TALISMAN_HANDLE_MASK, GAITEM_ACCESSORY
        if key in KNOWN_GOODS_BY_NAME:
            return KNOWN_GOODS_BY_NAME[key], GOODS_HANDLE_MASK, GAITEM_GOODS
        if key in KNOWN_TALISMANS_BY_NAME:
            return KNOWN_TALISMANS_BY_NAME[key], TALISMAN_HANDLE_MASK, GAITEM_ACCESSORY
        raise SystemExit(f"Unknown item name '{args.name}'. Use --item-id instead.")
    if args.item_id is not None:
        if args.talisman:
            return args.item_id, TALISMAN_HANDLE_MASK, GAITEM_ACCESSORY
        return args.item_id, GOODS_HANDLE_MASK, GAITEM_GOODS
    raise SystemExit("Provide --item-id or --name.")


def cmd_set_qty(args):
    buf = load_save(args.file)
    require_valid_slot(buf, args.slot)
    if args.qty < 1 or args.qty > MAX_ITEM_QTY:
        raise SystemExit(f"Quantity must be 1..{MAX_ITEM_QTY} "
                         "(item removal is not supported; leaves no ghost record).")
    off = slot_data_off(args.slot)
    data, inv = resolve_inventory(buf, args.slot)

    target_id = _match_item_id(args)
    hits = []
    for i, handle, qty, _, cat, item_id in iter_items(data, inv):
        if args.index is not None and i == args.index:
            hits.append((i, handle, qty, cat, item_id))
        elif target_id is not None and cat in (GAITEM_GOODS, GAITEM_ACCESSORY) and item_id == target_id:
            hits.append((i, handle, qty, cat, item_id))

    if not hits:
        raise SystemExit("No matching item found. Use 'list-items' to see indexes/ids.")
    if len(hits) > 1 and args.index is None:
        raise SystemExit(f"{len(hits)} items match; pass --index to disambiguate.")

    i, handle, old_qty, cat, item_id = hits[0]
    rec_off = off + inv["common_off"] + i * ITEM_RECORD_LEN
    put_u32(buf, rec_off + 4, args.qty)
    print(f"slot {args.slot}: {describe_item(cat, item_id)} (idx {i}) qty {old_qty} -> {args.qty}")
    commit(args.file, buf, [args.slot], args.yes)


def cmd_add_item(args):
    buf = load_save(args.file)
    require_valid_slot(buf, args.slot)
    if args.qty < 1 or args.qty > MAX_ITEM_QTY:
        raise SystemExit(f"Quantity must be 1..{MAX_ITEM_QTY}.")
    item_id, mask, cat = _resolve_add_target(args)
    if item_id & ~ITEM_ID_MASK:
        raise SystemExit("item-id must be a base param id (0..0x0FFFFFFF), no category bits.")

    off = slot_data_off(args.slot)
    data, inv = resolve_inventory(buf, args.slot)
    handle = mask | item_id

    # Merge into an existing stack if this item is already held.
    for i, h, qty, _, c, iid in iter_items(data, inv):
        if h == handle:
            new_qty = min(qty + args.qty, MAX_ITEM_QTY)
            put_u32(buf, off + inv["common_off"] + i * ITEM_RECORD_LEN + 4, new_qty)
            print(f"slot {args.slot}: {describe_item(cat, item_id)} already held, "
                  f"qty {qty} -> {new_qty}")
            commit(args.file, buf, [args.slot], args.yes)
            return

    count = inv["common_count"]
    if count >= INV_COMMON_CAP:
        raise SystemExit("Held common inventory is full.")
    next_acq = u32(data, inv["next_acq_off"])
    next_equip = u32(data, inv["next_equip_off"])

    rec_off = off + inv["common_off"] + count * ITEM_RECORD_LEN
    put_u32(buf, rec_off + 0, handle)
    put_u32(buf, rec_off + 4, args.qty)
    put_u32(buf, rec_off + 8, next_acq)
    put_u32(buf, off + inv["start"], count + 1)          # common_item_count
    put_u32(buf, off + inv["next_equip_off"], next_equip + 1)
    put_u32(buf, off + inv["next_acq_off"], next_acq + 1)

    print(f"slot {args.slot}: added {describe_item(cat, item_id)} x{args.qty} "
          f"(item_id {item_id}, handle {handle:#010x})")
    commit(args.file, buf, [args.slot], args.yes)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def default_save_path():
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    root = os.path.join(appdata, "EldenRing")
    if not os.path.isdir(root):
        return None
    for entry in os.listdir(root):
        cand = os.path.join(root, entry, "ER0000.sl2")
        if os.path.isfile(cand):
            return cand
    return None


def build_parser():
    p = argparse.ArgumentParser(description="Elden Ring PC save editor (offline).")
    p.add_argument("-f", "--file", default=default_save_path(),
                   help="path to ER0000.sl2 / ER0000.co2 (auto-detected on Windows)")
    p.add_argument("-y", "--yes", action="store_true", help="skip the confirmation prompt")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("selftest", help="verify the tool's model matches your file")
    sp.set_defaults(func=cmd_selftest)

    sp = sub.add_parser("list", help="list characters (name/level/runes)")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("list-items", help="list held inventory items")
    sp.add_argument("--slot", type=int, default=0)
    sp.add_argument("--goods-only", action="store_true")
    sp.set_defaults(func=cmd_list_items)

    sp = sub.add_parser("set-rune", help="set spendable runes")
    sp.add_argument("--slot", type=int, default=0)
    sp.add_argument("value", type=lambda x: int(x, 0))
    sp.set_defaults(func=cmd_set_rune)

    sp = sub.add_parser("set-qty", help="set quantity of an item you already own")
    sp.add_argument("--slot", type=int, default=0)
    sp.add_argument("--index", type=int, help="record index from list-items")
    sp.add_argument("--item-id", type=lambda x: int(x, 0), help="goods/talisman base param id")
    sp.add_argument("--name", help="known goods name (see list-items)")
    sp.add_argument("--qty", type=int, required=True)
    sp.set_defaults(func=cmd_set_qty)

    sp = sub.add_parser("add-item", help="add a NEW goods/consumable or talisman (weapons/armor unsupported)")
    sp.add_argument("--slot", type=int, default=0)
    sp.add_argument("--item-id", type=lambda x: int(x, 0), help="base param id (e.g. 190)")
    sp.add_argument("--name", help="known goods/talisman name (e.g. 'Rune Arc')")
    sp.add_argument("--talisman", action="store_true", help="treat item as a talisman (accessory)")
    sp.add_argument("--qty", type=int, required=True)
    sp.set_defaults(func=cmd_add_item)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.file:
        raise SystemExit("No save file given and none auto-detected. Use --file <path>.")
    if not os.path.isfile(args.file):
        raise SystemExit(f"Save file not found: {args.file}")
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
