---
phase: 2
title: "Implement add-weapon"
status: pending
priority: P1
effort: "2-3h"
dependencies: [1]
---

# Phase 2: Implement add-weapon

## Overview
Add an `add-weapon` code path + CLI subcommand to `elden_ring_save_editor.py`, reusing the audited safety pattern (in-memory edit, MD5 refresh, backup, reload+validate+integrity).

## Related Code Files
- Modify: `/Users/duymai/game/elden-ring/elden_ring_save_editor.py`

## Implementation Steps
1. **Helpers** (module-level): `parse_gaitem_map(slot)->list`, `serialize_gaitem_map(list)->bytes`, `find_gaitem_data(slot)->offset`, `gen_weapon_handle(map_entries)->handle`.
2. **`add_weapon(buf, slot, base_id, upgrade=0)`** - RED-TEAM CORRECTED order (reflow, no stale-offset splice; affinity dropped for v1):
   a. `item_id = base_id + upgrade`. Guard: `(item_id & 0xF0000000)==0` (weapon nibble); refuse projectile id ranges (arrows/bolts) - melee/shield/catalyst only.
   b. Parse gaitem_map on ORIGINAL body. Assert parse-end == `find_pgd(body)` (hard precondition). Roundtrip-assert serialize(parse)==map_bytes.
   c. Handle gen: `next_counter = max(h&0xFFFF over map)+1`; assert `next_counter <= 0xFFFF`. `part = (map[0].handle>>16)&0xFF`; assert `map[0].handle` high-nibble==0x8. `handle = 0x80000000 | (part<<16) | next_counter`. Assert handle not already present.
   d. Insert `GaItem{handle,item_id,unk2=-1,unk3=-1,aow=0xFFFFFFFF,unk5=0}` at the FIRST genuinely-empty map slot (handle==0 && item_id==0), NOT argmax+1. Re-serialize map (+13B).
   e. Build `new_body = body[:0x20] + new_map + body[map_end:]`; assert the final 13B dropped are all zero; truncate/assert `len(new_body)==0x280000`.
   f. On NEW body (re-scan, never reuse pre-shift offsets): `find_held_inventory` -> write inventory record at first-free held-common slot `{handle,1,next_acq}`; bump common_count, next_equip_index, next_acquisition. `find_gaitem_data` (fail-closed) -> if item_id absent, write `GaItem2{item_id,0,0,0}` at distinct_count; bump distinct_count.
   g. Write new_body into buf; refresh MD5.
3. **CLI:** `add-weapon --slot N --item-id ID [--upgrade L]`. NO `--affinity` in v1 (needs AoW/gem path, unimplemented). `--upgrade` default 0 (always valid); item_id=base+upgrade, reinforce_type stays 0 (matches reference).
4. **find_gaitem_data** fail-closed: unique match requires (a) distinct_count == nonzero-id count, (b) every non-zero GaItem2.id also a gaitem_map item_id, (c) plausible distance after storage inventory. Refuse (no write) otherwise.
5. Reuse `commit()` for backup+write+reload+`validate_slot`; MANDATORY post-write re-verify with auto-restore-on-mismatch: re-parse map (end==find_pgd), integrity (common/key count==nonzero), weapon handle present identically in map+inventory and item_id in GaItemData; restore backup if any check fails.

## Success Criteria
- [ ] Tool compiles; add-weapon path present with CLI
- [ ] On a synthetic/copy save: add a weapon -> map re-parses to find_pgd, inventory integrity holds, weapon present with matching handle in map+inventory+GaItemData
- [ ] No-op safety: if roundtrip/GaItemData/handle preconditions fail, it refuses (no write)

## Risk Assessment
Ordering of in-place edits vs the tail shift is the subtle part; a test that adds then reads back every field (handle in 3 places, counts, item_id) guards it. Keep default upgrade 0 to avoid somber/standard ambiguity in this phase.
