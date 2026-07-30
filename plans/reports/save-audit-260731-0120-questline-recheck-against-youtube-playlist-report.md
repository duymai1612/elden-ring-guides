# Soát 24 questline trong playlist đối chiếu save - bản đính chính

Ngày: 2026-07-31 | Save: `ER0000.sl2` slot 1 (`dyu`, Lv 713)
**Thay thế phần "Trạng thái questline" của** `save-audit-260730-2350-questline-status-post-haligtree-report.md`
(bản đó có 3 kết luận sai, ghi rõ ở mục cuối).

Playlist: "Elden Ring - Full Questline ( Nhiệm vụ của các NPC trong game )" - kênh **VỢ Cho Chơi Game**
https://www.youtube.com/playlist?list=PLWsanzojPwHfLQi0-O2qeDMCiy8hx9TOj
24 video = **23 questline riêng biệt** (Seluvis xuất hiện 2 lần: video #4 và #21).
Kết quả: **10 xong / 12 chưa xong / 1 không kết luận được**.

> **Cập nhật 2026-07-31 02:08** - đọc lại save: **Fia đã XONG 100%**. Xem mục
> "Cập nhật Fia" ở cuối file. Bảng dưới đã sửa theo.

## Phương pháp (đã sửa)

Bản trước sai vì dùng **item giữa chừng, missable** làm bằng chứng cho cả questline.
Lần này mỗi questline được kiểm bằng **phần thưởng CUỐI** hoặc item chỉ có khi
đã qua bước cuối, tra bằng danh sách tên chính xác (không grep mò), trên hợp nhất
3 nguồn: 641 common item + 109 key item + 224 vũ khí/giáp đã resolve qua gaitem map.

Cạm bẫy đã tính đến: item **bị tiêu khi đưa NPC** (vắng mặt = có thể đã dùng),
item **missable giữa quest** (vắng mặt ≠ chưa xong), item **theo nhánh chọn**
(vắng mặt = chọn nhánh khác), và **số lượng đã bị chỉnh** (Deathroot 90, Ancient
Dragon Smithing Stone 94 → không dùng qty làm bằng chứng).

---

## ✅ Đã xong (9/23)

| # | Questline | Bằng chứng quyết định |
|---|---|---|
| 1 | **Varré** | `Pureblood Knight's Medal` + `Varre's Bouquet` (vũ khí chỉ rơi khi giết Varré sau khi xong) + `Map: Mohgwyn Palace` |
| 2 | **Ranni / Blaidd** | Dark Moon Greatsword +10, `Miniature Ranni`, `Iji's Bell Bearing`, Iji's Mirrorhelm, Blaidd's set, Royal Greatsword +10, Astel Naturalborn **dead** |
| 3 | **Millicent** | `Rotten Winged Sword Insignia`, `Unalloyed Gold Needle` (đã lấy lại từ xác), `Gowry's Bell Bearing`, `Flock's Canvas Talisman`, War Surgeon set |
| 4+21 | **Seluvis** | `Magic Scorpion Charm` - đây là phần thưởng CUỐI, phải qua: đưa potion → mua 2 puppet → lấy Amber Starlight → Amber Draught → mời Ranni. Kèm Finger Maiden Therolina Puppet (puppet mua của Seluvis) + Preceptor's set (Seluvis đã chết theo quest Ranni) |
| 5 | **Yura** | `Nagakiba +25` **và** `Eleonora's Poleblade +10` (rơi từ Eleonora ở Second Church of Marika = bước cuối) |
| 6 | **Nepheli / Kenneth / Gostoc** | Anh xác nhận đã xong. Save khớp: Grafted Scion (Chapel of Anticipation) **dead** = đã quay lại lấy Stormhawk King; Stormhawk King **không còn trong túi** = đã đưa; **không có** Nepheli Loux Puppet = đã đưa potion cho Gideon (nhánh giữ được quest Nepheli) |
| 7 | **Irina / Edgar** | `Banished Knight's Halberd +8` = drop của **Edgar the Revenger** ở Revenger's Shack, đây là bước CUỐI. Kèm Grafted Blade Greatsword, 4x Sacrificial Twig, Shabriri Grape |
| 8 | **Gurranq** | Đủ **8/9** phần thưởng theo đúng thứ tự cố định: Clawmark Seal (1), Bestial Sling (2), Bestial Vitality (3), Beast's Roar (4), Beast Claw (5), Stone of Gurranq (6), Beastclaw Greathammer (7), **Gurranq's Beast Claw (8)**. Chỉ còn Deathroot thứ 9 → Ancient Dragon Smithing Stone |
| 9 | **Latenna** | `Latenna the Albinauric` ashes + cả 2 nửa medallion. Bước cuối ở Apostate Derelict **không xác định được từ save** |
| 10 | (Millicent, xem #3) | Còn 1 bước: giết Malenia → `Miquella's Needle` |

---

## ❌ Chưa xong (13/23)

| # | Questline | Signal thiếu | Ghi chú |
|---|---|---|---|
| 23 | **Rogier** | Rogier's Rapier, Spellblade set, Rogier's Bell Bearing, Black Knifeprint | 0/4 nhưng **Rogier ĐÃ CHẾT** - đồ đang nằm chờ nhặt ở Roundtable Hold, xem mục cuối |
| 8 | **Sellen & Jerren** | Sellian Sealbreaker, Sellen's Primal Glintstone, Witch's Glintstone Crown, Stars of Ruin, Eccentric set, Sellen's Bell Bearing | **0/6 - gần như chưa động tới** |
| 9 | **Alexander** | Shard of Alexander, Alexander's Innards | 0/2 |
| 10 | **Dung Eater** | Sword of Milos, Mending Rune of the Fell Curse | Đang giữ đủ **5x Seedbed Curse** chưa nộp. Potion đã đưa Gideon nên quest còn nguyên |
| 11 | **Corhyn & Goldmask** | Mending Rune of Perfect Order, Law of Regression, Corhyn's Bell Bearing, Iron Kasa | 0/4 |
| 16 | **Hyetta** | Frenzied Flame Seal | Còn giữ 2x Shabriri Grape + 1x Fingerprint Grape **chưa đưa** → mới ở giai đoạn đầu/giữa, không phải sắp xong như bản trước viết |
| 17 | **Volcano Manor / Rykard / Tanith** | Serpentbone Blade, Hoslow's Petal Whip, Blasphemous Blade, Taker's Cameo | Mới **1/3 hợp đồng** (Magma Whip Candlestick + Scaled set = xong Old Knight Istvan). Rykard **alive** |
| 20 | **Rya (Zorayas)** | Serpent's Amnion, Daedicar's Woe | 0/2 |
| 18 | **Patches** | Patches' Bell Bearing, Dancer's Castanets | Đã qua Murkwater Cave (cờ boss dead) nhưng chưa tới bước Volcano Manor |
| 22 | **Bernahl** | Devourer's Scepter, Beast Champion set, Bernahl's Bell Bearing | Bước cuối ở Crumbling Farum Azula - chưa tới (Godskin Duo / Placidusax / Maliketh đều alive) |
| 24 | **Diallos** | Diallos's Mask | Bước cuối ở Jarburg |
| 15 | **Thops** | Thops's Barrier, Thops's Bell Bearing | Đang giữ 1 `Academy Glintstone Key` dư - đúng thứ Thops cần |

## ⚠️ Không kết luận được từ save

- **Boc** (video #12): không có item nào chỉ tồn tại sau bước cuối. `Tailoring Tools`
  và `Gold Sewing Needle` đang giữ là đồ nhặt ở Haligtree, không phải bằng chứng Boc.
- **Latenna** bước cuối ở Apostate Derelict (xem trên).

---

## 3 lỗi trong bản trước - đính chính

| Bản trước viết | Thực tế | Nguyên nhân sai |
|---|---|---|
| Nepheli 🟡 chưa xong | ✅ xong | Dùng `Arsenal Charm` làm bằng chứng. Đó là item Nepheli đưa ở Roundtable **ngay sau Godrick**, missable riêng nếu reload area sớm, và quest vẫn chạy tiếp bình thường. Phần thưởng cuối thật là Ancient Dragon Smithing Stone |
| Gurranq 🟡 chưa xong | ✅ 8/9 | Chỉ tra `Beast Eye` (item ĐẦU quest, giữ suốt) mà không tra 8 phần thưởng thật. Đủ cả 8 |
| Hyetta "có 3 grape rồi, sắp xong" | mới đầu/giữa | Giữ grape = **chưa đưa**, không phải sắp xong |

Ngoài ra bản trước bỏ sót **Irina/Edgar** (đã xong) và không soát **Rogier, Patches,
Diallos, Thops, Boc, Rya, Bernahl** vì lúc đó chưa có danh sách playlist.

---

## Quest path cập nhật (2026-07-31)

**Bước 0 - làm ngay, 2 phút:** Roundtable Hold, ban công chỗ Rogier → nhặt
Bell Bearing + Spellblade set + Rapier +8 + Letter. Xong luôn questline Rogier.

**Nhóm A - deadline = giết Rykard** (giết Rykard là khoá vĩnh viễn hợp đồng ám sát):
1. Volcano Manor: nhận nốt 2 hợp đồng còn lại - Rileigh the Idle (→ `Serpentbone Blade`
   + Crepus's Vial) và Juno Hoslow (→ `Hoslow's Petal Whip` + Hoslow set)
2. **Rya** - trong Volcano Manor, → `Serpent's Amnion` + `Daedicar's Woe`
3. **Patches** - bước Volcano Manor, → `Dancer's Castanets`
4. **Bernahl** - nhận hợp đồng của anh ta ở Volcano Manor trước (bước cuối mới ở Farum Azula)
5. Giết Rykard → `Blasphemous Blade` + `Rykard's Great Rune`

**Nhóm B - deadline = giết Maliketh** (Leyndell → Ashen Capital):
6. **Dung Eater** - đã đủ 5 `Seedbed Curse`, chỉ cần nộp → `Mending Rune of the Fell Curse`
7. **Corhyn & Goldmask** - đẩy tới Leyndell Colosseum → `Mending Rune of Perfect Order`

**Nhóm C - không deadline, làm lúc nào cũng được:**
8. **Sellen** (0/6, gần như chưa động) - Sellia Hideaway → Master Lusat → `Stars of Ruin`
9. **Alexander** - Seethewater (Mt. Gelmir) → gần Fire Giant → Farum Azula → `Shard of Alexander`
10. **Thops** - đưa `Academy Glintstone Key` dư đang có → `Thops's Barrier` + Bell Bearing
11. **Diallos** - Volcano Manor → Jarburg → `Diallos's Mask`
12. **Boc** - không kết luận được từ save, tự kiểm trong game
13. **Gurranq** - còn Deathroot thứ 9 → `Ancient Dragon Smithing Stone`

**Nhóm D - cuối cùng, đúng thứ tự này:**
14. **Malenia** → `Miquella's Needle` (dùng `Unalloyed Gold Needle` đang giữ)
15. **Hyetta** - chỉ làm SAU bước 14. Đưa 2x Shabriri Grape + 1x Fingerprint Grape đang
    giữ → Church of Inhibition → Frenzied Flame → `Frenzied Flame Seal`
16. **Mohg, Lord of Blood** → mở khoá DLC Shadow of the Erdtree
17. Fire Giant → đốt Erdtree → Maliketh → Bernahl (Farum Azula) → Godfrey → Elden Beast

### Ending đang có sẵn để chọn ở cuối
- **Age of the Stars** (Ranni - xong)
- **Age of the Duskborn** (Mending Rune of the Death-Prince - **vừa mở**)
- Age of Order (cần Corhyn/Goldmask), Blessing of Despair (cần Dung Eater),
  Lord of Frenzied Flame (cần Hyetta)

---

## Cập nhật Fia (đọc save lúc 2026-07-31 02:08)

**Fia XONG 100%.** Save đổi từ 68 → 71 boss dead. Bằng chứng đầy đủ cả 2 nhánh:

| Bằng chứng | Ý nghĩa |
|---|---|
| `Cursemark of Death` **biến mất** | đã đưa cho Fia |
| `Mending Rune of the Death-Prince` **mới có** | phần thưởng CUỐI → ending **Age of the Duskborn** đã mở |
| **Fia's Champions** dead + **Lichdragon Fortissax** dead | đã vào Deathbed Dream |
| `Remembrance of the Lichdragon` | drop của Fortissax |
| `Fia's Hood` + `Fia's Robe` + `Deathbed Dress` | đồ của Fia sau khi cô ấy chết |
| `Twinned Helm/Armor/Gauntlets/Greaves` + `Inseparable Sword` | nhánh D / em trai D đã xong |
| `D's Bell Bearing` | nhận trong chuỗi Fia |
| `[Sorcery] Fia's Mist` | Fia dạy |

### Phát hiện kèm theo: đồ của Rogier đang nằm chờ nhặt

Rogier chết khi quest Ranni tiến triển (đã xong từ lâu), và **Rogier là một trong
Fia's Champions vừa bị hạ** - tức chắc chắn đã chết. Xác anh ta để lại ở đúng chỗ
cũ trên ban công Roundtable Hold:

- `Rogier's Bell Bearing`
- `Spellblade's` set (Hood/Traveling Attire/Gloves/Trousers)
- `Rogier's Rapier +8` - vẫn lấy được vì save chưa có món này
- `Rogier's Letter`

**Deadline: trước khi vào Crumbling Farum Azula** (Roundtable Hold đóng vĩnh viễn).
Đây là toàn bộ phần thưởng của questline Rogier - không cần làm thêm bước nào,
chỉ cần đi nhặt.

Ghi chú: `Black Knifeprint` không có và Black Knife Catacombs còn nguyên (2 boss
alive) → đã đi nhánh ngắn (nói chuyện với Ranni trước). Nhánh này vẫn cho đủ đồ,
chỉ mất phần lore.

### Quan sát chưa lý giải

**Omenkiller (Village of the Albinaurics)** cũng vừa bị hạ trong cùng phiên. Đó là
một bước GIỮA của questline Nepheli. Nếu Nepheli đã xong từ trước thì bước này thừa
- có thể anh chỉ dọn map, hoặc quest Nepheli mới đang làm bây giờ. Save không phân
biệt được.

## Câu hỏi chưa giải quyết

- Chưa RE được flag NPC quest → Boc và bước cuối của Latenna vẫn không xác định được.
  Muốn chắc phải map thêm flag ID NPC (nguồn: `ClayAmore/ER-Save-Lib`).
- Nepheli: kết luận dựa vào lời anh + bằng chứng gián tiếp, không có item nào chứng minh trực tiếp.
- `Erdsteel Dagger` (Kenneth đưa lúc đầu) không còn trong túi - có thể đã bán/vứt, không phải dấu hiệu quest hỏng.
