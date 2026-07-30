# Sửa được gì và không sửa được gì: Elden Ring trên macOS / CrossOver

Ghi lại ranh giới đã kiểm chứng bằng thực nghiệm, để không phải thử lại. Setup: CrossOver bottle "Steam", Wine 11.0, me3 v0.12.1, bản Việt hoá The Red Team, launcher `warp.command`.

## Làm được

| Việc | Công cụ | Ghi chú |
|---|---|---|
| Sửa save: runes, stats, HP, item, Ash of War | `elden_ring_save_editor.py` | offline, có `selftest` đối chiếu model với file thật |
| Nâng cấp / đổi vũ khí đang có | `... replace-weapon` | **thêm** vũ khí mới thì không được: slot 1 hết chỗ trống, cần +13 byte mà còn 0 byte |
| Bật Site of Grace, hiện map, whetblade, cookbook, summoning pool | `elden_ring_grace_unlock.py` | qua event flag, không phải item |
| Thay asset (text, font, msgbnd) | package của me3 | bản Việt hoá đang chạy bằng cách này |
| Save riêng để luyện tập | `savefile` trong profile me3 | `luyen-tap.command` dùng `ER_luyentap.sl2`, save chính không bị đụng |

## Không làm được

| Việc | Vì sao | Đã đo thế nào |
|---|---|---|
| Sửa `regulation.bin` (mọi param) | Đổi **1 float** cũng làm game abort khi load nhân vật; file gốc load bình thường | Hai lần chạy liền nhau, cùng profile cùng save, khác 4 byte. Chi tiết: `plans/reports/regulation-modding-260730-1215-*.md` |
| Đặt HP trực tiếp trong save | Game tính lại `max_hp` từ Vigor lúc load rồi ghi ngược vào save | `set-hp 60000` → quay về 2100 |
| ER Practice Tool (`jdsd_er_practice_tool.dll`) | d3dmetal: MinHook không vá được (`MH_ERROR_NOT_EXECUTABLE`). dxvk: hook được nhưng VKD3D thiếu thư viện chuyển đổi DXIL → shader DX12 không biên dịch → crash | Thử cả hai backend |

Hệ quả: **không có cách nào cho HP không giới hạn** trên setup này. Muốn luyện boss không chết thì chỉ còn dùng save riêng và chết thoải mái.

## Điểm cần biết về `regulation.bin`

Đã giải xong format, script còn giữ (`elden_ring_regulation.py`). Dùng lại được trên Windows thật.

`AES-256-CBC (IV 16 byte đầu)` → `DCX (ZSTD)` → `BND4` chứa 194 `.param`

- Khoá AES: `erRegulationKey`, có trong `SoulsFormats/Util/SFUtil.cs`
- DCX header 76 byte, chỉ hai trường kích thước ở `0x1C` thay đổi
- Khung zstd: `FHD=0x00`, `window_descriptor=0x80`; plaintext đệm zero cho đủ bội số 16
- PARAM: bảng hàng ở `0x40`, mỗi mục 24 byte `id u32 | pad u32 | data_off u64 | name_off u64`
- Đường cong Vigor→HP: `CalcCorrectGraph` hàng 100. Nhận diện bằng dữ liệu - hàng duy nhất có mốc x = 1/25/40/60/99 **và** y = 300/800/1450/1900/2100
- Paramdef lấy từ `soulstruct/eldenring/params/paramdef/` (tên gốc FromSoft sai chính tả: `CACL_CORRECT_GRAPH_ST`)

`disable_arxan = true` trong profile me3 có tác dụng thật: nó cho một regulation đã sửa **qua được màn hình title**. Nhưng không vào được thế giới. Đừng nhầm "qua title" là "chạy được".

## Cách đo cho đúng

Ba lỗi đo lường trong buổi làm việc này đều cho ra kết luận tự tin nhưng sai. Ghi lại để tránh lặp:

1. **argv của game là đường dẫn Windows dùng `\`.** `pgrep -f 'ELDEN RING/Game/Warp'` không bao giờ khớp và báo mọi lần chạy là "chết". Kiểm chứng pattern trước khi tin verdict.
2. **Phải chờ phiên cũ tắt hẳn.** Launch sớm thì phiên mới bị giết, hoặc detector bám vào phiên cũ đang shutdown rồi báo "chết sau 0s". Bỏ cuộc nếu không dọn được, đừng chạy tiếp.
3. **Title screen không phải đường load nhân vật.** Regulation đã sửa sống hơn 110 giây ở title trong bốn lần đo liên tiếp, rồi chết ngay khi load nhân vật. Phải đo đúng đường thực sự dùng.

Hai kỹ thuật cứu được các kết luận sai:

- **Sửa lượng nhỏ nhất có thể** để tách "việc sửa" khỏi "sửa cái gì". `2100 → 2101` trả lời trong một lần chạy điều mà sáu lần thử giá trị lớn không trả lời được.
- **Lặp lại mỗi phép đo.** Một mẫu duy nhất đã một lần dẫn tới kết luận sai ("giá trị lớn mới là vấn đề") mà lần chạy thứ hai phủ định.

## Oracle kiểm chứng

`elden_ring_save_editor.py list` in `vigor` và `max_hp`. `max_hp` là con số **game tự tính** rồi ghi vào save, không phải giá trị mình đặt. Nên nó là cách xác nhận end-to-end cho bất kỳ thay đổi nào liên quan HP. Vanilla: 2100 ở Vigor 99, 522 ở Vigor 15.
