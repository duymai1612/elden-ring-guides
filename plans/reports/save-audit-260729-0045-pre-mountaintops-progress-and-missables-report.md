# Elden Ring - Audit save & checklist trước khi mở Mountaintops of the Giants

Ngày: 2026-07-29 | Save: `ER0000.sl2` slot 1 (`dyu`, Lv 675) | Đọc trực tiếp từ binary

---

## 1. Trạng thái đã VERIFY từ save (ground truth)

Đọc bằng `elden_ring_save_editor.py` + parser bổ sung cho mảng **key items** và
gaitem map biến-độ-dài (mảng key items không hiện trong `list-items`).

### Nhân vật
| | |
|---|---|
| Tên / Level | `dyu` / **675** |
| Stats | VIG/MIND/END/STR/DEX/INT/FAI **99** mỗi cái, ARC 61 |
| Runes memory | 675.093.875 |
| Flask | Crimson +12 (10 charge) / Cerulean +12 (4 charge) - **đã max** |
| Memory Stone | 8/8 (max) |
| Talisman Pouch | 3/3 (max, 4 slot) |

### Vùng đã mở (theo map fragment đang giữ)
Limgrave W+E, Weeping Peninsula, Liurnia E/N/W, Caelid, Dragonbarrow,
Altus Plateau, Mt. Gelmir, Leyndell Royal Capital, Siofra River, Ainsel River,
Lake of Rot, Deeproot Depths.

**Chưa có:** Mountaintops of the Giants, Consecrated Snowfield, Mohgwyn Palace.

### Great Runes
| Có | Chưa có |
|---|---|
| Godrick's Great Rune | Morgott's |
| Radahn's Great Rune | Rykard's |
| Great Rune of the Unborn (Rennala) | Mohg's, Malenia's |

### Bằng chứng chốt: **Morgott chưa chết**
- Không có `Morgott's Great Rune` (id 8150)
- Không có `Remembrance of the Omen King`
- Không có `Rold Medallion` (id 8107) -> Grand Lift of Rold chưa mở

### Key items đáng chú ý đang giữ
Dectus Medallion (Left+Right), Rusty Key, Academy Scroll, Academy Glintstone Key,
Discarded Palace Key, **Miniature Ranni**, **Cursemark of Death**, **Beast Eye**,
Shabriri Grape x2, Celestial Dew x3, Larval Tear x6, Imbued Sword Key,
Iron Whetblade, Black Whetblade, Whetstone Knife, Crafting Kit, Tailoring Tools,
Lost Ashes of War x2.
Bell bearing: Smithing-Stone Miner's [2], Glovewort Picker's [1], Abandoned Merchant's.

### Key items KHÔNG có (đọc ra tiến độ)
`Rold Medallion`, `Haligtree Secret Medallion (L/R)`, `Pureblood Knight's Medal`,
`Unalloyed Gold Needle`, mọi `Mending Rune`, `Red-Hot Whetblade`,
`Sanctified Whetblade`, `Drawing-Room Key`, `Serpent's Amnion`, `Seedbed Curse`.

### Suy ra từ vũ khí (tool KHÔNG add được weapon -> vũ khí là 100% chơi ra)
- **Dark Moon Greatsword +10** + `Miniature Ranni` + `Seluvis's Bell Bearing` đã nộp
  + `Fingerslayer Blade`/`Dark Moon Ring` đã tiêu -> **questline Ranni ĐÃ XONG**
- **Royal Greatsword** (đồ của Blaidd) -> Blaidd đã chết
- **Bastard's Stars** + **Ash of War: Waves of Darkness** (cả 2 phần thưởng của
  Remembrance of the Naturalborn) -> Astel đã chết + đã nhân bản remembrance ở Walking Mausoleum
- **Bolt of Gransax +10** -> đã lấy trước khi đốt Erdtree (tốt)
- **Remembrance of the Grafted** đang giữ **chưa tiêu** (vừa nhân bản 2 ngày trước)

### Spirit Ashes đang có (chỉ 8)
Banished Knight Oleg +10, Banished Knight Engvall +10, Lhutel the Headless +10,
Spirit Jellyfish +10, Skeletal Militiaman, Skeletal Bandit, Demi-Human,
Finger Maiden Therolina Puppet.

**Thiếu hẳn:** `Mimic Tear Ashes` (Nokron - vùng ĐÃ mở), `Black Knife Tiche`,
`Latenna`, `Redmane Knight Ogha`, `Ancient Dragon Knight Kristoff`.

### Talisman: 34/117 dòng (chưa tính biến thể +1/+2/+3)
83 dòng chưa có (danh sách đầy đủ ở phần 4; đã lọc riêng đồ DLC).

### Hoạt động gần nhất (diff save 07-27 -> 07-29)
Mới nhặt: `Volcano Manor Invitation`, `Note: Below the Capital`,
`Remembrance of the Grafted` (bản nhân đôi), `[Sorcery] Tibia's Summons`,
`[Sorcery] Rancorcall`, `[Incantation] Flame Grant Me Strength`, `Order Healing`,
`Skeletal Bandit Ashes`. Key item tăng 70 -> 87 trong 2 ngày.
-> Đang ở Leyndell, vừa nhận thư mời Volcano Manor.

### DLC
`Game/sd/sd_dlc02.bdt` tồn tại -> **Shadow of the Erdtree đã cài**.
Điều kiện vào DLC: hạ **Radahn** (xong) **+ Mohg, Lord of Blood** (chưa) rồi chạm
cánh tay khô ở Cocoon of the Empyrean trong Mohgwyn Palace.

---

## 2. Độ tin cậy của dữ liệu

| Loại dữ liệu | Tin được? | Lý do |
|---|---|---|
| Key items (có/không) | Cao | `add-item --key` có tồn tại nhưng lịch sử backup cho thấy key item tăng dần đều theo ngày chơi (20 -> 87), không có burst injection |
| Vũ khí / Spirit Ashes | **Rất cao** | Tool chưa implement `add-weapon` (plan còn `pending`, CLI không có lệnh này) |
| Great Runes, map fragment | **Rất cao** | Cùng lý do trên, và khớp với tiến độ |
| Số lượng vật phẩm (qty) | **Không** | Đã bị sửa hàng loạt lên 99/999 (smithing stone, golden rune, mat crafting, Stonesword Key, Golden Seed) |
| Level / stats | Không | 675 với 99 mọi stat = đã chỉnh |
| Event flags (boss đã giết, NPC ở đâu) | Không đọc được | Save editor không parse event flag; suy luận gián tiếp qua key item + vũ khí |

---

## 3. Trả lời câu hỏi chính: giết Morgott để mở Mountaintops - OK chưa?

### Kết luận: **Giết Morgott KHÔNG phải điểm không quay lại.** An toàn.

Morgott drop: `Remembrance of the Omen King` + `Morgott's Great Rune`
(+ `Talisman Pouch` nếu chưa giết Margit - anh đã có đủ 3 pouch nên đã lấy rồi).
Sau đó Melina xuất hiện, đưa `Rold Medallion` -> mở Grand Lift of Rold.
Không NPC nào chết/biến mất chỉ vì Morgott chết.
Nguồn: https://eldenring.wiki.gg/wiki/Morgott,_the_Omen_King

### Điểm không quay lại THẬT SỰ nằm ở đâu?

| Mốc | Mất gì |
|---|---|
| Giết Morgott | **Không mất gì** |
| Dùng Grand Lift of Rold lên Mountaintops | **Không mất gì** (chỉ mở vùng mới) |
| **Đốt Erdtree (Fire Giant -> Forge of the Giants)** | Bắt đầu chuỗi khoá |
| **Giết Maliketh (Crumbling Farum Azula)** | **Leyndell -> Ashen Capital. Đây mới là điểm chết.** |
| Chạm Three Fingers (Frenzied Flame Proscription, dưới Leyndell) | Khoá TẤT CẢ ending khác, chỉ gỡ được bằng Miquella's Needle |

Khi Leyndell thành Ashen Capital: mất `Sanctified Whetblade` (Fortified Manor),
mất Corhyn/Goldmask nếu chưa đẩy quest đến Leyndell Colosseum, mất Dung Eater,
mất Nepheli, và nhiều loot chỉ có ở Royal Capital.
Nguồn: https://eldenring.fandom.com/wiki/Sanctified_Whetblade ,
https://primewikis.com/guides/before-burning-erdtree-in-elden-ring/

---

## 4. Việc NÊN làm trước - xếp theo mức "mất vĩnh viễn"

### 4.1. MISSABLE THẬT - phải lấy khi còn ở Leyndell Royal Capital

| Việc | Vị trí | Mất khi nào |
|---|---|---|
| **Sanctified Whetblade** (chưa có) | Fortified Manor, Leyndell, tầng 2, cạnh cái đe. Leo giàn gỗ bên hông vào | Sau Maliketh (Ashen Capital) |
| **Coded Sword** (chưa có) | Fortified Manor, Leyndell, phòng ngai trên cùng - **cùng toà nhà với Sanctified Whetblade** | Sau Maliketh |
| **2x Seedbed Curse** (đang có 0) | East Capital Rampart (tầng cao nhất) + West Capital Rampart / trong Fortified Manor | Sau Maliketh. Không đủ 5 cái thì hỏng ending Dung Eater |
| **Haligtree Secret Medallion (Right)** -> **Latenna** | Village of the Albinaurics, Liurnia -> đưa cho Latenna ở Slumbering Wolf's Shack | ⚠️ Nếu nhặt nửa **Left** (Castle Sol, Mountaintops) TRƯỚC khi gặp Latenna thì **Latenna chết**, chỉ nhặt được ashes, hỏng quest. Đây là missable thật gắn với Mountaintops |
| **Corhyn + Goldmask** | Corhyn rời Roundtable -> Altus -> cả 2 đứng trước Leyndell Colosseum. Phải đẩy hết chuỗi ở Royal Capital | Sau Maliketh |
| **Dung Eater** (5x Seedbed Curse) | Subterranean Shunning-Grounds + Leyndell + Nokron + Caelid | Sau Maliketh |
| **Nepheli Loux** | Stormveil throne room (cần Gostoc/Kenneth) | Sau Maliketh |

> Lưu ý về mốc chính xác: **đốt Erdtree** (Forge of the Giants) chỉ châm lửa cây;
> Leyndell vẫn ở dạng Royal Capital. Capital chỉ đổi thành **Ashen Capital sau khi
> giết Maliketh, the Black Blade**. Đa số guide viết "trước khi đốt Erdtree" cho an
> toàn, nhưng deadline thật là Maliketh.
> Nguồn: https://eldenring.fandom.com/wiki/Leyndell,_Ashen_Capital

> ⚠️ Three Fingers - **rủi ro chỉ bắt đầu SAU khi giết Morgott**, không phải bây giờ.
> Đường xuống Frenzied Flame Proscription bị Morgott's Grace chặn, chỉ mở sau khi
> hạ Morgott ở Elden Throne. Cửa cuối còn phải cởi sạch giáp mới qua được nên
> không thể vô tình bước vào. Nhưng sau Morgott thì nhớ: chạm Three Fingers =
> khoá mọi ending khác (kể cả Age of the Stars anh đã mở khoá), chỉ gỡ được bằng
> Miquella's Needle ở đấu trường Placidusax. Quest Hyetta kết thúc đúng chỗ đó.
> Anh đang giữ 2 Shabriri Grape.
> Nguồn: https://eldenring.fandom.com/wiki/Frenzied_Flame_Proscription

### 4.2. Đồ mạnh cho build INT/Moon của anh - toàn bộ nằm ở vùng ĐÃ MỞ

Anh 99 INT nhưng chỉ có **21 sorcery**. Thiếu gần hết cỡ lớn:

| Món | Vị trí | Ghi chú |
|---|---|---|
| **Comet Azur** | Primeval Sorcerer Azur, vách đá đông nam Hermit Village, Mt. Gelmir | Sorcery mạnh nhất game |
| **Azur's Glintstone Staff** | Raya Lucaria, phòng phía trên grace Church of the Cuckoo | Cặp với Comet Azur |
| **Lusat's Glintstone Staff** | Rương phía bắc phòng boss Nox Swordstress & Nox Priest, Sellia Town of Sorcery, Caelid | Staff sát thương cao nhất |
| **Stars of Ruin** | Master Lusat, Sellia Hideaway (cần `Sellian Sealbreaker` - chưa có) | Qua quest Sellen |
| **Radagon Icon** | Rương tầng 2 gần grace Debate Parlor, Raya Lucaria | Giảm cast time - bắt buộc cho caster |
| **Graven-School Talisman** | Raya Lucaria, từ Debate Parlor đi tây, rẽ phải trước cầu thang | +sorcery damage |
| **Moon of Nokstella** | Rương dưới ngai lớn, phòng cao nhất Nokstella | **+2 memory slot** |
| Adula's Moonblade, Carian Slicer/Greatsword/Piercer, Comet, Glintstone Cometshard, Cannon/Gavel of Haima, Meteorite of Astel, Ancient Death Rancor | Liurnia / Caria Manor / Sellen / Nokron | Tất cả đều ở vùng đã mở |

Nguồn: fextralife + game8 + eldenring.fandom (đã verify từng món)

### 4.3. Spirit Ash - anh chỉ có 8 con, thiếu 2 con top

| Món | Vị trí | Ghi chú |
|---|---|---|
| **Mimic Tear Ashes** | Rương ở Night's Sacred Ground, Nokron | Anh đã vào Nokron rồi (Fingerslayer Blade lấy ở đó) mà bỏ sót |
| **Black Knife Tiche** | Ringleader's Evergaol, Moonlight Altar (giết Alecto) | Moonlight Altar anh đã mở |

### 4.4. Whetblade còn thiếu
- `Red-Hot Whetblade` - Redmane Castle, Caelid (Chamber Outside the Plaza)
- `Sanctified Whetblade` - Leyndell (xem 4.1, **missable**)

### 4.5. Không cần bận tâm
Golden Seed / Sacred Tear: flask đã max +12 / 14 charge -> bỏ qua.
Larval Tear: có 6, chỉ dùng để respec.
Level 675 + 99 mọi stat -> không boss nào còn là mối đe doạ về damage.
Vấn đề duy nhất là **nội dung bị bỏ sót**, không phải độ khó.

---

## 5. Trạng thái questline (suy từ save)

| Questline | Trạng thái | Bằng chứng | Còn phải làm |
|---|---|---|---|
| **Ranni + Blaidd + Seluvis** | ✅ XONG | Dark Moon Greatsword +10, Miniature Ranni, Royal Greatsword (đồ Blaidd), Seluvis's Bell Bearing đã nộp, Fingerslayer Blade + Dark Moon Ring đã tiêu | Không. Ending Age of the Stars đã sẵn, chọn ở cuối game |
| **Fia** | 🟡 ĐANG DỞ | Giữ `Cursemark of Death` chưa dùng, có map Deeproot Depths + Prince of Death's Pustule, KHÔNG có Mending Rune of the Death-Prince | Đưa Cursemark cho Fia ở Deeproot Depths -> fast travel -> vào Deathbed Dream -> giết **Lichdragon Fortissax** |
| **Gurranq / Beast Clergyman** | 🟡 ĐANG DỞ | Giữ `Beast Eye` | Tiếp tục cho ăn Deathroot |
| **Hyetta** | 🟡 ĐANG DỞ | Giữ 2x Shabriri Grape | Cần grape thứ 3 (từ Edgar) + Fingerprint Grape (Vyke, Church of Inhibition). ⚠️ Kết thúc = nhận Frenzied Flame |
| **Volcano Manor / Rykard** | 🔵 VỪA BẮT ĐẦU | Có `Volcano Manor Invitation` (nhặt 2 ngày trước), không có Drawing-Room Key | Làm hết hợp đồng ám sát + quest Rya **TRƯỚC** khi giết Rykard. Giết Rykard = toàn bộ NPC Volcano Manor biến mất |
| **Sellen** | ❌ CHƯA | Không có `Sellian Sealbreaker` | Cần cho Stars of Ruin (Lusat) + Comet Azur (Azur) |
| **Millicent / Gowry** | ❌ CHƯA | Không có `Unalloyed Gold Needle` | Cần nếu muốn Miquella's Needle (gỡ Frenzied Flame) |
| **Varre** | ❌ CHƯA | Không có `Pureblood Knight's Medal` | Rose Church, Liurnia. Đây là đường TẮT vào Mohgwyn Palace |
| **Dung Eater / Corhyn+Goldmask / Nepheli** | ❌ CHƯA | Không có Seedbed Curse, không có Mending Rune nào | **Phải làm trước khi đốt Erdtree** |

---

## 6. DLC Shadow of the Erdtree

DLC **đã cài** (`Game/sd/sd_dlc02.bdt`). Điều kiện vào:
hạ **Radahn** (✅ xong) + **Mohg, Lord of Blood** (❌ chưa), rồi chạm cánh tay khô
ở cocoon tại grace `Cocoon of the Empyrean` trong đấu trường Mohg.
Có thể vào DLC **trước khi đốt Erdtree**.
Nguồn: https://gamerant.com/elden-ring-how-start-the-shadow-of-the-erdtree-dlc/

Vào Mohgwyn Palace có 2 đường:
1. **Pureblood Knight's Medal** từ Varre (Rose Church, Liurnia) - **làm được NGAY**
2. Cổng dịch chuyển ở Consecrated Snowfield - cần 2 nửa Haligtree Secret Medallion
   (sau Mountaintops)

-> Nếu muốn chơi DLC sớm, làm quest Varre trước.

---


## 7. Thứ tự đề xuất từ vị trí hiện tại

1. **Leyndell Royal Capital (đang ở)** - lấy `Sanctified Whetblade` ở Fortified Manor.
   Đẩy Corhyn + Goldmask tới Leyndell Colosseum. Gom Seedbed Curse cho Dung Eater.
   Xuống Subterranean Shunning-Grounds nhưng **KHÔNG chạm Three Fingers**.
2. **Quay lại Raya Lucaria** - Radagon Icon, Graven-School Talisman, Azur's Glintstone Staff.
3. **Nokron / Nokstella** - Mimic Tear Ashes (Night's Sacred Ground), Moon of Nokstella.
4. **Moonlight Altar** - Black Knife Tiche (Ringleader's Evergaol).
5. **Caelid** - Lusat's Glintstone Staff (Sellia Town of Sorcery), Red-Hot Whetblade
   (Redmane Castle), quest Sellen -> Sellian Sealbreaker -> Stars of Ruin.
6. **Mt. Gelmir** - Comet Azur (Primeval Sorcerer Azur).
7. **Volcano Manor** - quest Rya (Serpent's Amnion ở Temple of Eiglay, sau Godskin Noble)
   **TRƯỚC**, rồi mới làm hết hợp đồng ám sát, cuối cùng giết Rykard.
   Giết Rykard = toàn bộ NPC Volcano Manor rời đi.
   Nguồn: https://steamcommunity.com/app/1245620/discussions/0/597413188027545492/
8. **Deeproot Depths** - đưa Cursemark of Death cho Fia -> Lichdragon Fortissax.
9. **Rose Church** - quest Varre -> Pureblood Knight's Medal -> Mohgwyn Palace
   -> Mohg -> mở DLC.
10. **Morgott** -> Rold Medallion -> Mountaintops. An toàn.
11. Fire Giant -> **đốt Erdtree** (chỉ làm khi đã xong hết mục 1-9).

---

## 8. Prompt cho Perplexity (deep research)

```
I'm playing Elden Ring (base game + Shadow of the Erdtree installed, patch 1.16+).
My exact save state, read directly from the .sl2 binary:

PROGRESS: In Leyndell Royal Capital, have NOT fought Morgott. No Rold Medallion.
GREAT RUNES HELD: Godrick's, Radahn's, Great Rune of the Unborn (Rennala).
GREAT RUNES MISSING: Morgott's, Rykard's, Mohg's, Malenia's.
MAPS HELD: Limgrave W+E, Weeping Peninsula, Liurnia E/N/W, Caelid, Dragonbarrow,
Altus Plateau, Mt. Gelmir, Leyndell, Siofra River, Ainsel River, Lake of Rot,
Deeproot Depths. MAPS MISSING: Mountaintops, Consecrated Snowfield, Mohgwyn Palace.
QUESTLINES: Ranni COMPLETE (have Dark Moon Greatsword, Miniature Ranni, Royal
Greatsword from Blaidd, Seluvis's Bell Bearing turned in). Astel dead. Fia: holding
an unused Cursemark of Death, no Mending Rune of the Death-Prince. Volcano Manor:
just got the invitation, nothing else. NOT started: Varre (no Pureblood Knight's
Medal), Sellen (no Sellian Sealbreaker), Millicent/Gowry (no Unalloyed Gold Needle),
Dung Eater (no Seedbed Curse), Corhyn/Goldmask, Nepheli.
BUILD: level 675, all stats 99 (arcane 61), INT moon build - Dark Moon Greatsword
+10, Moonveil +10, Carian Regal Scepter +10, Staff of Loss +25, Meteorite Staff.
Only 21 sorceries; missing Comet Azur, Stars of Ruin, Adula's Moonblade, Carian
Slicer/Greatsword/Piercer, Loretta's Mastery, Meteorite of Astel, Cannon of Haima.
Missing talismans include Radagon Icon, Graven-School, Moon of Nokstella, Erdtree's
Favor, Marika's Soreseal, Gold Scarab, Shard of Alexander, Great-Jar's Arsenal,
Bull-Goat's, Longtail Cat, Godskin Swaddling Cloth, Winged Sword Insignia.
Missing spirit ashes: Mimic Tear, Black Knife Tiche, Latenna.
Flasks maxed (+12, 14 charges). 8/8 Memory Stones. 3/3 Talisman Pouches.

QUESTIONS - answer each with a source URL, and flag where guides disagree:
1. Give me an exact ordered checklist of everything I should do BEFORE defeating
   Morgott and BEFORE taking the Grand Lift of Rold, ranked by how permanently
   lost it is. Distinguish clearly between what is lost at (a) Morgott's death,
   (b) entering the Mountaintops, (c) burning the Erdtree, (d) defeating Maliketh
   / Leyndell becoming the Ashen Capital.
2. For each NPC questline I have NOT started or have half-finished, tell me its
   exact hard deadline and whether it is already broken given my state above.
3. Which items in Leyndell Royal Capital become unobtainable once it turns into
   the Ashen Capital? Full list.
4. Best order to slot in Volcano Manor/Rykard, Varre -> Mohgwyn -> Mohg, and the
   Shadow of the Erdtree DLC relative to Morgott and burning the Erdtree.
5. For a 99 INT moon/spellblade build, which sorceries, staves and talismans in
   my ALREADY-OPEN regions give the biggest power jump? Rank top 15 with exact
   locations.
6. Any ending I have already locked myself out of, or any single action from here
   that would irreversibly lock an ending?
```

---

## 9. Series YouTube anh gửi

**Playlist:** "Elden Ring: Things You Missed" - kênh **Doms Roundtable** - tiếng Anh - **65 video**.
https://www.youtube.com/playlist?list=PLuCGvRgru-FN8MiDMJ4dLtAAmrFGezGyf

Đúng thứ anh cần: đây là series **checklist đồ bị bỏ sót theo từng vùng**, không phải
walkthrough tuyến tính, không phải lore, không phải build guide.
(10 video cuối là supercut ghép lại các tập cũ, không có vùng mới.)

### Thứ tự playlist tự nó xác nhận lộ trình

Toàn bộ vùng phụ + vùng ngầm (Nokron, Nokstella, Deeproot Depths, Ainsel River,
Shaded Castle, Subterranean Shunning-Grounds, Lake of Rot, Volcano Manor) đều nằm
**trước tập 38 (Mountaintops Part 1)** và trước tập 53 (Leyndell Capital of Ash).
Tập 37 "The Lake of Rot" - tập cuối của cụm ngầm, ngay sát tập Mountaintops đầu
tiên - có hẳn chapter tên **"What to do next" ở 17:20**, đúng ngưỡng chuyển sang
Mountaintops.

### Tập nên xem NGAY theo tình trạng save

| Tập | Nội dung | Vì sao hợp lúc này |
|---|---|---|
| 12 | Leyndell, Royal Capital - `f_DxICIS0Xc` | Có chapter "DO NOT MISS THIS ITEM!!! MISSABLE LEGENDARY WEAPON!!!" + "...leaving the Capital". Anh đang ở đây |
| 34, 35 | Subterranean Shunning-Grounds - `zVcO7JArYgI`, `_fdEG6IjLIc` | Anh vừa nhặt `Note: Below the Capital` |
| 5 | Raya Lucaria Academy - `MxmXmqeYuZM` | Radagon Icon, Graven-School, Azur's Staff đều ở đây |
| 26, 31 | Nokron `byIEeqoIkvQ`, Nokstella `Y1tklR67fO4` | Mimic Tear Ashes, Moon of Nokstella |
| 54 | The Moonlight Altar - `bCA9tG4Sy7U` | Black Knife Tiche |
| 14-17, 32, 33 | Caelid | Lusat's Staff, Red-Hot Whetblade, quest Sellen |
| 21, 22 | Mt Gelmir - `k_lCDslCEnQ`, `Xt-XaUvlGJE` | Comet Azur (Azur) |
| 23, 24, 29, 36 | Volcano Manor (4 tập, tập 36 là FINALE) | Anh vừa nhận invitation |
| 30 | The Deeproot Depths - `I11O62jZ9tM` | Bước Fia + Fortissax |
| 37 | The Lake of Rot - `653BXIVa1x8` | Chapter "What to do next" ngay trước Mountaintops |

Link tập: `https://www.youtube.com/watch?v=<videoId>`

### Giới hạn của phần này
Không lấy được transcript/caption (YouTube timedtext trả 200 + 0 byte, cần yt-dlp
mà máy chưa cài). Nên **không có câu chữ trực tiếp** series nói gì về mốc Morgott.
Kết luận ở trên rút từ **thứ tự playlist + tên chapter**, không phải từ lời thoại.

---

## 10. Kiểm chứng chéo: những claim của agent research bị LOẠI

Chạy 5 agent research song song. Chất lượng không đồng đều - dưới đây là các claim
bị bác sau khi tự verify. Ghi lại để lần sau không tin lại.

| Claim của agent | Thực tế | Nguồn bác |
|---|---|---|
| "Morgott drop Royal Greatsword" | Royal Greatsword là vũ khí của **Blaidd**. Morgott drop Remembrance of the Omen King + Morgott's Great Rune | https://eldenring.wiki.gg/wiki/Morgott,_the_Omen_King |
| "Fia cần 2x Cursed Burial Urn" | Fia cần **Cursemark of Death**, rồi Deathbed Dream -> Lichdragon Fortissax -> Mending Rune of the Death-Prince | https://www.gamesradar.com/elden-ring-fia-quest-questline-walkthrough-deathbed-companion-age-of-duskborn-ending/ |
| "Master Lusat ở Crystal Tunnel, Altus Plateau" | Master Lusat ở **Sellia Hideaway, Caelid**, cần `Sellian Sealbreaker` | https://exputer.com/guides/master-lusat-location-elden-ring/ |
| "Latenna hard-blocked vì chưa có Haligtree Secret Medallion" | Latenna lấy được **ngay bây giờ**: nửa **Right** ở Village of the Albinaurics (Liurnia). Nguy hiểm ngược lại: nhặt nửa Left ở Castle Sol trước khi gặp Latenna thì cô ta chết | https://eldenring.fandom.com/wiki/Latenna_the_Albinauric |
| "Millicent/Gowry hard-blocked vì chưa có Haligtree medallion" | Quest bắt đầu ở **Gowry's Shack, đông Caelid** -> giết Commander O'Neil -> Unalloyed Gold Needle. Toàn bộ ở vùng đã mở | https://www.rpgsite.net/feature/12501-elden-ring-millicent-questline-walkthrough-millicents-location-the-unalloyed-gold-needle-and-miquellas-needle |
| "Maliketh mở đường vào Frenzied Flame Proscription" | **Morgott** mới là cửa. Đường bị Morgott's Grace chặn | https://eldenring.fandom.com/wiki/Frenzied_Flame_Proscription |
| "Great-Jar's Arsenal ở Dee Siofra Well" | Là phần thưởng thắng 3 đấu sĩ của Great Jar, bắc Caelid | (chưa verify sâu - **coi là chưa xác nhận**) |
| "Comet Azur là incantation" | Là **sorcery** | https://eldenring.wiki.fextralife.com/Comet+Azur |
| "Celestial Dew dùng để gỡ Frenzied Flame" | Celestial Dew là để xin absolution ở Church of Vows. Gỡ Frenzied Flame chỉ có Miquella's Needle | https://eldenring.wiki.fextralife.com/Three+Fingers |

### Claim của agent chưa verify -> chỉ coi là gợi ý, cần tự kiểm trong game
- Brother Corhyn chết ngay khi đốt Erdtree (nhiều guide nói vậy, chưa tự đọc source gốc)
- Boc / Roderika / D / Jar Bairn ra sao sau Ashen Capital
- Phần thưởng cụ thể của từng hợp đồng ám sát Volcano Manor
- Vị trí chính xác của Winged Sword Insignia, Ritual Shield Talisman, Two Fingers Heirloom

---

## Câu hỏi chưa giải quyết

1. Không đọc được **event flag** từ save -> không biết chắc boss phụ / dungeon nào đã
   clear, NPC hiện đứng ở đâu. Toàn bộ suy luận dựa trên key item + vũ khí + spirit ash.
   Muốn chắc 100% phải dùng tool parse event flag (ví dụ ClayAmore/ER-Save-Editor) hoặc kiểm trong game.
2. Gurranq: đã cho ăn bao nhiêu Deathroot - không đọc được vì số lượng đã bị sửa.
   Kiểm bằng cách tới Bestial Sanctum xem còn nói chuyện được không.
3. Sellen đang ở stage nào - kiểm ở Waypoint Ruins.
4. Nepheli / Corhyn hiện đứng đâu - kiểm ở Roundtable Hold.
5. Không lấy được transcript series YouTube (thiếu yt-dlp) -> phần "series khuyên gì"
   suy từ thứ tự playlist + tên chapter, không phải lời thoại.
