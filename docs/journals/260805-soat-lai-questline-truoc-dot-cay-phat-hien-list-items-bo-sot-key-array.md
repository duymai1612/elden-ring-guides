# Soát lại questline trước khi đốt cây: phát hiện `list-items` bỏ sót mảng key item

**Ngày**: 2026-08-05
**Mục đích**: Xác nhận Fire Giant có bị stuck gì không, rồi soát toàn bộ questline trước
mốc đốt Erdtree (không quay lại được sau đó về mặt câu chuyện).
**Kết quả**: Không stuck gì. Fire Giant sẵn sàng đánh (đường đã mở, build dư). Soát lại
toàn bộ 24 questline "đã xong" trong doc thì đúng nguyên vẹn - chỉ có mục "đồ còn sót"
và Phần 6 của doc bị sai, đã sửa.

---

## Việc đã làm

1. Đọc save trực tiếp (`ER0000.sl2`, slot 1, không ghi - chỉ đọc). Xác nhận Mountaintops
   of the Giants grace 10/10 sáng, 3 vùng map đã lộ, đường vào Fire Giant không còn cổng
   khoá nào. Stats 8/8 đều 99, HP 2100 trần vanilla, kho vũ khí đủ Rivers of Blood +10,
   Blood Uchigatana +25, Nagakiba +25 - build không phải vấn đề.
2. Đối chiếu lại 24 questline trong
   `docs/elden-ring-questline-checklist-va-quest-path.md` bằng cách quét item mốc cuối
   qua `list-items --slot 1`.
3. Verify các mốc cơ chế qua WebSearch/WebFetch trước khi trả lời (thứ tự Fire Giant vs
   Malenia, point of no return thật sự, Torrent bị khoá khi summon NPC).

## Phát hiện: `list-items` không đọc mảng key item

Lệnh `elden_ring_save_editor.py list-items` chỉ duyệt `inv["common_off"]`
(`iter_items()` tại `elden_ring_save_editor.py:479-483`), bỏ hẳn `inv["key_off"]` - mảng
384 slot key item. Dump thủ công qua `_iter_records` trên cả hai mảng cho ra **116 key
item không hề xuất hiện trong output `list-items`**, bao gồm `Black Knifeprint`,
`Sellian Sealbreaker`, `Mending Rune of the Fell Curse`, `Unalloyed Gold Needle`, toàn bộ
Great Rune, và các Medallion.

Hệ quả: report `save-audit-260731-0120-...md` (dùng đúng `list-items`) kết luận sai ít
nhất Rogier, Sellen/Jerren, Dung Eater, Rya, Diallos là "chưa xong" - thực ra bằng chứng
nằm trong key array mà lệnh không in ra. Doc `elden-ring-questline-checklist-va-quest-path.md`
bản 2026-08-04 đã tự sửa việc này bằng cách khác (đọc armor + weapon resolve qua gaitem
map), nên phần "Đã xong (24 questline)" của nó **đúng** dù report gốc sai.

## Phát hiện thứ hai: dò spirit ash theo tên "Ashes" bỏ sót nhiều ash

Doc (trước khi sửa) ghi `Black Knife Tiche` và `Blackflame Monk Amon` là chưa có, dựa
trên report cũ. Dump lại theo dải id `200000-299999` (danh mục spirit ash thật, không
phải theo tên) thì cả hai đã có, cả hai +10:

- `Black Knife Tiche` → id `200010` (Alecto: `dead`)
- `Blackflame Monk Amon` → id `228010` (Stray Mimic Tear: `dead`)

Hai lỗi cộng lại: (1) không phải ash nào cũng có chữ "Ashes" trong tên hiển thị -
`Black Knife Tiche`, `Latenna the Albinauric`, `Lhutel the Headless` thì không - nên grep
theo tên bỏ sót; (2) id item mang cả mức nâng ở hai chữ số cuối (`228000` = +0,
`228010` = +10), tìm đúng `228000` sẽ trượt một ash đã nâng cấp.

## Bài học

Cách dò đáng tin cho một loại item trong save này là theo **dải id + cờ boss**, không
phải theo chuỗi tên hay theo lệnh CLI mặc định mà không kiểm tra nó có duyệt hết mảng
inventory hay không. `list-items` là công cụ tiện nhưng phạm vi của nó (chỉ common array)
không được ghi rõ trong help text - phải đọc source mới biết. Liên quan
[[verify-the-probe-before-trusting-its-verdict]] và [[save-editor-slot-and-inventory-probe-traps]].

## Việc còn treo

- Bước cuối của Latenna ở Apostate Derelict không có cờ trong save để xác nhận, doc ghi
  xong nhưng không kiểm chứng lại được lần này.
- Bernahl invade cần đã exhaust thoại ở Volcano Manor sau khi Rykard chết - save không
  đọc được trạng thái này, chỉ suy luận qua `Letter to Bernahl` + Raging Wolf Set đã có.
