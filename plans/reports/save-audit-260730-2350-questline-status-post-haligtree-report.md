# Elden Ring - Questline nào đã xong / còn dở (đọc từ save)

Ngày: 2026-07-30 23:52 | Save: `ER0000.sl2` slot 1 (`dyu`, Lv 713)
Nối tiếp `save-audit-260729-0045-pre-mountaintops-progress-and-missables-report.md`
(bản đó viết khi Morgott còn sống; giờ đã qua Haligtree).

## Cách đo & độ tin cậy

| Nguồn | Lệnh | Tin được? |
|---|---|---|
| Event flag boss (157 boss) | `elden_ring_grace_unlock.py boss-report` | **Cao**. Tool chỉ có `respawn-boss` (xoá cờ), không có "kill-boss" → cờ `dead` là chơi ra thật. Auto-detect base `0x37e9c`, progress oracle 23/23 |
| Vũ khí / giáp (224 món) | script resolve gaitem map + `elden_ring_items_full_reference.json` | **Rất cao**. Tool không add được weapon/armor |
| Key items (109 món) | script đọc mảng `key_off` (lệnh `list-items` KHÔNG hiện mảng này) | Cao |
| Talisman / goods (641 món) | `list-items` | Cao cho "có/không", chỉ 1/641 món không tra được tên (`Goods #166`) |
| Grace flags | - | **KHÔNG dùng**. Đã bị unlock hàng loạt 130 grace bằng tool |
| Số lượng (qty) | - | **KHÔNG**. Deathroot 90, Stonesword Key 98, Somber Ancient Dragon 68 = đã chỉnh |

**Giới hạn quan trọng:** save này chưa có bảng flag cho từng bước NPC quest
(mới RE được flag boss/grace/map/cookbook/whetblade/summoning-pool). Nên mọi
kết luận dưới đây là **suy luận từ vật phẩm + cờ boss**, không phải đọc thẳng
trạng thái NPC. Chỗ nào không đủ bằng chứng thì ghi rõ.

68/157 boss đã hạ.

---

## ✅ Đã xong

| Questline | Bằng chứng |
|---|---|
| **Millicent** | `Unalloyed Gold Needle` (đã lấy LẠI từ xác), `Rotten Winged Sword Insignia`, `Prosthesis-Wearer Heirloom`, War Surgeon set (đồ của Millicent), `Gowry's Bell Bearing` + `Flock's Canvas Talisman` (đã giết Gowry sau khi xong). Commander O'Neil + Godskin Apostle (Dominula) + Loretta (Haligtree) đều dead |
| **Ranni / Blaidd / Iji / Seluvis** | Dark Moon Greatsword +10, Bastard's Stars +10, Royal Greatsword +10 + Blaidd's set, `Miniature Ranni`, `Iji's Bell Bearing`, Magic Scorpion Charm, Astel Naturalborn dead |
| **Varré** | `Pureblood Knight's Medal` + `Map: Mohgwyn Palace` (đã teleport sang Mohgwyn) |
| **Yura** | Nagakiba +25 **và** Eleonora's Poleblade +10 (rơi từ Eleonora ở Second Church of Marika = bước cuối) |
| **Latenna** (ít nhất phần thưởng chính) | `Latenna the Albinauric` ashes + cả 2 nửa `Haligtree Secret Medallion` |

### Millicent còn đúng 1 bước
`Unalloyed Gold Needle` đang nằm trong túi. Giết **Malenia** (đang alive) rồi
tương tác bông Scarlet Aeonia → `Miquella's Needle` + Somber Ancient Dragon
Smithing Stone. Không có deadline.

---

## 🟡 Còn dở - xếp theo deadline

### 1. Dung Eater — CÓ ĐỦ ĐỒ RỒI, chỉ chưa nộp
Đang giữ đúng **5x `Seedbed Curse`**. Không có `Mending Rune of the Fell Curse`,
không có Sword of Milos → chưa nộp cho Dung Eater.
**Deadline: trước khi giết Maliketh** (Leyndell → Ashen Capital).

### 2. Volcano Manor / Tanith / Bernahl / Rya
Có `Drawing-Room Key`, Magma Whip Candlestick (= xong hợp đồng Old Knight Istvan),
Serpent Bow. **Rykard còn sống.**
Chưa có: `Serpent's Amnion` (Rya), Hoslow's Petal Whip (hợp đồng Juno Hoslow),
Blasphemous Blade, Devourer's Scepter (Bernahl).
**Deadline: giết Rykard = khoá toàn bộ hợp đồng ám sát còn lại.**

### 3. Nepheli Loux / Kenneth Haight / Gostoc
Không có `Arsenal Charm`, không có `Stormhawk King` ashes.
Morgott đã chết → bước cuối (cả 3 vào throne room Stormveil) **làm được ngay bây giờ**.
**Deadline: đốt Erdtree.**

### 4. Corhyn / Goldmask
Không có `Mending Rune of Perfect Order`, không có incantation Golden Order cỡ lớn.
**Deadline: Ashen Capital.**

### 5. Fia
Đã bắt đầu (Clinging Bone, Prince of Death's Pustule, `Cursemark of Death` còn nguyên
chưa dùng). Fia's Champions + Lichdragon Fortissax đều alive.
→ Đưa Cursemark cho Fia ở Deeproot Depths → Fia's Champions → Deathbed Dream →
Fortissax → `Mending Rune of the Death-Prince`. Không có deadline gấp.

### 6. Hyetta ⚠️ ĐỪNG LÀM VỘI
Có `Fingerprint Grape` + 2x `Shabriri Grape`, chưa có `Frenzied Flame Seal`.
Bước cuối = nhận Frenzied Flame → **khoá mọi ending khác**, kể cả Age of the Stars
đã mở khoá sẵn. Chỉ gỡ được bằng Miquella's Needle.
→ Làm sau khi đã giết Malenia và cầm Miquella's Needle trong tay.

### 7. Sellen
Không có `Sellian Sealbreaker`, `Sellen's Primal Glintstone`, Stars of Ruin,
Witch's Glintstone Crown → gần như chưa động tới. Vào Sellia Hideaway (tường ảo
sau bia mộ ở nghĩa địa trên Church of the Plague - ngay chỗ vừa làm quest Millicent).

### 8. Alexander
Không có `Shard of Alexander`. Alexander xuất hiện: Seethewater (Mt. Gelmir) →
gần Fire Giant → Crumbling Farum Azula.

### 9. Gurranq
`Beast Eye` còn trong túi, Deathroot 90 (số lượng đã chỉnh). Cho ăn là xong ngay.

### Không đủ dữ liệu để kết luận
Diallos, Boc, Jar Bairn, Blackguard Big Boggart, Thops, Roderika, Irina/Edgar,
Rogier, D + anh em D. Save không lưu trạng thái NPC ở dạng đọc được với bộ flag hiện có.

---

## Đồ bỏ sót đáng nhặt (vùng đã mở)

| Món | Bằng chứng thiếu | Ở đâu |
|---|---|---|
| **Mimic Tear Ashes** | boss Mimic Tear (Nokron) **dead** nhưng không có ashes | Rương ở Night's Sacred Ground, Nokron |
| **Black Knife Tiche** | Alecto, Black Knife Ringleader **alive** | Ringleader's Evergaol, Moonlight Altar |
| **Marais Executioner's Sword** | Elemer of the Briar **alive** | The Shaded Castle (chỗ vừa lấy Valkyrie's Prosthesis) |
| **Ronin's Set** | không có trong giáp | Shabriri ở Zamor Ruins, Mountaintops |
| **Glintstone Whetblade** | có Iron/Black/Red-Hot/Sanctified, thiếu cái này | Raya Lucaria Academy |

---

## Trạng thái điểm không quay lại

| Mốc | Trạng thái |
|---|---|
| Morgott | ✅ đã qua (không mất gì) |
| **Fire Giant / đốt Erdtree** | ⛔ **chưa** - Fire Giant còn alive. Tốt |
| **Maliketh** | ⛔ chưa - Malekith alive |
| Three Fingers | chưa nhận (chưa có Frenzied Flame Seal) |
| Mohg, Lord of Blood | alive → **DLC Shadow of the Erdtree chưa vào được** (đã cài sẵn) |

Thứ tự an toàn: Dung Eater + Nepheli + Corhyn + Volcano Manor → Malenia (lấy
Miquella's Needle) → Hyetta/Frenzied Flame nếu muốn → Fire Giant → Maliketh.

## Câu hỏi chưa giải quyết

- Chưa RE được flag cho bước NPC quest → không xác nhận được Latenna đã kết thúc ở
  Apostate Derelict chưa, và các quest nhỏ (Boc, Diallos, Jar Bairn...) đang ở bước nào.
  Muốn chắc thì phải map thêm flag ID của NPC quest (nguồn: `ClayAmore/ER-Save-Lib`).
- `Lord of Blood's Favor` vẫn còn trong key items dù đã có `Pureblood Knight's Medal` -
  chưa rõ item này có bị tiêu khi trả cho Varré hay không.
- Seedbed Curse 0 → 5 và 2 whetblade mới xuất hiện so với audit hôm qua: chưa phân biệt
  được là chơi ra hay thêm bằng `add-item --key`.
