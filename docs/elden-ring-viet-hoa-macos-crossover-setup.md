# Việt hóa Elden Ring trên macOS (CrossOver)

Trạng thái: đã cài xong và chạy được. Bản việt hóa The Red Team `ERDLCVH_190824` (19/08/2024, có DLC Shadow of the Erdtree).

## TL;DR

Bộ cài `.exe` là installer Windows (PyInstaller + PyQt5), không chạy được trên macOS. Payload thật nằm trong `dlc.zip` bên trong nó, và việc "cài đặt" chỉ là bung thư mục `Game/` của zip đó vào thư mục game. Đã bung thủ công, không ghi đè bất kỳ file gốc nào của game.

- Bottle CrossOver: `Steam`
- Thư mục game: `~/Library/Application Support/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam/steamapps/common/ELDEN RING/Game`
- Khởi chạy: gõ `elden` (hoặc `ervh`) trong terminal, hoặc double-click `elden-ring-viet-hoa.command` ở gốc repo này

Đã chạy thử thành công: `modengine2.dll` inject vào tiến trình game, log 0 lỗi, và game thật sự đọc các file việt hóa (`atime` của `mod/msg/engus/menu.msgbnd.dcx`, `menu_dlc02.msgbnd.dcx`, `font/eu_std/font.gfx` đều cập nhật sau lúc khởi chạy).

## Việt hóa gồm những gì

Cơ chế là ModEngine2 2.1.0 nạp file text/font đè lên game lúc runtime, không sửa file gốc:

| Đường dẫn (trong `Game/`) | Vai trò |
|---|---|
| `mod/msg/engus/*.msgbnd.dcx` | Toàn bộ text tiếng Việt (base + `dlc01` + `dlc02`) |
| `mod/font/**/font.gfx` | Font hỗ trợ dấu tiếng Việt |
| `modengine2/`, `modengine2_launcher.exe` | Mod loader + launcher |
| `config_eldenring.toml` | Trỏ mod loader tới thư mục `mod` |
| `Elden_Ring_VHTRT.bat` | Launcher bản Windows (vô dụng trên macOS) |
| `Gỡ Việt Hóa.exe` | Trình gỡ bản Windows (vô dụng trên macOS) |

Vì text nằm ở `mod/`, game gốc vẫn nguyên vẹn: bỏ việt hóa chỉ cần xóa thư mục `mod`.

## Cách chạy

`.bat` của Windows không dùng được trên macOS nên có script thay thế ở `~/Desktop/Elden Ring Việt Hóa.command`. Script tự mở Steam trong bottle nếu chưa chạy, rồi gọi:

```sh
/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine \
  --bottle Steam \
  --workdir 'C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game' \
  --cx-app 'C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game\modengine2_launcher.exe' \
  -t er -c '.\config_eldenring.toml'
```

Lưu ý: `--cx-app` phải nhận đường dẫn Windows (`C:\...`), truyền đường dẫn macOS sẽ lỗi `could not find ... in drive_c`.

Shortcut CrossOver cũ (`eldenring`) chạy `eldenring.exe` trực tiếp nên **không có việt hóa**. Muốn tiếng Việt thì chạy qua script trên.

## Kiểm tra mod đã nạp

Log ở `Game/modengine2/logs/modengine_<ngày>.log`, nạp thành công sẽ có:

```
ModEngine version 2.1.0-... initializing for Elden Ring
Enabling extension mod_loader
Resolved mod path to C:\...\ELDEN RING\Game\mod
Applied 3 hooks
```

## Chơi mạng

ModEngine2 khởi chạy `eldenring.exe` trực tiếp, bỏ qua EasyAntiCheat, nên chỉ chơi offline. Đây cũng đúng cách shortcut CrossOver cũ đang chạy sẵn. Không bật online với mod để tránh bị ban.

## Gỡ việt hóa

Xóa các mục đã thêm trong `Game/`, giữ nguyên phần còn lại:

```sh
ER="$HOME/Library/Application Support/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam/steamapps/common/ELDEN RING/Game"
rm -rf "$ER/mod" "$ER/modengine2" "$ER/modengine2_launcher.exe" \
       "$ER/config_eldenring.toml" "$ER/Elden_Ring_VHTRT.bat" \
       "$ER/Gỡ Việt Hóa.exe" "$ER/steam_appid.txt" "$ER"/modengine_*.log
rm -f "$HOME/Desktop/Elden Ring Việt Hóa.command"
```

## Nguồn

- Bản việt hóa: https://theredteam.vn/elden-ring.php
- Bộ cài gốc: `~/Downloads/ERDLCVH_190824.exe`
