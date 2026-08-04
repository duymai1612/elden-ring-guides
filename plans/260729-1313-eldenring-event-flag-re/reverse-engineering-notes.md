---
title: "Elden Ring event flag / Sites of Grace - reverse engineering"
status: done
created: 2026-07-29
---

# Mở khoá Sites of Grace bằng cách sửa save - tiến độ RE

## Kết luận ngắn
**Xong.** Khối event flag nằm ở `0x373a1` trong slot 1. Đã mở 130 grace, tổng
297/314. Công cụ: `elden_ring_grace_unlock.py`.

## Đã có (verify được)

### Thuật toán địa chỉ hoá flag
Nguồn: `ClayAmore/ER-Save-Lib`, `src/api/event_flags.rs`
(https://github.com/ClayAmore/ER-Save-Lib)

```
block = event_id / 1000
index = event_id % 1000
offset = BST[block] * 125          # BLOCK_SIZE = 125 byte mỗi block
byte   = event_flags[offset + index / 8]
bit    = 7 - (index % 8)           # MSB trước trong byte
```

### Kích thước khối
`src/save/user_data_x.rs`: `#[deku(bytes_read = "0x1BF99F")] event_flags: Vec<u8>`
-> **0x1BF99F byte (1.832.351)**, theo sau là 1 byte terminator = 0.
Khớp với vùng 1,9 MB toàn zero đo được ở `0x20000..0x1f0000`.

### Dữ liệu tra cứu (đã lưu cạnh file này)
- `eventflag-block-map.csv` - bảng BST `block,slot`, 11.919 dòng
- `grace-event-flag-ids.tsv` - **314 grace** kèm flag id + region,
  trích từ `ClayAmore/ER-Save-Editor` `src/db/graces.rs`

## Vì sao chưa ghi được

### 1. Lib gốc không parse được save này
`SaveApi::from_path()` trả lỗi:
`Failed to fetch regulation size from version: 738263176`

`ver_size_map()` của lib chỉ biết tới bản `11611000` (patch 1.16.1, commit cuối
2026-05-15). Version đọc ra không nằm trong bảng và cũng không đúng định dạng
`1xxxxxxx` - nghĩa là parser lệch từ trước đó, hoặc save mới hơn lib.
Chưa truy ra nguyên nhân gốc.

### 2. Tự định vị base offset -> không thoả oracle
Vì lib đi tới khối flag qua struct đã parse, nó không cho biết offset tuyệt đối.
Đã thử giải ngược base bằng ground truth của save này.

Oracle dùng: nhân vật đã clear Limgrave -> Leyndell, và **chưa từng** vào
Haligtree / Elphael / Mohgwyn / Consecrated Snowfield / Farum Azula. Slot 0
(Lv 9) gần như chưa thắp gì.

Kết quả tốt nhất, base `0x1a66d`:

| Khớp | Mâu thuẫn |
|---|---|
| Liurnia 52/52, Caelid 25/25, Limgrave 21/21 | **Stormveil 0/7** (đã giết Godrick) |
| Altus 19/19, Weeping 18/18, Leyndell 9/9 | **Academy 0/4** (đã giết Rennala) |
| Volcano Manor 8/8, Deeproot 6/6 | **Roundtable Hold 0/1** |
| Farum Azula 0/11, Elphael 0/5, Haligtree 0/4 | **Consecrated Snowfield 7/7** (chưa tới) |
| Mohgwyn 0/4, Ashen Capital 0/6, slot0 0/190 | Stranded Graveyard 0/2 |

251/314 đúng, nhưng cả false-negative lẫn false-positive đều theo cụm **nguyên
region** - dấu hiệu mô hình "một base phẳng" chưa đủ, không phải lệch vài byte.

Chạy lại với oracle chặt (chỉ lấy region không thể sai): **không base nào** đạt
đồng thời MUST_ON cao và MUST_OFF sạch. Tốt nhất 87/96 ON nhưng 12/37 OFF sai.

### Giả thuyết chưa kiểm chứng
- `eventflag_bst.txt` không khớp version save này
- Khối flag có cấu trúc thêm ngoài `base + BST[block]*125`
- Một số flag id trong `graces.rs` không phải cờ "đã thắp"

## Cách định vị base - neo theo struct, không brute-force

Brute-force base bằng "region nào phải sáng/tối" **thất bại**: base tìm được rơi
vào vùng bit dày, cho Liurnia 52/52 và Caelid 25/25 giả, đồng thời Stormveil 0/7
dù đã giết Godrick.

Cách đúng là neo vào chữ ký các field ngay trước khối flag trong `UserDataX`:

```
character_type i32 | in_online_session_flag u8 | character_type_online u32
| last_rested_grace u32 | not_alone_flag u8 | in_game_countdown_timer u32
| unk_gamedataman u32 | event_flags[0x1BF99F] | terminator u8 == 0
```

`character_type_online == 8` (0 chỉ dành cho bản ghi phantom/invader, không phải
slot nhân vật thật) + `not_alone_flag ∈ {0,1}` + terminator == 0, cộng với oracle
tiến độ hai chiều -> **đúng một nghiệm duy nhất**: anchor `0x37390`,
`event_flags = 0x37390 + 17 = 0x373a1`.

## Kiểm chứng tại base 0x373a1 (trước khi ghi)

| Phải sáng | | Phải tối | |
|---|---|---|---|
| Stormveil (đã giết Godrick) | 7/7 | Crumbling Farum Azula | 0/11 |
| Academy (đã giết Rennala) | 4/4 | Elphael / Haligtree | 0/5, 0/4 |
| Roundtable Hold | 1/1 | Mohgwyn Palace | 0/4 |
| Nokron (quest Ranni) | 6/6 | Consecrated Snowfield | 0/7 |
| Moonlight Altar / Lake of Rot | 3/3, 2/2 | Leyndell Ashen Capital | 0/6 |
| Stranded Graveyard | 2/2 | Volcano Manor (mới nhận thư) | 0/8 |

Mountaintops 1/10 - khớp, vừa lên tới. Tổng ban đầu 167/314.

## Kết quả ghi

130 grace được thắp, bỏ 17 grace thuộc `LeyndellAshenCapital` +
`CrumblingFarumAzula` (trạng thái thế giới sau điểm không quay lại). Tổng 297/314.

Kiểm tra sau khi ghi:
- **48 byte** thay đổi trên tổng 2.621.440
- toàn bộ nằm trong khối event flag
- **chỉ set bit, không xoá bit nào**
- inventory / gaitem map / stats / checksum: không đụng tới
- slot 0: nguyên vẹn byte-for-byte

## Bẫy đã gặp khi viết guard

Nới oracle để `report` chạy được trên save đã sửa -> guard chọn nhầm base
`0x13419`, báo Roundtable Hold chưa thắp. Bài học: **không được dùng chính thứ
script vừa sửa để làm tiêu chí xác thực.** Guard giữ chặt và từ chối, ai cần chạy
lại trên save đã unlock thì truyền `--base` (vẫn phải qua kiểm tra cấu trúc).

## Chưa verify
Chưa mở game. Chỉ mới chứng minh save hợp lệ về cấu trúc và checksum.

---

# Bổ sung DLC Shadow of the Erdtree (2026-08-04)

## Kết luận ngắn
**Xong.** 105 grace DLC + 5 mảnh bản đồ DLC, lấy thẳng từ `regulation.bin` của
máy này (bản `DLC02`) chứ không từ thư viện ngoài. Tổng sau khi ghi: 402/419.

## Vì sao phải tự trích
`ClayAmore/ER-Save-Editor` (nguồn của bảng 314 grace base game) **không có DLC** -
`src/db/regions.rs` không có một region Realm of Shadow nào. Không tìm được editor
nào khác có. Nên nguồn duy nhất đáng tin là param của chính game.

## Đường đi
`regulation.bin` -> AES -> DCX(zstd) -> BND4 -> `BonfireWarpParam.param`.
Dùng lại `elden_ring_regulation.py`; phần đọc PARAM và paramdef viết thêm
(scratchpad, ~40 dòng: PARAM 64-bit = 24 byte/row entry, row size suy từ khoảng
cách giữa hai data offset liền nhau).

Offset field lấy từ `soulsmods/Paramdex` `ER/Defs/BonfireWarpParam.xml`. Bẫy:
paramdef đầu file là `u8 disableParam_NT:1` + `dummy8 ...:7` - **hai bitfield
chung một byte**. Nếu parser tách chúng thành 2 byte thì mọi offset lệch 4 và
`eventflagId` bị đọc ở 8 thay vì 4. Bit packing quyết định bởi KÍCH THƯỚC ô nhớ,
không phải tên kiểu.

## Tự kiểm chứng (điểm mạnh của cách này)
Quét mọi offset u32 trong row, đếm xem giá trị nào trùng với 314 flag base game
đã biết: **offset 4 khớp đúng 314/422 row**, không offset nào khác khớp lấy một
row. Nghĩa là cùng một field, đọc trên row DLC, chắc chắn cũng là event flag.

Phân loại base/DLC bằng `areaNo` cho kết quả sạch tuyệt đối: area
10-19/30-39/60 = đúng 314 row base, area 20/21/22/25/28/40/41/42/43/61 = 105 row
DLC, không có row nào lẫn giữa hai nhóm.

## Bảng thu được
- `dlc-grace-event-flag-ids.tsv` - 105 grace, flag 72000-76960
  - m20 Belurat + Enir-Ilim 10, m21 Shadow Keep 14, m22 Stone Coffin Fissure 5,
    m25 Finger Birthing Grounds 1, m28 Midra's Manse 4, m40-m43 hầm/ngục/lò/hang
    12, **m61 Realm of Shadow 59**
- 5 dòng thêm vào `map-reveal-flag-ids.tsv`: `WorldMapPieceParam` row 1000-1004 ->
  flag 62080-62084. Thứ tự row khớp thứ tự item `Map:` (2008600-2008604), kiểm
  bằng base game: row 0 -> 62010 -> "Map: Limgrave, West".
- Base game còn thiếu **62053 Consecrated Snowfield** (row 14), đã bổ sung.

Tên grace lấy từ `PlaceName_dlc02.fmg` trong `mod/msg/engus/item_dlc02.msgbnd.dcx`
(bản Việt hoá, DCX nén DFLT nên zlib đọc được). `item.msgbnd.dcx` và
`item_dlc01.msgbnd.dcx` nén KRAK/Oodle - không đọc được trên macOS, nhưng không
cần vì tên base game đã có sẵn.

## Không đụng tới
`62065` (row 105, một vùng ngầm không rõ) và `62002`/`62000` (đã set sẵn) - không
xác định được ý nghĩa nên để nguyên.
