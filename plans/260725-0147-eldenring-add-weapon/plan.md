---
title: "Elden Ring save editor: add-weapon capability"
description: "Add weapons/shields/staves/seals to inventory (gaitem_map + GaItemData registration + slot re-serialization)"
status: pending
priority: P2
created: 2026-07-24
---

# Elden Ring save editor: add-weapon capability

## Overview

`elden_ring_save_editor.py` can add goods + talismans (deterministic handle, in-place). It CANNOT add weapons/shields/staves/seals. Weapons need: a sequential gaitem handle, a gaitem_map entry, an inventory record, and a GaItemData "acquired items" entry.

**Load-bearing difficulty:** the gaitem_map serializes VARIABLE-SIZE on disk (empty entry = 8 bytes, weapon = 21 bytes, armor = 16). Adding a weapon grows the map by 13 bytes, which shifts the ENTIRE slot tail (PlayerGameData onward) forward by 13 bytes, consuming trailing zero-padding. This is a whole-slot restructure, far riskier than the in-place goods add. Two prior bugs this session (sparse-array overwrite, false inventory match) were caught only by verification - the same discipline (roundtrip gate + copy-testing + integrity checks) is mandatory here.

Goal: implement `add-weapon`, then add 4 items to slot 1: Erdtree Seal (34070000), Jellyfish Shield (32120000), Buckler (30000000), Wing of Astel (7070000).

## Verified algorithm (from ClayAmore/ER-Save-Editor)

- `item_id = base_id + upgrade_level + affinity_id` (plain add: affinity 0).
- `gaitem_handle = 0x80000000 | (part_gaitem_handle << 16) | next_gaitem_handle` where
  - `next_gaitem_handle = max(h & 0xFFFF for all map handles) + 1`
  - `part_gaitem_handle = (gaitem_map[0].handle >> 16) & 0xFF`
- Insert `GaItem{gaitem_handle, item_id, unk2=-1, unk3=-1, aow_gaitem_handle=0xFFFFFFFF, unk5=0}` (weapon = 21 bytes) at `next_armament_or_armor_index` = (index of the entry holding the current max counter) + 1.
- Inventory record → first FREE held-common slot (reuse `_first_free`): `{gaitem_handle, quantity=1, inventory_index=next_acq}`; bump common_count, next_equip_index, next_acquisition.
- GaItemData upsert: if `item_id` not already in `ga_items[0..distinct_count]`, write `GaItem2{id=item_id, unk=0, reinforce_type=0, unk1=0}` (16 bytes) at `ga_items[distinct_count]`; bump `distinct_aquired_items_count`. Struct: `{distinct_count:i32, unk:i32, ga_items:[GaItem2;0x1b58]}`.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Verify format](./phase-01-verify-format.md) | Pending |
| 2 | [Implement add-weapon](./phase-02-implement-add-weapon.md) | Pending |
| 3 | [Test and apply](./phase-03-test-and-apply.md) | Pending |

## Key risks

- gaitem_map re-serialize + tail-shift wrong → corrupt everything after the map. Gate: roundtrip (re-serialize unchanged map == original bytes, byte-for-byte).
- Handle generation wrong → invalid weapon / game crash. Gate: derive empirically from existing 0x8xxxxxxx handles AND match ClayAmore formula.
- GaItemData mislocated → corruption. Gate: structure scan + refuse if not uniquely found.
- somber (+10) vs standard (+25) max-upgrade unknown per weapon → invalid item_id. Gate: default to +0 (always valid) unless max is confirmed; user upgrades in-game (has all stones).
- Cannot run the game to confirm → rely on structural + roundtrip verification + exact algorithm match. Accept residual risk; backup always.

## Dependencies

None. Single-file tool change + tested batch against the user's save (slot 1).
