# Việt hóa Elden Ring trên macOS (CrossOver)

Trạng thái: đã cài xong và chạy được. Bản việt hóa The Red Team `ERDLCVH_190824` (19/08/2024, có DLC Shadow of the Erdtree).

## TL;DR

Bộ cài `.exe` là installer Windows (PyInstaller + PyQt5), không chạy được trên macOS. Payload thật nằm trong `dlc.zip` bên trong nó, và việc "cài đặt" chỉ là bung thư mục `Game/` của zip đó vào thư mục game. Đã bung thủ công, không ghi đè bất kỳ file gốc nào của game.

- Bottle CrossOver: `Steam`
- Thư mục game: `~/Library/Application Support/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam/steamapps/common/ELDEN RING/Game`
- Khởi chạy: gõ `warp` (hoặc `elden` / `ervh`) trong terminal, mở `Warp.app` trong `~/Applications`, hoặc double-click `warp.command` ở gốc repo này
- Tên hiển thị trên macOS là **Warp** ở mọi chỗ, xem [Đổi tên hiển thị thành "Warp"](#đổi-tên-hiển-thị-thành-warp)

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

`.bat` của Windows không dùng được trên macOS nên có script thay thế `warp.command` ở gốc repo (alias `warp` / `elden` / `ervh`). Script tự mở Steam trong bottle nếu chưa chạy, chặn mở trùng phiên, rồi gọi:

```sh
/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine \
  --bottle Steam --workdir 'C:\me3' \
  --cx-app 'C:\me3\bin\me3.exe' launch \
  --exe 'C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game\Warp' \
  -p viet-hoa.me3
```

Lưu ý: `--cx-app` phải nhận đường dẫn Windows (`C:\...`), truyền đường dẫn macOS sẽ lỗi `could not find ... in drive_c`.

`Warp.app` trong `~/Applications` là bản copy của chính script này, đóng gói lại thành app bundle để mở từ Finder/Spotlight/Dock mà không bật cửa sổ Terminal. Sửa `warp.command` xong thì đồng bộ lại:

```sh
cp ~/game/elden-ring/warp.command ~/Applications/Warp.app/Contents/MacOS/Warp
```

Shortcut CrossOver (`Warp (vanilla)`, `Warp (shortcut)`) chạy `eldenring.exe` trực tiếp nên **không có việt hóa**. Muốn tiếng Việt thì chạy qua script trên.

## Đổi tên hiển thị thành "Warp"

Tên game xuất hiện ở hai lớp độc lập, đổi lớp này không kéo theo lớp kia:

| Lớp | Nguồn tên | Cách đổi |
|---|---|---|
| Finder / Launchpad / Spotlight | `CFBundleName` trong app bundle | Đổi tên `.app` + sửa plist |
| Dock / Cmd+Tab / Activity Monitor **lúc đang chạy** | basename của file exe Windows | Gọi game qua file tên khác |

Lớp thứ hai là chỗ dễ nhầm. Wine đặt tên process macOS bằng cách hardlink `wineloader` thành `/tmp/winetemp-*/<tên-exe>`, rồi macOS lấy tên file đó làm tên app. Nên tên trên Dock bám theo **tên file exe**, hoàn toàn không liên quan tới app bundle nào đã mở nó.

Cách làm ở đây, không sửa một byte nào của game:

```sh
G="$HOME/Library/Application Support/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam/steamapps/common/ELDEN RING/Game"
ln "$G/eldenring.exe" "$G/Warp"     # hardlink, cùng inode, tốn 0 byte
```

Rồi trỏ me3 vào hardlink đó bằng cờ `--exe` (xem [Cách chạy](#cách-chạy)). File `eldenring.exe` gốc còn nguyên nên chạy thẳng qua Steam vẫn bình thường.

Đặt tên `Warp` không có đuôi `.exe` là cố ý: wine nạp PE theo magic byte chứ không theo đuôi file, và macOS hiện nguyên basename, nên có đuôi thì Dock sẽ hiện `Warp.exe`.

Hardlink giữ nguyên nội dung file nên Arxan (kiểm tra toàn vẹn code, không kiểm tra tên file) và Steam DRM (đọc appid từ `steam_appid.txt`) đều không bị ảnh hưởng.

Các bundle đã đổi tên:

| Trước | Sau |
|---|---|
| — | `~/Applications/Warp.app` (mới, bản việt hóa) |
| `~/Applications/CrossOver/Steam/ELDEN RING.app` | `Warp (vanilla).app` |
| `~/Applications/CrossOver/eldenring.app` | `Warp (shortcut).app` |

Hai bundle của CrossOver do CrossOver tự sinh ra từ shortcut trong bottle, nên nếu CrossOver đồng bộ lại menu thì tên cũ có thể quay về. Lúc đó đổi tên lại và sửa `CFBundleName` + `CXOriginalMenuName` trong `Contents/Info.plist`, rồi `killall Dock`.

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
       "$ER/backtrace.txt" "$B/me3" "$ER/Warp"
rm -f "$HOME/game/elden-ring/warp.command"
rm -rf "$HOME/Applications/Warp.app"
```

Alias `warp` / `elden` / `ervh` nằm trong `~/.dotfiles/shell-aliases.sh`, xoá tay nếu cần.

Hai bundle `Warp (vanilla).app` và `Warp (shortcut).app` là của CrossOver, đổi tên về `ELDEN RING.app` / `eldenring.app` nếu muốn trả lại nguyên trạng.

## Nguồn

- Bản việt hóa: https://theredteam.vn/elden-ring.php
- Bộ cài gốc: `~/Downloads/ERDLCVH_190824.exe`
- me3: https://github.com/garyttierney/me3/releases (v0.12.1, 19/07/2026)
- ModEngine2 (đã archive 19/07/2024): https://github.com/soulsmods/ModEngine2
