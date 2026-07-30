#!/usr/bin/env python3
"""Light Sites of Grace and reveal map regions in an Elden Ring PC save.

Neither is an inventory item. A grace is a single bit in the slot's event-flag
block, and so is a revealed map region - holding the Map Fragment item does NOT
draw the map, which is why adding fragments with `elden_ring_save_editor.py` has
no visible effect. Both live in the same flag block, addressed the same way.

Addressing scheme, from ClayAmore's ER-Save-Lib (src/api/event_flags.rs):

    block = event_id // 1000
    index = event_id  % 1000
    byte  = base + BST[block] * 125 + index // 8
    bit   = 7 - index % 8              (most significant bit first)

BST is the block -> slot table shipped with that library. What the library cannot
give is `base`, the absolute offset of the block, because it reaches the block
through a fully parsed struct and that struct is variable-size (the gaitem map
ahead of it grows with the character). So `base` is recovered per save from the
field signature that immediately precedes the block in UserDataX:

    character_type i32 | in_online_session_flag u8 | character_type_online u32
    | last_rested_grace u32 | not_alone_flag u8 | in_game_countdown_timer u32
    | unk_gamedataman u32 | event_flags[0x1BF99F]

Those field constraints alone match at thousands of offsets, so the anchor is
confirmed against the character's known progress as well: regions it has certainly
cleared must read lit, regions it has certainly never entered must read dark. On an
untouched save exactly one offset satisfies all of it. Once graces have been
unlocked the dark half stops being true, so auto-detection deliberately refuses
rather than guessing - pass --base to re-run on an already-unlocked save."""
import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import elden_ring_save_editor as E

FLAG_DIVISOR = 1000
BLOCK_SIZE = 125
EVENT_FLAG_BYTES = 0x1BF99F
# character_type_online .. event_flags: u32 + u32 + u8 + u32 + u32
ANCHOR_TO_FLAGS = 17
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "plans", "260729-1313-eldenring-event-flag-re")

# Regions whose graces only exist in a post-point-of-no-return world state.
# Lighting them early would let the player warp into a world the story has not
# reached yet, so they are opt-in.
ENDGAME_REGIONS = {"LeyndellAshenCapital", "CrumblingFarumAzula"}


def load_bst():
    bst = {}
    with open(os.path.join(DATA, "eventflag-block-map.csv")) as fh:
        for line in fh:
            key, _, val = line.strip().partition(",")
            if val:
                bst[int(key)] = int(val)
    return bst


def load_graces():
    out = []
    with open(os.path.join(DATA, "grace-event-flag-ids.tsv")) as fh:
        for line in fh:
            fid, region, name = line.rstrip("\n").split("\t")
            out.append((int(fid), region, name))
    return out


# category -> the flag table extracted from ER-Save-Editor's src/db/*.rs.
# Every one of these is a plain "<flag id>\t<display name>" TSV.
FLAG_TABLES = {
    "maps": "map-reveal-flag-ids.tsv",
    "whetblades": "whetblade-flag-ids.tsv",
    "cookbooks": "cookbook-flag-ids.tsv",
    "summoning-pools": "summoning-pool-flag-ids.tsv",
}


def load_table(category):
    out = []
    with open(os.path.join(DATA, FLAG_TABLES[category])) as fh:
        for line in fh:
            fid, name = line.rstrip("\n").split("\t")
            out.append((int(fid), name))
    return out


def load_maps():
    return load_table("maps")


def flag_addr(bst, event_id):
    block, index = divmod(event_id, FLAG_DIVISOR)
    if block not in bst:
        return None
    return bst[block] * BLOCK_SIZE + index // 8, 7 - index % 8


def read_flag(slot, base, addr):
    byte_off, bit = addr
    return slot[base + byte_off] >> bit & 1


def find_base(slot, bst, graces):
    """Every offset whose struct signature fits AND whose flags agree with a
    progress oracle. A correct save yields exactly one.

    The base is NOT stable for a given save file: the gaitem map ahead of it grows
    as the character picks things up, so every play session shifts it (observed:
    0x373a1 -> 0x37551 after one session). It has to be re-derived every run.

    The struct signature alone is far too weak - a couple of range checks match at
    thousands of offsets - so the grace oracle carries the weight. Demanding that
    EVERY must-be-lit grace reads lit is both strict enough to be unique and
    stable across this script's own writes, since unlocking only ever sets bits.
    The must-be-dark half is used only as a fallback tie-break, because it stops
    being true the moment we light the Haligtree; relying on it after an unlock
    picked a plausible-looking wrong offset in testing (0x13419, which reported
    Roundtable Hold as unlit)."""
    must_on = {"RoundtableHold", "StormveilCastle", "AcademyOfRayaLucaria",
               "StrandedGraveyard", "LeyndellRoyalCapital"}
    must_off = {"ConsecratedSnowfield", "CrumblingFarumAzula",
                "ElphaelBraceOfTheHaligtree", "MiquellasHaligtree",
                "MohgwynPalace", "LeyndellAshenCapital"}
    on = [a for a in (flag_addr(bst, f) for f, r, _ in graces if r in must_on) if a]
    off = [a for a in (flag_addr(bst, f) for f, r, _ in graces if r in must_off) if a]
    reach = max(o for o, _ in on + off)
    exact, partial = [], []
    for anchor in range(0x8000, len(slot) - EVENT_FLAG_BYTES - ANCHOR_TO_FLAGS - reach):
        if not anchor_fits(slot, anchor):
            continue
        base = anchor + ANCHOR_TO_FLAGS
        lit = sum(read_flag(slot, base, a) for a in on)
        if lit == len(on):
            exact.append((base, lit, len(on)))
        elif lit >= len(on) * 0.9 and not any(read_flag(slot, base, a) for a in off):
            partial.append((base, lit, len(on)))
    return exact if exact else partial


def anchor_fits(slot, anchor):
    """Structural test on the fields that sit just before the flag block. None of
    these bits are ever touched by this script, so unlike the grace oracle the
    test stays valid on a save that has already been unlocked.

    character_type_online is 0 only for phantom and invader records; a real
    character slot carries 8. Requiring 8 rather than "0 or 8" is what separates
    the true offset from the decoy at 0x13419, which reads 0 there."""
    base = anchor + ANCHOR_TO_FLAGS
    if base + EVENT_FLAG_BYTES >= len(slot):
        return False
    if struct.unpack_from("<I", slot, anchor)[0] != 8:
        return False
    if slot[anchor + 8] not in (0, 1):
        return False
    return slot[base + EVENT_FLAG_BYTES] == 0


def check_base(slot, bst, graces, base):
    """Sanity-check an offset supplied with --base: the must-be-lit half of the
    oracle still has to hold, since unlocking never clears a bit."""
    must_on = {"RoundtableHold", "StormveilCastle", "AcademyOfRayaLucaria",
               "StrandedGraveyard", "LeyndellRoyalCapital"}
    on = [a for a in (flag_addr(bst, f) for f, r, _ in graces if r in must_on) if a]
    if not anchor_fits(slot, base - ANCHOR_TO_FLAGS):
        raise SystemExit(
            f"--base {base:#x} does not sit behind a valid UserDataX anchor "
            "(character_type_online != 8, or the block terminator is missing).")
    lit = sum(read_flag(slot, base, a) for a in on)
    if lit < len(on) * 0.9:
        raise SystemExit(
            f"--base {base:#x} fails the progress check ({lit}/{len(on)} graces "
            "that must be lit read as dark). Refusing to write.")
    return base, lit, len(on)


def cmd_flags(args, buf, slot, base, bst, category):
    """Set every flag in one of the FLAG_TABLES categories that is not set yet."""
    slot_off = E.slot_data_off(args.slot)
    changed = []
    for fid, name in load_table(category):
        addr = flag_addr(bst, fid)
        if not addr or read_flag(slot, base, addr):
            continue
        byte_off, bit = addr
        buf[slot_off + base + byte_off] |= 1 << bit
        changed.append(name)
    if not changed:
        print(f"every {category} flag is already set; nothing to do.")
        return
    print(f"setting {len(changed)} {category} flags:")
    for name in changed:
        print(f"  {name}")
    E.commit(args.file, buf, [args.slot], args.yes)


def cmd_report(args, slot, base, bst, graces):
    print("map regions:")
    for fid, name in load_maps():
        addr = flag_addr(bst, fid)
        state = "revealed" if addr and read_flag(slot, base, addr) else "dark"
        print(f"  {state:<9} {name}")
    print()
    per = {}
    for fid, region, _name in graces:
        addr = flag_addr(bst, fid)
        if not addr:
            continue
        entry = per.setdefault(region, [0, 0])
        entry[1] += 1
        entry[0] += read_flag(slot, base, addr)
    print(f"{'region':<34} {'lit/total':>10}")
    for region in sorted(per, key=lambda k: -per[k][1]):
        lit, total = per[region]
        print(f"{region:<34} {lit:>5}/{total:<4}")
    print(f"{'TOTAL':<34} {sum(v[0] for v in per.values()):>5}/"
          f"{sum(v[1] for v in per.values())}")


def cmd_unlock(args, buf, slot, base, bst, graces):
    slot_off = E.slot_data_off(args.slot)
    changed = []
    for fid, region, name in graces:
        if region in ENDGAME_REGIONS and not args.include_endgame:
            continue
        addr = flag_addr(bst, fid)
        if not addr or read_flag(slot, base, addr):
            continue
        byte_off, bit = addr
        pos = slot_off + base + byte_off
        buf[pos] |= 1 << bit
        changed.append((region, name))
    if not changed:
        print("every grace in scope is already lit; nothing to do.")
        return
    print(f"lighting {len(changed)} graces:")
    for region, name in changed[:15]:
        print(f"  {region:<30} {name}")
    if len(changed) > 15:
        print(f"  ... and {len(changed) - 15} more")
    if not args.include_endgame:
        skipped = sum(1 for _, r, _ in graces if r in ENDGAME_REGIONS)
        print(f"skipped {skipped} graces in {', '.join(sorted(ENDGAME_REGIONS))} "
              "(pass --include-endgame to light those too)")
    E.commit(args.file, buf, [args.slot], args.yes)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("-f", "--file", required=True, help="path to ER0000.sl2")
    p.add_argument("--slot", type=int, default=0)
    p.add_argument("-y", "--yes", action="store_true")
    p.add_argument("--include-endgame", action="store_true",
                   help="also light Ashen Capital / Crumbling Farum Azula graces")
    p.add_argument("--base", type=lambda x: int(x, 0),
                   help="event-flag block offset, for a save already unlocked once "
                        "(auto-detection only works on an untouched save)")
    p.add_argument("cmd",
                   choices=["report", "unlock"] + [f"unlock-{c}" for c in FLAG_TABLES])
    args = p.parse_args()

    buf = E.load_save(args.file)
    E.require_valid_slot(buf, args.slot)
    slot = E.get_slot(buf, args.slot)
    bst, graces = load_bst(), load_graces()

    if args.base is not None:
        base, lit, total = check_base(slot, bst, graces, args.base)
    else:
        hits = find_base(slot, bst, graces)
        if len(hits) != 1:
            raise SystemExit(
                f"expected exactly one event-flag base, found {len(hits)}: "
                f"{[hex(h[0]) for h in hits]}. Refusing to touch the save. If this "
                "save was already unlocked once, re-run with --base <offset>.")
        base, lit, total = hits[0]
    print(f"event_flags @ {base:#x}  (progress oracle {lit}/{total})\n")

    if args.cmd == "report":
        cmd_report(args, slot, base, bst, graces)
    elif args.cmd.startswith("unlock-"):
        cmd_flags(args, buf, slot, base, bst, args.cmd[len("unlock-"):])
    else:
        cmd_unlock(args, buf, slot, base, bst, graces)


if __name__ == "__main__":
    main()
