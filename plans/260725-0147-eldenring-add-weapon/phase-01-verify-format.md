---
phase: 1
title: "Verify format"
status: pending
priority: P1
effort: "1-2h"
dependencies: []
---

# Phase 1: Verify format

## Overview
Prove we can round-trip the gaitem_map (parse -> serialize == original bytes) and locate GaItemData + the handle-generation inputs on the user's real save, BEFORE writing any mutation. This is the safety foundation; if any check fails, add-weapon is not attempted.

## Implementation Steps
1. **gaitem_map parser/serializer** (helpers in the tool): parse 0x1400 entries from slot-body 0x20 (record = handle u32 + item_id u32, then +13 if weapon nibble 0x0 & item_id!=0, +8 if armor nibble 0x1, else +0). Serializer emits the same bytes per entry.
2. **Roundtrip gate:** `serialize(parse(map_bytes)) == map_bytes` byte-for-byte on the real save. Also assert parse end offset == `find_pgd` offset (already validated once this session).
3. **Locate GaItemData:** scan the slot body AFTER the storage-box inventory for the struct `{distinct_count:i32 (0<=n<0x1b58), unk:i32, ga_items:[GaItem2;0x1b58]}` (GaItem2 = 16 bytes). Discriminator: distinct_count matches the number of non-zero GaItem2.id entries; the ids overlap the gaitem_map item_ids. Refuse if not uniquely found.
4. **Derive handle inputs** empirically from the real save and cross-check against the ClayAmore formula:
   - `next_gaitem_handle = max(h & 0xFFFF for map handles) + 1`
   - `part_gaitem_handle = (gaitem_map[0].handle >> 16) & 0xFF`
   - `next_armament_or_armor_index = argmax_index(h & 0xFFFF) + 1`; confirm that slot is currently empty (handle==0 & item_id==0).
   - Sanity: the generated handle's nibble/part/counter shape matches existing 0x8xxxxxxx weapon handles.
5. **Tail-padding check:** confirm the last >=13 bytes of the 0x280000 slot body are zero (room to absorb the +13 shift).

## Success Criteria
- [ ] Roundtrip serialize(parse(map)) == original map bytes, exact
- [ ] parse end == find_pgd offset
- [ ] GaItemData located uniquely; distinct_count consistent with non-zero ids
- [ ] Handle inputs derived; generated handle shape matches existing weapon handles
- [ ] >=13 trailing zero bytes confirmed in slot body

## Risk Assessment
If roundtrip or GaItemData scan fails, STOP - do not implement mutation. The whole feature depends on a lossless map serializer; a mismatch means unknown conditional fields and guarantees corruption.
