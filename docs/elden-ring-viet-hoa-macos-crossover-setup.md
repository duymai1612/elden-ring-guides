# Việt hóa Elden Ring trên macOS (CrossOver)

Trạng thái: đã cài xong và chạy được. Bản việt hóa The Red Team `ERDLCVH_190824` (19/08/2024, có DLC Shadow of the Erdtree).

## TL;DR

Bộ cài `.exe` là installer Windows (PyInstaller + PyQt5), không chạy được trên macOS. Payload thật nằm trong `dlc.zip` bên trong nó, và việc "cài đặt" chỉ là bung thư mục `Game/` của zip đó vào thư mục game. Đã bung thủ công, không ghi đè bất kỳ file gốc nào của game.

- Bottle CrossOver: `Steam`
- Thư mục game: `~/Library/Application Support/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam/steamapps/common/ELDEN RING/Game`
- Khởi chạy: gõ `elden` (hoặc `ervh`) trong terminal, hoặc double-click `elden-ring-viet-hoa.command` ở gốc repo này

Mod loader dùng **me3 v0.12.1**, không dùng ModEngine2 đi kèm bộ cài. ModEngine2 đã bị archive từ 19/07/2024 (bản cuối 2.1) và làm game crash mỗi lần thoát dưới Wine (page fault đọc `0x1000f` trong đường teardown, sau khi save đã ghi xong nên vô hại nhưng gây hộp thoại). me3 là bản kế nhiệm chính thức, vẫn được phát triển, và chạy được trên CrossOver.

Đã chạy thử thành công: me3 log rõ từng file nó thay thế, và phiên chạy đầu thoát sạch không sinh crash dump.

## Việt hóa gồm những gì

Cơ chế là mod loader nạp file text/font đè lên game lúc runtime, không sửa file gốc:

| Đường dẫn (trong `Game/`) | Vai trò |
|---|---|
| `mod/msg/engus/*.msgbnd.dcx` | Toàn bộ text tiếng Việt (base + `dlc01` + `dlc02`) |
| `mod/font/**/font.gfx` | Font hỗ trợ dấu tiếng Việt |
| `modengine2/`, `modengine2_launcher.exe`, `config_eldenring.toml` | ModEngine2 - giữ lại làm phương án dự phòng, không còn dùng |
| `Elden_Ring_VHTRT.bat` | Launcher bản Windows (vô dụng trên macOS) |
| `Gỡ Việt Hóa.exe` | Trình gỡ bản Windows (vô dụng trên macOS) |

me3 nằm ngoài thư mục game, ở `C:\me3` trong bottle (bản portable `me3-windows-amd64.zip`), profile `C:\me3\viet-hoa.me3` trỏ tuyệt đối vào `mod/` nên không copy trùng file nào.

Vì text nằm ở `mod/`, game gốc vẫn nguyên vẹn: bỏ việt hóa chỉ cần xóa thư mục `mod`.

## Cách chạy

`.bat` của Windows không dùng được trên macOS nên có script thay thế `elden-ring-viet-hoa.command` ở gốc repo (alias `elden` / `ervh`). Script tự mở Steam trong bottle nếu chưa chạy, chặn mở trùng phiên, rồi gọi:

```sh
/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine \
  --bottle Steam --workdir 'C:\me3' \
  --cx-app 'C:\me3\bin\me3.exe' launch -p viet-hoa.me3
```

Lưu ý: `--cx-app` phải nhận đường dẫn Windows (`C:\...`), truyền đường dẫn macOS sẽ lỗi `could not find ... in drive_c`.

Shortcut CrossOver cũ (`eldenring`) chạy `eldenring.exe` trực tiếp nên **không có việt hóa**. Muốn tiếng Việt thì chạy qua script trên.

## Đừng mở lại game ngay sau khi vừa thoát

Mở lại quá sớm thì Arxan (lớp chống can thiệp của Elden Ring) bắt trap `int3` và game chết ngay lúc khởi động. Đo được: mở lại sau 16 giây thì chết, sau khoảng 85 giây thì chạy tốt. Script đã chờ tiến trình cũ dọn sạch cộng 5 giây, nếu vẫn gặp `int3` thì đợi thêm khoảng 30 giây rồi chạy lại.

## Kiểm tra mod đã nạp

Log me3 ở `~/Library/Application Support/CrossOver/Bottles/Steam/drive_c/users/crossover/AppData/Local/garyttierney/me3/data/logs/viet-hoa/<ngày>.log`. Nạp thành công sẽ có một dòng `override=` cho mỗi file việt hóa game đọc:

```
override=C:\...\ELDEN RING\Game\mod\msg\engus\menu_dlc02.msgbnd.dcx
override=C:\...\ELDEN RING\Game\mod\font\eu_std\font.gfx
```

Muốn quay lại ModEngine2 thì đổi dòng `exec` cuối trong script (command để sẵn trong comment đầu file). Log ME2 ở `Game/modengine2/logs/modengine_<ngày>.log`, nạp thành công có:

```
ModEngine version 2.1.0-... initializing for Elden Ring
Enabling extension mod_loader
Resolved mod path to C:\...\ELDEN RING\Game\mod
Applied 3 hooks
```

## Chơi mạng

Cả me3 và ModEngine2 đều khởi chạy `eldenring.exe` trực tiếp, bỏ qua EasyAntiCheat, nên chỉ chơi offline. Đây cũng đúng cách shortcut CrossOver cũ đang chạy sẵn. Không bật online với mod để tránh bị ban. me3 mặc định cũng chặn kết nối tới server matchmaking (`start_online` để trống).

## Gỡ việt hóa

Xóa các mục đã thêm trong `Game/` cộng thư mục me3, giữ nguyên phần còn lại:

```sh
B="$HOME/Library/Application Support/CrossOver/Bottles/Steam/drive_c"
ER="$B/Program Files (x86)/Steam/steamapps/common/ELDEN RING/Game"
rm -rf "$ER/mod" "$ER/modengine2" "$ER/modengine2_launcher.exe" \
       "$ER/config_eldenring.toml" "$ER/Elden_Ring_VHTRT.bat" \
       "$ER/Gỡ Việt Hóa.exe" "$ER/steam_appid.txt" "$ER"/modengine_*.log \
       "$ER/backtrace.txt" "$B/me3"
rm -f "$HOME/game/elden-ring/elden-ring-viet-hoa.command"
```

Alias `elden` / `ervh` nằm trong `~/.dotfiles/shell-aliases.sh`, xoá tay nếu cần.

## Nguồn

- Bản việt hóa: https://theredteam.vn/elden-ring.php
- Bộ cài gốc: `~/Downloads/ERDLCVH_190824.exe`
- me3: https://github.com/garyttierney/me3/releases (v0.12.1, 19/07/2026)
- ModEngine2 (đã archive 19/07/2024): https://github.com/soulsmods/ModEngine2
