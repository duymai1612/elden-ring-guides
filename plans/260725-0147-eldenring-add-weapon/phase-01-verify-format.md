---
phase: 1
title: "Verify format"
status: done-blocked
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


## Kết quả chạy gate (2026-07-29)

Chạy trên save thật `ER0000.sl2` slot 1 (`dyu`, Lv 675).

### GATE 1 - roundtrip: **PASS**
Model gaitem map đúng. Parse 5120 entry từ `0x20` tới `0xa93b`, re-serialize ra
43291 byte **khớp byte-for-byte** với bản gốc. `parsed_end == pgd` chính xác.

Kích thước entry xác nhận: rỗng 8 byte, weapon 21 byte (8 + 13), armor 16 byte (8 + 8).
Phân bố: 127 weapon, 85 armor, 35 khác, 4873 rỗng.

Handle: high-16 chỉ nhận 5 giá trị - `0x8080`/`0x8081` (weapon), `0x9080`/`0x9081`
(armor), `0xC080` (AoW). Counter tràn qua 16 bit (đã thấy `0x808107ac`), nên công
thức `0x80000000 | (part << 16) | next16` trong plan **không đủ tổng quát**.

### GATE 2 - tail headroom: **FAIL - chặn cứng**

Plan giả định phần đuôi slot có zero-padding để nuốt 13 byte tăng thêm. Sai:

| Slot | Byte non-zero cuối | Padding còn lại |
|---|---|---|
| 0 | `0x27fff3` | 12 byte |
| 1 (nhân vật chính) | `0x27ffff` | **0 byte** |

Slot dài cố định `0x280000`. Slot 1 có dữ liệu sống tới đúng byte cuối cùng.
Đẩy đuôi lên 13 byte = **đẩy 13 byte dữ liệu sống ra khỏi slot** = hỏng save.
Slot 0 có 12 byte, vẫn thiếu 1.

=> Không thể thêm entry mới vào gaitem map bằng cách grow. Phase 2 theo thiết kế
hiện tại **phải bỏ**.

### Hướng thay thế (chưa verify đủ, không được làm mù)

Save có **53 entry weapon "dangling"** - có trong gaitem map nhưng không có record
inventory nào (đồ đã bán/vứt: Wing of Astel, Golden Halberd, Starscourge Greatsword,
Bastard Sword, Round Shield...). Ghi đè `item_id` của một entry như vậy thì:
- entry vẫn là weapon -> vẫn 21 byte -> **kích thước không đổi, không phải shift đuôi**
- chỉ cần thêm 1 record vào mảng common (in-place, giống hệt add-item)

Còn phải verify trước khi làm:
1. `GaItemData` (registry "distinct acquired items", `{count:i32, unk:i32,
   ga_items[0x1b58] x 16B}`) nằm ở đâu trong slot, và có bắt buộc upsert không.
2. Vùng `~0x144ce-0x146d2` (giữa held inventory kết thúc ở `0x13ce4` và storage box
   ở `0x1cc34`) có chứa các handle dangling này. **Chưa xác định được đó là struct
   gì** - có thể là equip slot / quick slot. Ghi đè handle mà chưa biết chỗ này là
   gì thì rủi ro.
