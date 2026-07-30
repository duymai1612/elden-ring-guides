---
title: "Elden Ring save editor: add-weapon capability"
description: "Add weapons/shields/staves/seals to inventory (gaitem_map + GaItemData registration + slot re-serialization)"
status: done-alternative
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
| 1 | [Verify format](./phase-01-verify-format.md) | Done - gate 1 pass, gate 2 FAIL |
| 2 | [Implement add-weapon](./phase-02-implement-add-weapon.md) | Bo - bat kha thi, thay bang `replace-weapon` |
| 3 | [Test and apply](./phase-03-test-and-apply.md) | Done - Coded Sword da vao save |

## Key risks

- gaitem_map re-serialize + tail-shift wrong → corrupt everything after the map. Gate: roundtrip (re-serialize unchanged map == original bytes, byte-for-byte).
- Handle generation wrong → invalid weapon / game crash. Gate: derive empirically from existing 0x8xxxxxxx handles AND match ClayAmore formula.
- GaItemData mislocated → corruption. Gate: structure scan + refuse if not uniquely found.
- somber (+10) vs standard (+25) max-upgrade unknown per weapon → invalid item_id. Gate: default to +0 (always valid) unless max is confirmed; user upgrades in-game (has all stones).
- Cannot run the game to confirm → rely on structural + roundtrip verification + exact algorithm match. Accept residual risk; backup always.

## Dependencies

None. Single-file tool change + tested batch against the user's save (slot 1).


## Kết cục thực tế (2026-07-29)

`add-weapon` **không làm được** trên save đã chơi: thêm entry mới vào gaitem map
tốn thêm 13 byte, phải đẩy đuôi slot, mà slot 1 còn **0 byte padding** (đo được).
Chi tiết ở phase 1.

Thay bằng lệnh **`replace-weapon`** đã implement trong `elden_ring_save_editor.py`:
ghi đè `item_id` của một entry **vốn đã là weapon** -> entry vẫn 21 byte, không
dịch chuyển gì. Handle, record inventory, mọi counter giữ nguyên. Đổi lại: mất
món weapon dùng làm "donor".

```
python3 elden_ring_save_editor.py -f <save> replace-weapon \
    --slot 1 --source "Marred Wooden Shield" --target "Coded Sword"
```

Kèm theo, sửa một bug thật trong `iter_gaitem_entries`: nó duyệt map bằng bước cố
định 8 byte, desync ngay từ entry weapon đầu tiên. Hệ quả: `find_free_gaitem()` có
thể trả về offset nằm GIỮA phần đuôi 13 byte của một weapon -> `add-aow` ghi đè
lệch. Giờ duyệt đúng độ dài biến thiên (rỗng 8 / weapon 21 / armor 16).

### Gate đã chạy
- roundtrip map byte-for-byte: PASS (43291 byte, 5120 entry, `parsed_end == pgd`)
- `selftest` checksum: PASS
- regression `add-aow` sau khi sửa walker: PASS
- test trên 2 bản copy trước khi động vào save thật

### CHƯA verify
Chưa mở game kiểm tra. Câu hỏi mở: registry `GaItemData` ("distinct acquired
items") có cần upsert `item_id` mới không - chưa xác định được struct đó nằm đâu
trong slot. Nếu game hiển thị sai hoặc crash khi mở túi thì restore backup.
