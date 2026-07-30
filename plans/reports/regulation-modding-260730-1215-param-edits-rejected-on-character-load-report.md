# Không mod được regulation.bin trên CrossOver: mọi sửa đổi param làm vỡ đường load nhân vật

Kết luận: hướng này hết đường. Không đạt được HP không giới hạn qua `regulation.bin`.

## Bằng chứng

Hai lần chạy liền nhau, cùng profile, cùng save, cùng `disable_arxan = true`. Khác nhau đúng 4 byte:

| regulation.bin | title screen | load nhân vật |
|---|---|---|
| gốc | sống | **được** - save ghi sau 11s, `max_hp` 2100 / 522 |
| sửa 4 byte (2100→2101) | sống | **chết ~15s**, `movl $0xdeadba, 0` |

File sửa 4 byte có kích thước **đúng bằng** bản repack không sửa (1.726.256 byte). Nên không phải kích thước, không phải container, không phải giá trị, không phải độ lớn.

`disable_arxan = true` có tác dụng thật nhưng chỉ ở title screen:

| file | `disable_arxan` | title screen |
|---|---|---|
| sửa 4 byte | false | chết 22s |
| sửa 4 byte | true | sống 130s, lặp lại 110s |
| HP 9999 | true | sống 110s, lặp lại 110s |

Tắt Arxan đưa được qua title, không vào được thế giới.

## Cái gì vẫn dùng được

`regulation.bin` đã giải mã và đóng gói lại được byte-exact. Format:

`AES-256-CBC (IV 16 byte đầu)` → `DCX (ZSTD)` → `BND4` chứa 194 `.param`

- Khoá AES: `erRegulationKey` trong `SoulsFormats/Util/SFUtil.cs`
- DCX header 76 byte, chỉ hai trường kích thước tại `0x1C` thay đổi
- Khung zstd: `FHD=0x00`, `window_descriptor=0x80`
- Plaintext đệm zero cho đủ bội số 16
- PARAM: bảng hàng tại `0x40`, mỗi mục 24 byte `id u32 | pad u32 | data_off u64 | name_off u64`

Đường cong Vigor→HP là `CalcCorrectGraph` hàng 100, nhận diện bằng dữ liệu: hàng duy nhất có mốc x = 1/25/40/60/99 **và** y = 300/800/1450/1900/2100. Paramdef từ `soulstruct/eldenring/params/paramdef/CACL_CORRECT_GRAPH_ST.py`.

Script: `elden_ring_regulation.py` (giải mã + đóng gói lại), `elden_ring_patch_hp_curve.py` (sửa đường cong). Cần `pycryptodome` + `zstandard`. Dùng được nếu sau này setup thay đổi (CrossOver cập nhật, hoặc chạy trên Windows thật).

## Ba lỗi đo lường đã cho ra kết luận sai

Đáng ghi lại vì cả ba đều tạo ra verdict tự tin nhưng sai:

1. **Pattern sai** - `pgrep -f 'ELDEN RING/Game/Warp'` dùng `/`, argv của tiến trình dùng `\`. Không bao giờ khớp, nên mọi lần chạy đều báo "chết". Suýt kết luận ngược: rằng repack không có lỗi.
2. **Đua với phiên cũ** - launch trước khi phiên trước tắt hẳn. Phiên mới bị giết, hoặc detector bám vào phiên cũ đang shutdown rồi báo "chết sau 0s". Xảy ra hai lần, lần đầu chỉ nhận lỗi mà không sửa vào script dùng chung nên nó quay lại.
3. **Đo sai đường** - bốn ô ma trận đều chỉ ngồi ở title screen, không ai bấm gì. Tuyên bố thành công trên phép đo không chạm tới đường load nhân vật - đường duy nhất quan trọng.

Hai thứ cứu được các kết luận sai: sửa **lượng nhỏ nhất có thể** (2100→2101) để tách "việc sửa" khỏi "sửa cái gì", và **lặp lại mỗi phép đo** thay vì tin một mẫu.

## Oracle đọc HP

`elden_ring_save_editor.py list` giờ in thêm `vigor` và `max_hp`. `max_hp` không phải giá trị đặt được: game tính lại từ Vigor lúc load rồi ghi ngược vào save. Nên nó là oracle chỉ-đọc để biết có thứ gì thực sự đổi đường cong HP hay không. Vanilla: 2100 ở Vigor 99, 522 ở Vigor 15.

## Trạng thái hiện tại

- `Game/regulation.bin` bản gốc, verify bằng `cmp`
- `C:\me3\practice-mod\regulation.bin` đã xoá, package đã bỏ khỏi profile
- `disable_arxan` đã bỏ - không đổi lại được gì mà giảm lớp chống sửa đổi
- `luyen-tap.me3` giữ lại: Việt hoá + save riêng `ER_luyentap.sl2`. Vẫn hữu ích để luyện tập mà không ảnh hưởng save chính
- `warp.command` không bị đụng

## Còn lại cho mục tiêu ban đầu

Luyện parry không chết: không có đường mod nào trên setup này. Thực tế còn lại là dùng `luyen-tap.command` - chết thoải mái trên save riêng, save chính không ảnh hưởng.

## Câu hỏi chưa trả lời

- Tại sao sửa param chỉ vỡ ở đường load nhân vật mà không vỡ ở title? Chưa trace được, và không cần thiết vì kết luận không đổi.
- Trên Windows thật, cùng file này có load được không? Chưa có cách kiểm tra ở đây. Nếu được thì vấn đề nằm ở Wine/CrossOver chứ không ở game.
