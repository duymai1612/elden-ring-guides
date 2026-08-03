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
import subprocess
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
PGD_HP_OFF = 0x08            # 3 consecutive u32: hp, max_hp, base_max_hp
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
# 8 core stats in save order, at PGD+0x34..+0x50 (4 bytes each).
STAT_NAMES = ("vigor", "mind", "endurance", "strength",
              "dexterity", "intelligence", "faith", "arcane")
WRETCH_STATS = 10   # every stat at 10 -> level 1 (the blank-slate class base)

# EquipInventoryData (held inventory) geometry.
INV_COMMON_CAP = 2688        # 0xA80 held common items
INV_KEY_CAP = 384            # 0x180 held key items
ITEM_RECORD_LEN = 12         # gaitem_handle u32 | quantity u32 | index u32
MAX_ITEM_QTY = 999

# Armor stores its protector param id offset by this in the gaitem map, so the
# raw value on disk for White Mask (param 680000) is 0x10000000 | 680000.
ARMOR_ITEM_ID_OFF = 0x10000000

# gaitem-handle high nibble -> category
GAITEM_WEAPON = 0x8
GAITEM_ARMOR = 0x9
GAITEM_ACCESSORY = 0xA
GAITEM_GOODS = 0xB
GAITEM_AOW = 0xC
GOODS_HANDLE_MASK = 0xB0000000       # goods handle    = mask | item_id
TALISMAN_HANDLE_MASK = 0xA0000000    # talisman handle = mask | item_id
ITEM_ID_MASK = 0x0FFFFFFF

# Ashes of War are handle-referenced: the inventory record only stores an
# allocated handle, and the gem id lives in a separate gaitem map entry at the
# start of the slot. Layout verified against a real save: 8-byte entries
# {gaitem_handle u32, item_id u32}, empty ones written as {0, 0xFFFFFFFF},
# item_id carrying a 0x80000000 flag on top of the EquipParamGem id.
GAITEM_ARRAY_START = 0x20
GAITEM_ENTRY_LEN = 8
GAITEM_EMPTY_ITEM_ID = 0xFFFFFFFF
AOW_HANDLE_BASE = 0xC0800000         # handle = base | allocation counter
AOW_ITEM_ID_FLAG = 0x80000000
# The game allocates handle counters sequentially and stores no counter we can
# safely bump, so new handles start far above anything a playthrough reaches
# (observed max on a level-461 save: ~0xD23). This keeps the game's own
# allocations from ever colliding with ours.
AOW_HANDLE_COUNTER_BASE = 0x10000

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
KNOWN_AOW = {}
KNOWN_WEAPONS = {}
KNOWN_ARMOR = {}
KNOWN_GOODS_BY_NAME = {v.lower(): k for k, v in KNOWN_GOODS.items()}
KNOWN_TALISMANS_BY_NAME = {}
KNOWN_AOW_BY_NAME = {}
KNOWN_WEAPONS_BY_NAME = {}
KNOWN_ARMOR_BY_NAME = {}


def _load_item_db():
    """Merge the full name tables shipped next to this script. Both files are
    read: the base one carries goods + talismans, the full reference adds the
    Ash of War (EquipParamGem) table. Falls back to the built-ins."""
    import json
    here = os.path.dirname(os.path.abspath(__file__))
    seen = set()
    for fname in ("elden_ring_items.json", "elden_ring_items_full_reference.json"):
        for cand in (os.path.join(here, fname), os.path.join(os.getcwd(), fname)):
            if not os.path.isfile(cand) or cand in seen:
                continue
            seen.add(cand)
            try:
                with open(cand, encoding="utf-8") as fh:
                    data = json.load(fh)
            except (ValueError, OSError):
                break
            for sid, name in data.get("goods", {}).items():
                KNOWN_GOODS[int(sid)] = name
                KNOWN_GOODS_BY_NAME[name.lower()] = int(sid)
            for sid, name in data.get("talismans", {}).items():
                KNOWN_TALISMANS[int(sid)] = name
                KNOWN_TALISMANS_BY_NAME[name.lower()] = int(sid)
            # The gem table lists several ids per skill (per-weapon-class
            # variants); the save only ever stores the multiple-of-100 base id,
            # so ignore the rest to keep name lookup unambiguous.
            for sid, name in data.get("ashes_of_war", {}).items():
                if int(sid) % 100:
                    continue
                KNOWN_AOW[int(sid)] = name
                KNOWN_AOW_BY_NAME.setdefault(name.lower(), int(sid))
            for sid, name in data.get("weapons", {}).items():
                KNOWN_WEAPONS[int(sid)] = name
                KNOWN_WEAPONS_BY_NAME.setdefault(name.lower(), int(sid))
            # The first few dozen protector rows are engine placeholders named
            # "Type 1", "Type 2"... - real gear starts after them, so drop those
            # or a name lookup for a real piece can collide with a placeholder.
            for sid, name in data.get("armor", {}).items():
                if name.startswith("Type "):
                    continue
                KNOWN_ARMOR[int(sid)] = name
                KNOWN_ARMOR_BY_NAME.setdefault(name.lower(), int(sid))
            break


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
        # max_hp is worth surfacing because it is not a value you can set: the game
        # recomputes it from Vigor on load and writes the result back here. That
        # makes it a read-only oracle for whether something actually changed the
        # HP curve - vanilla Elden Ring gives 2100 at Vigor 99 and 522 at Vigor 15.
        "vigor": u32(data, pgd + PGD_STATS_OFF),
        "max_hp": u32(data, pgd + PGD_HP_OFF + 4),
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
        key_count = u32(slot, p + key_count_rel)
        if key_count > INV_KEY_CAP:
            continue
        next_equip = u32(slot, p + next_equip_rel)
        next_acq = u32(slot, p + next_acq_rel)
        if next_equip >= 0x100000 or next_acq >= 0x100000:
            continue
        # Decisive check: the real held inventory has exactly common_count
        # non-zero common records and key_count non-zero key records. A stray
        # in-range u32 a few records into the real array is followed by the
        # SAME item bytes, so its declared count no longer matches the non-zero
        # record total - that false match is skipped here.
        nz_common = sum(1 for k in range(INV_COMMON_CAP)
                        if u32(slot, p + 4 + k * ITEM_RECORD_LEN) != 0)
        if nz_common != common_count:
            continue
        key_arr = p + key_count_rel + 4
        nz_key = sum(1 for k in range(INV_KEY_CAP)
                     if u32(slot, key_arr + k * ITEM_RECORD_LEN) != 0)
        if nz_key != key_count:
            continue
        return {
            "start": p,
            "common_off": p + 4,
            "common_count": common_count,
            "key_count_off": p + key_count_rel,
            "key_off": key_arr,
            "key_count": key_count,
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


def iter_gaitem_entries(slot, pgd):
    """Walk the gaitem map that sits between the slot header and PlayerGameData.
    Yields (offset, handle, item_id).

    Entries are VARIABLE-SIZE on disk: the {handle, item_id} pair is always 8
    bytes, but a live weapon carries 13 trailing bytes and a live armour piece 8.
    Walking a flat 8 bytes desyncs at the first weapon and every later entry is
    then read from the middle of the previous record - which also made
    find_free_gaitem() hand back an offset inside a weapon's trailing bytes.
    Verified against a real save: parsing to PlayerGameData lands exactly on it,
    and re-serializing the walk reproduces the region byte-for-byte."""
    off = GAITEM_ARRAY_START
    while off + GAITEM_ENTRY_LEN <= pgd:
        handle, item_id = struct.unpack_from("<II", slot, off)
        yield off, handle, item_id
        off += GAITEM_ENTRY_LEN + gaitem_extra_len(handle, item_id)


def gaitem_extra_len(handle, item_id):
    """Trailing bytes after the {handle, item_id} pair for a live entry."""
    if handle == 0 or item_id == GAITEM_EMPTY_ITEM_ID:
        return 0
    cat = (handle >> 28) & 0xF
    if cat == GAITEM_WEAPON:
        return 13
    if cat == GAITEM_ARMOR:
        return 8
    return 0


def gaitem_map(slot, pgd):
    """handle -> item_id, for naming handle-referenced inventory records."""
    return {h: iid for _, h, iid in iter_gaitem_entries(slot, pgd) if h}


def find_free_gaitem(slot, pgd):
    """Offset of the first entry carrying the canonical empty marker
    {handle 0, item_id -1}. Anything else is live data and must not be reused:
    an entry with no inventory record is usually an Ash of War already applied
    to a weapon."""
    for off, handle, item_id in iter_gaitem_entries(slot, pgd):
        if handle == 0 and item_id == GAITEM_EMPTY_ITEM_ID:
            return off
    return None


def used_handles(slot, pgd, inv):
    """Every handle the save already refers to, from the gaitem map and from
    both inventory arrays, so a freshly allocated one cannot collide."""
    taken = {h for _, h, _ in iter_gaitem_entries(slot, pgd) if h}
    for arr, cap in ((inv["common_off"], INV_COMMON_CAP), (inv["key_off"], INV_KEY_CAP)):
        for _, handle, _, _ in _iter_records(slot, arr, cap):
            taken.add(handle)
    return taken


def _iter_records(data, arr_off, cap):
    """Yield (index, handle, qty, acq_index) for every non-zero record. The
    array is SPARSE - items can sit past the count-th slot with gaps between -
    so walk the whole capacity, not just the first `count` slots."""
    for k in range(cap):
        handle, qty, idx = _record(data, arr_off, k)
        if handle != 0:
            yield k, handle, qty, idx


def _first_free(data, arr_off, cap):
    """Index of the first empty (zero-handle) slot, or None if the array is full."""
    for k in range(cap):
        if u32(data, arr_off + k * ITEM_RECORD_LEN) == 0:
            return k
    return None


def iter_items(data, inv):
    for k, handle, qty, idx in _iter_records(data, inv["common_off"], INV_COMMON_CAP):
        cat = (handle >> 28) & 0xF
        item_id = handle & ITEM_ID_MASK
        yield k, handle, qty, idx, cat, item_id


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


# Substrings that identify a live game session. The game's argv is a WINDOWS
# path even when it runs under Wine, so anything written with forward slashes
# never matches - these deliberately key off the bare directory / binary names.
GAME_PROCESS_MARKERS = ("ELDEN RING", "eldenring.exe", "me3-launcher", "me3.exe")
# A shell or python invocation that merely MENTIONS the save path also carries
# the marker in its argv - including this tool's own command line. Those are not
# game sessions, and treating them as such would block every write made from a
# command line that names the game directory.
NON_GAME_MARKERS = ("/bin/sh", "/bin/zsh", "/bin/bash", "python", os.path.basename(__file__))


def running_game_processes():
    """Command lines of any live Elden Ring / me3 process, best effort.

    Editing the save while the game is up is silently useless: the game holds
    the whole save in memory and rewrites the file on its next autosave, so the
    edit lands, verifies clean, and then vanishes minutes later with nothing to
    show it ever happened. Cheaper to refuse the write than to debug that.

    Returns an empty list when the process list cannot be read, so a platform
    this does not understand degrades to the old behaviour instead of blocking.
    """
    cmd = ["tasklist", "/fo", "csv", "/nh"] if os.name == "nt" else ["ps", "-Ao", "args="]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [line.strip()[:110] for line in out.splitlines()
            if any(marker in line for marker in GAME_PROCESS_MARKERS)
            and not any(marker in line for marker in NON_GAME_MARKERS)]


def commit(path, buf, edited_slots, assume_yes, ignore_running_game=False):
    if not ignore_running_game:
        live = running_game_processes()
        if live:
            listing = "\n  ".join(live[:4])
            raise SystemExit(
                "The game appears to be RUNNING. Refusing to write.\n  "
                + listing
                + "\n\nThe game keeps the save in memory and overwrites the file on its "
                  "next autosave, so this edit would be thrown away without any error. "
                  "Quit the game, wait for the session to clear, then run this again.\n"
                  "Pass --ignore-running-game to write anyway.")

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
    print(f"{'slot':>4}  {'name':<20} {'level':>5} {'runes':>12} {'vigor':>6} {'max_hp':>7}")
    for slot in range(NUM_CHAR_SLOTS):
        s = character_summary(buf, slot)
        if s is None:
            print(f"{slot:>4}  {'<empty>':<20}")
        else:
            print(f"{slot:>4}  {s['name']:<20} {s['level']:>5} {s['runes']:>12} "
                  f"{s['vigor']:>6} {s['max_hp']:>7}")


def cmd_list_items(args):
    buf = load_save(args.file)
    require_valid_slot(buf, args.slot)
    data, inv = resolve_inventory(buf, args.slot)
    # Ashes of War carry no id in the record itself, so resolve them through the
    # gaitem map to print a real name instead of "handle-referenced".
    pgd = find_pgd(data)
    gamap = gaitem_map(data, pgd) if pgd is not None else {}
    print(f"held inventory (used common slots: {inv['common_count']})")
    print(f"{'idx':>4}  {'qty':>4}  {'item_id':>8}  name")
    shown = 0
    for i, handle, qty, _, cat, item_id in iter_items(data, inv):
        if args.goods_only and cat != GAITEM_GOODS:
            continue
        label = describe_item(cat, item_id)
        if cat == GAITEM_AOW and handle in gamap:
            gem = gamap[handle] & ~AOW_ITEM_ID_FLAG
            label = KNOWN_AOW.get(gem, f"Ash of War #{gem}")
        print(f"{i:>4}  {qty:>4}  {item_id:>8}  {label}")
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
    commit(args.file, buf, [args.slot], args.yes, args.ignore_running_game)


def cmd_set_stats(args):
    """Respec: write the 8 core stats directly and set level = sum - 79 so the
    save invariant holds. Class is irrelevant (raw values are written). HP/FP/
    stamina are recomputed by the game on load - rest at a Site of Grace to
    refresh the bars."""
    buf = load_save(args.file)
    require_valid_slot(buf, args.slot)
    off = slot_data_off(args.slot)
    data = get_slot(buf, args.slot)
    pgd = find_pgd(data)
    if pgd is None:
        raise SystemExit(f"Could not locate character data in slot {args.slot}.")

    cur = [u32(data, pgd + PGD_STATS_OFF + i * 4) for i in range(8)]
    if args.wretch:
        new = [WRETCH_STATS] * 8
    else:
        new = list(cur)
        for i, name in enumerate(STAT_NAMES):
            v = getattr(args, name)
            if v is not None:
                new[i] = v
        if new == cur:
            raise SystemExit("No stats given. Use --wretch or --vigor/--mind/... values.")

    for i, v in enumerate(new):
        if v < 1 or v > 99:
            raise SystemExit(f"{STAT_NAMES[i]} must be 1..99 (got {v}).")
    level = sum(new) - LEVEL_STAT_BIAS
    if level < 1 or level > MAX_LEVEL:
        raise SystemExit(f"Stats sum to level {level}, out of range 1..{MAX_LEVEL}.")

    for i, v in enumerate(new):
        put_u32(buf, off + pgd + PGD_STATS_OFF + i * 4, v)
    old_level = u32(data, pgd + PGD_LEVEL_OFF)
    put_u32(buf, off + pgd + PGD_LEVEL_OFF, level)

    print(f"slot {args.slot}: level {old_level} -> {level}")
    for i, name in enumerate(STAT_NAMES):
        print(f"  {name:12} {cur[i]:>3} -> {new[i]:>3}")
    commit(args.file, buf, [args.slot], args.yes, args.ignore_running_game)


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
    commit(args.file, buf, [args.slot], args.yes, args.ignore_running_game)


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

    # Key items (medallions, maps, cookbooks, crystal tears...) live in the
    # separate key-items array; everything else (consumables, materials,
    # talismans...) in the common array. The two acquisition counters at the
    # end of the struct are shared by both.
    if args.key:
        arr_off, count = inv["key_off"], inv["key_count"]
        count_off, cap = inv["key_count_off"], INV_KEY_CAP
    else:
        arr_off, count = inv["common_off"], inv["common_count"]
        count_off, cap = inv["start"], INV_COMMON_CAP

    # Merge into an existing stack if already held (scan the whole array; it
    # can be sparse, with items past the count-th slot).
    for k, h, qty, _ in _iter_records(data, arr_off, cap):
        if h == handle:
            new_qty = min(qty + args.qty, MAX_ITEM_QTY)
            put_u32(buf, off + arr_off + k * ITEM_RECORD_LEN + 4, new_qty)
            print(f"slot {args.slot}: {describe_item(cat, item_id)} already held, "
                  f"qty {qty} -> {new_qty}")
            commit(args.file, buf, [args.slot], args.yes, args.ignore_running_game)
            return

    # Write into the first FREE slot (NOT index==count: the array has gaps, so
    # count is not the next free index). Then bump the count field by one.
    free = _first_free(data, arr_off, cap)
    if free is None:
        raise SystemExit("That inventory array is full.")
    next_acq = u32(data, inv["next_acq_off"])
    next_equip = u32(data, inv["next_equip_off"])

    rec_off = off + arr_off + free * ITEM_RECORD_LEN
    put_u32(buf, rec_off + 0, handle)
    put_u32(buf, rec_off + 4, args.qty)
    put_u32(buf, rec_off + 8, next_acq)
    put_u32(buf, off + count_off, count + 1)             # common_ or key_item_count
    put_u32(buf, off + inv["next_equip_off"], next_equip + 1)
    put_u32(buf, off + inv["next_acq_off"], next_acq + 1)

    where = "key" if args.key else "common"
    print(f"slot {args.slot}: added {describe_item(cat, item_id)} x{args.qty} "
          f"(item_id {item_id}, handle {handle:#010x}, {where} array slot {free})")
    commit(args.file, buf, [args.slot], args.yes, args.ignore_running_game)


def _resolve_aow_target(args):
    """Pick the EquipParamGem id for add-aow, by id or by name (the 'Ash of War: '
    prefix is optional)."""
    if args.gem_id is not None:
        return args.gem_id
    if args.name is None:
        raise SystemExit("Provide --gem-id or --name.")
    key = args.name.lower()
    for cand in (key, f"ash of war: {key}"):
        if cand in KNOWN_AOW_BY_NAME:
            return KNOWN_AOW_BY_NAME[cand]
    raise SystemExit(f"Unknown Ash of War '{args.name}'. Use --gem-id instead.")


def cmd_add_aow(args):
    """Add an Ash of War. Unlike goods it needs two writes: a gaitem map entry
    holding the gem id, plus an inventory record pointing at that entry through
    a freshly allocated handle."""
    buf = load_save(args.file)
    require_valid_slot(buf, args.slot)
    gem_id = _resolve_aow_target(args)
    if gem_id & ~ITEM_ID_MASK:
        raise SystemExit("gem-id must be a base EquipParamGem id.")

    off = slot_data_off(args.slot)
    data = get_slot(buf, args.slot)
    pgd = find_pgd(data)
    if pgd is None:
        raise SystemExit(f"Could not locate character data in slot {args.slot}.")
    inv = find_held_inventory(data, start_hint=pgd)
    if inv is None:
        raise SystemExit(f"Could not locate the held inventory in slot {args.slot}.")

    ga_off = find_free_gaitem(data, pgd)
    if ga_off is None:
        raise SystemExit("No free gaitem map entry left.")
    free = _first_free(data, inv["common_off"], INV_COMMON_CAP)
    if free is None:
        raise SystemExit("The common inventory array is full.")

    taken = used_handles(data, pgd, inv)
    counter = AOW_HANDLE_COUNTER_BASE
    while (AOW_HANDLE_BASE | counter) in taken:
        counter += 1
    handle = AOW_HANDLE_BASE | counter

    next_acq = u32(data, inv["next_acq_off"])
    next_equip = u32(data, inv["next_equip_off"])

    struct.pack_into("<II", buf, off + ga_off, handle, AOW_ITEM_ID_FLAG | gem_id)
    rec_off = off + inv["common_off"] + free * ITEM_RECORD_LEN
    put_u32(buf, rec_off + 0, handle)
    put_u32(buf, rec_off + 4, 1)          # one gaitem entry backs exactly one copy
    put_u32(buf, rec_off + 8, next_acq)
    put_u32(buf, off + inv["start"], inv["common_count"] + 1)
    put_u32(buf, off + inv["next_equip_off"], next_equip + 1)
    put_u32(buf, off + inv["next_acq_off"], next_acq + 1)

    name = KNOWN_AOW.get(gem_id, f"Ash of War #{gem_id}")
    print(f"slot {args.slot}: added {name} (gem_id {gem_id}, handle {handle:#010x}, "
          f"gaitem offset {ga_off:#x}, common array slot {free})")
    commit(args.file, buf, [args.slot], args.yes, args.ignore_running_game)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def cmd_set_hp(args):
    """Raise the stored HP pool.

    CAVEAT: the game derives max HP from Vigor plus equipment, so it may well
    recompute this on load and throw the written value away. Nothing here can
    grant invincibility - that needs runtime memory patching, not a save edit.
    Treat this as an experiment and keep the backup."""
    buf = load_save(args.file)
    require_valid_slot(buf, args.slot)
    if args.value < 1 or args.value > 0xFFFFFF:
        raise SystemExit("HP must be 1..16777215 (keep it sane; huge values may "
                         "display or clamp oddly).")
    off = slot_data_off(args.slot)
    data = get_slot(buf, args.slot)
    pgd = find_pgd(data)
    old = struct.unpack_from("<3I", data, pgd + PGD_HP_OFF)
    for i in range(3):                      # hp, max_hp, base_max_hp
        put_u32(buf, off + pgd + PGD_HP_OFF + i * 4, args.value)
    print(f"slot {args.slot}: hp/max_hp/base_max_hp {old} -> "
          f"({args.value}, {args.value}, {args.value})")
    print("  note: the game may recalculate max HP from Vigor on load and undo this")
    commit(args.file, buf, [args.slot], args.yes, args.ignore_running_game)


def weapon_base_id(item_id):
    """Strip affinity + upgrade level. Weapon param ids are base + affinity*100 +
    level, and every base is a multiple of 10000 (Uchigatana 9000000, Blood +25 =
    9001125 -> 9000000)."""
    return item_id - item_id % 10000


def _resolve_weapon_id(token, what):
    """Accept a numeric param id or a name from the weapon table."""
    if token is None:
        raise SystemExit(f"Provide --{what}.")
    try:
        return int(token, 0)
    except ValueError:
        pass
    hit = KNOWN_WEAPONS_BY_NAME.get(token.lower())
    if hit is None:
        raise SystemExit(f"Unknown weapon name '{token}' for --{what}. "
                         "Pass a numeric param id instead.")
    return hit


def weapon_label(item_id):
    lvl = item_id % 100
    name = KNOWN_WEAPONS.get(item_id) or KNOWN_WEAPONS.get(weapon_base_id(item_id))
    return (name or f"Weapon #{item_id}") + (f" +{lvl}" if lvl else "")


def _resolve_armor_id(token, what):
    """Accept a numeric protector param id or a name from the armor table."""
    if token is None:
        raise SystemExit(f"Provide --{what}.")
    try:
        return int(token, 0)
    except ValueError:
        pass
    hit = KNOWN_ARMOR_BY_NAME.get(token.lower())
    if hit is None:
        raise SystemExit(f"Unknown armor name '{token}' for --{what}. "
                         "Pass a numeric param id instead.")
    return hit


def armor_label(param_id):
    return KNOWN_ARMOR.get(param_id) or f"Armor #{param_id}"


def cmd_replace_armor(args):
    """Retarget a piece of armor you own to a different piece.

    Same trick as replace-weapon and the same reason it is safe: only the
    item_id field of an existing gaitem entry is rewritten, so the record keeps
    its size, the handle and the inventory record are untouched, and nothing in
    the slot shifts. Adding a brand new piece is impossible for the same reason
    it is impossible for weapons - there is no spare room in the slot.

    Armor stores its protector param id offset by ARMOR_ITEM_ID_OFF in the
    gaitem map, so the raw value on disk is 0x10000000 | param_id. Callers deal
    in plain param ids (White Mask = 680000) and this converts."""
    buf = load_save(args.file)
    require_valid_slot(buf, args.slot)
    src_id = _resolve_armor_id(args.source, "source")
    dst_id = _resolve_armor_id(args.target, "target")
    if src_id == dst_id:
        raise SystemExit(f"Source and target are both {armor_label(src_id)}; nothing to do.")

    off = slot_data_off(args.slot)
    data, inv = resolve_inventory(buf, args.slot)
    pgd = find_pgd(data)

    # Walk the INVENTORY and resolve back into the gaitem map, never the other
    # way round. A gaitem entry with no inventory record behind it is dead
    # weight the game ignores on load and drops on its next save, so retargeting
    # one produces a piece that never shows up in game (measured: 24 of 218
    # armor entries on this save are orphans like that).
    held_handles = set()
    for arr, cap in ((inv["common_off"], INV_COMMON_CAP), (inv["key_off"], INV_KEY_CAP)):
        for _, handle, _, _ in _iter_records(data, arr, cap):
            held_handles.add(handle)

    hits = []
    for ent_off, handle, iid in iter_gaitem_entries(data, pgd):
        if not handle or ((handle >> 28) & 0xF) != GAITEM_ARMOR:
            continue
        if iid - ARMOR_ITEM_ID_OFF == src_id and handle in held_handles:
            hits.append((ent_off, handle, iid))

    if not hits:
        raise SystemExit(f"No armor in your inventory matches --source {args.source}. "
                         "Run list-armor to see what you carry (pieces marked "
                         "'orphan' are not usable as a donor).")
    if len(hits) > 1 and args.index is None:
        listing = ", ".join(f"gaitem {o:#x}" for o, _, _ in hits)
        raise SystemExit(f"{len(hits)} copies match ({listing}). Pass --index "
                         "with the 0-based position to pick one.")
    idx = args.index or 0
    if idx >= len(hits):
        raise SystemExit(f"--index {idx} is out of range ({len(hits)} match).")

    ent_off, handle, _ = hits[idx]
    put_u32(buf, off + ent_off + 4, ARMOR_ITEM_ID_OFF | dst_id)
    print(f"slot {args.slot}: gaitem {ent_off:#x} (handle {handle:#010x})\n"
          f"  {armor_label(src_id)}  ->  {armor_label(dst_id)}")
    print("  the donor piece is gone")
    commit(args.file, buf, [args.slot], args.yes, args.ignore_running_game)


def cmd_list_armor(args):
    """List owned armor, flagging entries with no inventory record behind them.

    Those orphans are invisible in game and the game drops them on its next
    save, so they must not be used as a replace-armor donor."""
    buf = load_save(args.file)
    require_valid_slot(buf, args.slot)
    data, inv = resolve_inventory(buf, args.slot)
    pgd = find_pgd(data)
    if pgd is None:
        raise SystemExit(f"Could not locate character data in slot {args.slot}.")

    held_handles = set()
    for arr, cap in ((inv["common_off"], INV_COMMON_CAP), (inv["key_off"], INV_KEY_CAP)):
        for _, handle, _, _ in _iter_records(data, arr, cap):
            held_handles.add(handle)

    rows = []
    for _, handle, iid in iter_gaitem_entries(data, pgd):
        if handle and ((handle >> 28) & 0xF) == GAITEM_ARMOR:
            rows.append((iid - ARMOR_ITEM_ID_OFF, handle in held_handles))

    print(f"{'param_id':>9}  name")
    for pid, in_bag in sorted(rows):
        print(f"{pid:>9}  {armor_label(pid)}{'' if in_bag else '   [orphan]'}")
    live = sum(1 for _, in_bag in rows if in_bag)
    print(f"({len(rows)} entries, {live} in inventory, {len(rows) - live} orphan)")


def cmd_replace_weapon(args):
    """Retarget a weapon you already own to a different weapon.

    Adding a BRAND NEW weapon is not possible on a real save: a new gaitem map
    entry costs 13 more bytes than the empty one it replaces, and the whole slot
    tail would have to shift forward to absorb that. Slots are a fixed 0x280000
    and a played save has no trailing padding left (measured: 0 bytes free on a
    level-675 slot), so the shift would push live data off the end.

    Rewriting the item_id of an entry that is ALREADY a weapon keeps the record
    exactly 21 bytes, so nothing moves: the handle, the inventory record and
    every counter stay untouched, and anything else referencing that handle stays
    valid. The cost is that the donor weapon is consumed."""
    buf = load_save(args.file)
    require_valid_slot(buf, args.slot)
    src_id = _resolve_weapon_id(args.source, "source")
    dst_id = _resolve_weapon_id(args.target, "target")

    off = slot_data_off(args.slot)
    data, inv = resolve_inventory(buf, args.slot)
    pgd = find_pgd(data)
    entries = {h: (o, iid) for o, h, iid in iter_gaitem_entries(data, pgd) if h}

    hits = []
    for k, handle, qty, _, cat, _ in iter_items(data, inv):
        if cat != GAITEM_WEAPON or handle not in entries:
            continue
        ent_off, real = entries[handle]
        if real == src_id or weapon_base_id(real) == weapon_base_id(src_id):
            hits.append((k, handle, ent_off, real))

    if not hits:
        raise SystemExit(f"No held weapon matches --source {args.source}. "
                         "Run list-items to see what you carry.")
    if len(hits) > 1 and args.index is None:
        listing = ", ".join(f"idx {k} ({weapon_label(r)})" for k, _, _, r in hits)
        raise SystemExit(f"{len(hits)} weapons match: {listing}. Pass --index.")
    if args.index is not None:
        hits = [h for h in hits if h[0] == args.index]
        if not hits:
            raise SystemExit(f"--index {args.index} is not one of the matches.")

    k, handle, ent_off, real = hits[0]
    # Same base id is fine and is how an upgrade is expressed: the level lives in
    # the last two digits, so Great Stars +0 -> +25 is 12180000 -> 12180025. Only
    # an identical id is a genuine no-op.
    if real == dst_id:
        raise SystemExit(f"Already {weapon_label(real)}; nothing to do.")

    put_u32(buf, off + ent_off + 4, dst_id)
    print(f"slot {args.slot}: inventory idx {k} (handle {handle:#010x}, gaitem "
          f"{ent_off:#x})\n  {weapon_label(real)}  ->  {weapon_label(dst_id)}")
    print("  the donor weapon is gone; the target arrives unupgraded unless the "
          "id you passed already encodes a level")
    commit(args.file, buf, [args.slot], args.yes, args.ignore_running_game)


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
    p.add_argument("--ignore-running-game", action="store_true",
                   help="write even when the game looks like it is running. The game "
                        "overwrites the save from memory on its next autosave, so the "
                        "edit will almost certainly be lost")
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

    sp = sub.add_parser("set-hp", help="set hp/max_hp/base_max_hp (may be "
                                       "recalculated from Vigor on load)")
    sp.add_argument("--slot", type=int, default=0)
    sp.add_argument("value", type=lambda x: int(x, 0))
    sp.set_defaults(func=cmd_set_hp)

    sp = sub.add_parser("set-stats", help="respec: set stats directly (level auto = sum-79)")
    sp.add_argument("--slot", type=int, default=0)
    sp.add_argument("--wretch", action="store_true", help="reset all 8 stats to 10 (level 1)")
    for _name in STAT_NAMES:
        sp.add_argument(f"--{_name}", type=int, help=f"{_name} (1-99)")
    sp.set_defaults(func=cmd_set_stats)

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
    sp.add_argument("--key", action="store_true", help="add into the key-items array (medallions, maps, cookbooks, crystal tears...)")
    sp.add_argument("--qty", type=int, required=True)
    sp.set_defaults(func=cmd_add_item)

    sp = sub.add_parser("replace-weapon",
                        help="retarget a weapon you own to a different one "
                             "(adding a new weapon is impossible - see the docstring)")
    sp.add_argument("--slot", type=int, default=0)
    sp.add_argument("--source", required=True,
                    help="weapon you currently hold and are willing to lose "
                         "(name or param id)")
    sp.add_argument("--target", required=True,
                    help="weapon to turn it into (name or param id)")
    sp.add_argument("--index", type=int,
                    help="record index from list-items, when --source is ambiguous")
    sp.set_defaults(func=cmd_replace_weapon)

    sp = sub.add_parser("list-armor", help="list armor pieces you own")
    sp.add_argument("--slot", type=int, default=0)
    sp.set_defaults(func=cmd_list_armor)

    sp = sub.add_parser("replace-armor",
                        help="retarget a piece of armor you own to a different one")
    sp.add_argument("--slot", type=int, default=0)
    sp.add_argument("--source", required=True,
                    help="armor you currently hold and are willing to lose "
                         "(name or protector param id)")
    sp.add_argument("--target", required=True,
                    help="armor to turn it into (name or protector param id)")
    sp.add_argument("--index", type=int,
                    help="0-based pick when you own several copies of --source")
    sp.set_defaults(func=cmd_replace_armor)

    sp = sub.add_parser("add-aow", help="add an Ash of War (writes a gaitem map entry too)")
    sp.add_argument("--slot", type=int, default=0)
    sp.add_argument("--gem-id", type=lambda x: int(x, 0), help="EquipParamGem id (e.g. 30500)")
    sp.add_argument("--name", help="Ash of War name, prefix optional (e.g. 'Golden Parry')")
    sp.set_defaults(func=cmd_add_aow)

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
