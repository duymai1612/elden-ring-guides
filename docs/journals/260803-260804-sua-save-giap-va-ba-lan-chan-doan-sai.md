# Thêm Rotten Duelist set: Bốn lần thất bại, ba lần chẩn đoán sai

**Ngày**: 2026-08-03 vào 2026-08-04
**Mục đích**: Thêm bộ áo giáp `Rotten Duelist Set` vào save
**Kết quả**: Thành công sau 4 lần thử + 3 chẩn đoán sai

---

## Dòng sự kiện

### Lần 1: Sửa lúc game đang chạy (im lặng)

User yêu cầu thêm `Rotten Duelist Set`. Không kiểm tra game có đang chạy không, chạy ba
lệnh `replace-armor` lấy `Iron Kasa` và hai mảnh `Ronin's` làm donor. Lệnh báo thành công,
`selftest` báo checksum sạch. Vài phút sau user mở game lên không thấy bộ đó đâu.

Chẩn đoán sai lần 1: "Bộ này không tồn tại trong save hoặc bị orphan."

**Nguyên nhân thực**: Game giữ toàn bộ save trong RAM. Edits được ghi vào file, đầu vào đều hợp lệ, nhưng game lại ghi đè file vào phiên autosave tiếp theo, xóa sạch thay đổi. Không có thông báo lỗi nào cảnh báo điều này.

### Lần 2: Cùng lỗi, do user mở game gần như cùng lúc

User chỉ định thoát game, nhưng mở lại gần như cùng lúc khi tool đang ghi. Giờ có hai phiên game chạy độc lập, chúng ta ghi vào file của một phiên, rồi phiên kia khi tắt lại ghi đè ngay.

Chẩn đoán sai lần 2: "User không thoát game hẳn."

**Nguyên nhân thực**: Cùng như lần 1.

### Lần 3: Bug trong implementation

Viết `replace-armor` bằng cách:

```python
for ent_off, handle, iid in iter_gaitem_entries(data, pgd):
    if not handle or ((handle >> 28) & 0xF) != GAITEM_ARMOR:
        continue
    if iid - ARMOR_ITEM_ID_OFF == src_id:
        hits.append((ent_off, handle, iid))
```

Lệnh có `--index 0`, chọn bộ đầu tiên khớp. Khi `replace-weapon` chạy thì luôn được, vì nó đi từ inventory rồi resolve về gaitem. `replace-armor` đi trực tiếp vào gaitem map, không có đảm bảo là mục đó cũng có trong held inventory.

Sau 24 vòng lặp tìm kiếm trong gaitem, chọn vào một entry không có trong held inventory.

Chẩn đoán sai lần 3: "Gaitem có 218 entries, held inventory có 194. 24 mục đó là orphans mà game bỏ qua."

User phủ định ngay: "Anh có full Ronin set thật, a giết Shabriri trong thân xác Yura rồi."

**Nguyên nhân thực**: Không phải orphan - đó là bộ quần áo lưu trong **storage box** mà probe chưa decode. Probe chỉ đọc held inventory; chưa nhìn thấy storage box nên "không có" mà thôi.

### Lần 4: Thành công

Điểm khác biệt là **chọn donor nằm trong held inventory**, chứ không phải nhóm
`Iron Kasa` / `Ronin's` mà ba lần trước đã dùng. Cả 12 entry của nhóm đó đều không có
bản ghi trong túi, nên mọi lần replace vào chúng đều rơi vào khoảng không.

```
replace-armor --source "Leyndell Soldier Helm"   --target "Rotten Duelist Helm"
replace-armor --source "Tree-and-Beast Surcoat"  --target "Rotten Gravekeeper Cloak"
replace-armor --source "Exile Greaves"           --target "Rotten Duelist Greaves"
```

Ba món donor này đều là bản dư và đều có bản ghi trong túi. Game đã tắt, xác nhận bằng
`running_game_processes()` trả về 0 trước khi ghi. Ghi xong không mảnh nào bị đánh dấu
`[orphan]`, đúng cơ chế đã cho `Black Knife Set` sống sót qua nhiều lần game tự lưu.

---

## Các chẩn đoán sai và gốc rễ chung

### Claim 1: Bảng tên áo giáp bị hỏng ("Type 1", "Type 2", ...)

Ban đầu khi gọi `list-armor`, có đến ~40 dòng "Type 1", "Type 2" ở đầu. Kết luận: bảng tên engine placeholder sẽ đụng độ với real gear.

**Thực tế**: Bảng tên không hỏng. Giải pháp là **bỏ qua** mọi dòng bắt đầu bằng "Type " khi load bảng:

```python
for sid, name in data.get("armor", {}).items():
    if name.startswith("Type "):
        continue
```

Sau đó all 220 pieces resolve được, không đụng độ.

### Claim 2: User không có Ronin's Set

Probe đọc gaitem map thấy 218 entry, đối chiếu held inventory thấy 194 entry có bản ghi.
Bốn mảnh `Ronin's` nằm trong nhóm 24 còn lại, nên bị gán nhãn orphan và kết luận là
"game không thấy". User phủ định: đã giết Shabriri trong thân xác Yura, bộ đó có thật.

**Thực tế**: chưa biết chắc chúng nằm ở đâu, nhưng **không phải rác**. Khả năng cao là
trong **storage box** ở Roundtable Hold, một mảng riêng mà tool chưa decode. Sai lầm không
nằm ở phép đo, mà ở chỗ biến "reader của tôi không thấy" thành "không tồn tại trong game".

### Claim 3: User không có crystal tear nào

Dùng grep tìm "Tear" trong JSON reference table, lọc bỏ một số cái, kết luận: zero tear.

**Thực tế**: user đang giữ **14 crystal tear**, trong đó có đúng hai cái vừa được khuyên
đi nhặt: `Stonebarb Cracked Tear` (param **11026**) và `Thorny Cracked Tear` (param
**11013**), cộng `Purifying Crystal Tear` (**11027**) mà user tự nêu ra.

Lỗi nằm ở phép lọc: grep chuỗi `"Tear"` trên tên hiển thị rồi loại trừ thủ công mấy từ
khoá, thay vì lấy tập id crystal tear từ bảng reference rồi giao với tập id trong túi.
Cách sau chạy đúng ngay lần đầu.

---

## Bài học chung

Mỗi chẩn đoán sai đều từ **một kiểu đo lường thiếu hụt**:

1. **Claim 1 (bảng tên bị hỏng)**: Không biết cơ chế offset. Armor lưu `0x10000000 | param_id` trong gaitem map. Nên khi đọc, phải **trừ offset đã rồi mới tra bảng tên**. Trace test sample: Deathbed Dress = param 1930100, White Mask = 680000. Trong file: `0x10000000 | 680000` = `0x100A69C0`. Trừ offset mới được 680000, tra được White Mask.

2. **Claim 2 (Ronin's Set không có)**: Probe chỉ nhìn thấy **held inventory**, không thấy storage box. Kết luận "không có" là sai vì **chưa thấy không có là không tồn tại**. Muốn nói "người dùng không có X", phải:
   - Scan toàn bộ data structure (held inventory + storage box + drops + ...)
   - Hoặc nói rõ phạm vi: "không có trong held inventory" (không phải "không có")

3. **Claim 3 (zero tears)**: grep trên tên hiển thị không phải một phép đo. Phải so param
   id. Lần này user tự nói ra là mình có `Purifying Crystal Tear`, đọc lại bằng id thì ra
   14 cái. Nếu user không lên tiếng thì kết luận sai đó đã đi thẳng vào doc build.

---

## Cái được build ra

### Commit 6c40dd3: list-armor và replace-armor

**Cơ chế**: Armor param id được lưu với offset `0x10000000` trong gaitem map (để phân biệt với category GAITEM_ARMOR = 0x9 trên handle high nibble). Khi đọc, trừ offset mới được param id thực.

**replace-armor**: Rewrite `item_id` field của một gaitem entry đang có sẵn. Cùng trick như `replace-weapon` - record giữ nguyên size nên handle + inventory record đều không bị xê dịch. Adding new piece không thể vì không có free slot.

**list-armor**: quét gaitem entry mang category `GAITEM_ARMOR`, trừ offset, in tên. Trên
save thật: **218 entry, 194 có bản ghi trong held inventory, 24 không**. Nhóm 24 đó hiện
bị gắn nhãn `[orphan]`, nhưng nhãn này đang gây hiểu lầm và cần sửa: nó chỉ có nghĩa
"không nằm trong túi cầm tay", không phải "game không thấy".

### Commit 1aa9382: Refuse to write while game is running

Game giữ save trong RAM, ghi đè file mỗi autosave. Edits made during live session biến mất im lặng, không có error. Fix: `commit()` now scans process list và abort nếu game đang chạy.

**Bẫy đo lường**: Argv của game dùng Windows path (backslash) kể cả dưới Wine. Pattern `/ELDEN RING/Game/` không bao giờ khớp - phải dùng backslash. Mà shell escape backslash nên phải dùng raw constant hoặc chuyển về tên file/dir mà escape-safe.

**Thêm bẫy**: Shell/python processes khớp với đúng game command vì command line của chính tool có chứa `ELDEN RING` khi user truyền save path. Phải filter bỏ shell/python.

Cờ `--ignore-running-game` để bỏ qua nếu user thực sự muốn (e.g. quick test).

### Commit 7296121: Docs updates

- Thêm parry dagger + Great Stars build guide (đo được đấm giao thiệp, stance break, attack loop)
- Document parts-replacer mod install qua me3: syntax `[[package]]` với `id` + `path` (không phải `[[packages]]` + `name` + `paths` như tutorial sai trên mạng)
- Fix claim trong questline checklist: armor name table không hỏng, Ronin's Set đã có đầy đủ

---

## Cách đo cho đúng (từ lần này học được)

Sắp xếp theo mức độ sai mà dễ lặp lại:

1. **Luôn so sánh param id, không grep tên**. Tên là display label cho người dùng. Param id là địa chỉ thực. Nếu chạy probe mà grep, kết quả "không có" có thể là "tên tìm sai", không phải "mục không tồn tại".

2. **Biết offset, bias khi đo**. Armor = param + 0x10000000 trong gaitem. Item A = param A trong một place, 0x10000000 | A ở place khác. Offset thay đổi → đo ngay bị nhầm.

3. **Probe chỉ thấy phạm vi nó quét**. Nếu quét held inventory, kết luận "không có trong save" là dự đoán. Nói rõ: "không có trong held inventory" hoặc dùng từ chỉ negative để đảm bảo không bị hiểu lầm.

4. **Xác nhận pattern trước khi tin**. Windows path / backslash trong argv, shell escape, process id match - chạy thử một lần, print ra argv để thấy format thực tế.

5. **Lặp lại đo 1-2 lần nếu claim quan trọng**. "User không có X" là một claim nặng. Một sample duy nhất đã từng cho kết luận sai, phản chứng được ở phiên thứ 2. Đừng tự tin sau một lần thắng.

