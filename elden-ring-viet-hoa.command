#!/bin/sh
# Chay Elden Ring ban Viet hoa (The Red Team) qua ModEngine 3 (me3) trong CrossOver bottle "Steam".
# Thay cho file Elden_Ring_VHTRT.bat cua ban Windows.
#
# Dung me3 chu khong dung ModEngine2: ME2 bi archive 07/2024 (ban cuoi 2.1, dang cai san trong
# thu muc Game) va lam game crash luc thoat duoi Wine. me3 la ban ke nhiem, van duoc phat trien.
# Profile C:\me3\viet-hoa.me3 tro thang vao thu muc mod/ cua ban Viet hoa, khong copy gi them.
#
# Muon quay lai ModEngine2 thi thay dong exec cuoi bang:
#   GAME='C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game'
#   exec "$WINE" --bottle "$BOTTLE" --workdir "$GAME" \
#     --cx-app "$GAME"'\modengine2_launcher.exe' -t er -c '.\config_eldenring.toml'

WINE="/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine"
BOTTLE="Steam"

# Mo lai game ngay sau khi vua thoat thi Arxan (lop chong can thiep cua Elden Ring)
# bat trap int3 va game chet ngay luc khoi dong. Do la: mo lai sau 16s -> chet,
# sau ~85s -> chay tot. Nen doi cho phien cu don sach han truoc khi mo lai.
if pgrep -f "ELDEN RING.*eldenring\.exe" >/dev/null 2>&1; then
  echo "Elden Ring dang chay roi, thoat game truoc da."
  exit 1
fi
i=0
while pgrep -f "me3-launcher\.exe|me3\.exe" >/dev/null 2>&1 && [ $i -lt 20 ]; do
  echo "Doi phien me3 truoc ket thuc..."
  sleep 2
  i=$((i + 1))
done
sleep 5   # cho Steam va wineserver nha trang thai game vua thoat

# Elden Ring can Steam dang chay trong cung bottle moi khoi dong duoc
if ! pgrep -f "Steam\\\\steam.exe" >/dev/null 2>&1; then
  echo "Steam chua chay, dang mo Steam trong bottle $BOTTLE..."
  "$WINE" --bottle "$BOTTLE" --cx-app 'C:\Program Files (x86)\Steam\steam.exe' >/dev/null 2>&1 &
  i=0
  while [ $i -lt 60 ]; do
    pgrep -f "Steam\\\\steam.exe" >/dev/null 2>&1 && break
    sleep 2
    i=$((i + 1))
  done
  sleep 5
fi

echo "Dang khoi dong Elden Ring (Viet hoa, me3)..."
exec "$WINE" --bottle "$BOTTLE" --workdir 'C:\me3' \
  --cx-app 'C:\me3\bin\me3.exe' launch -p viet-hoa.me3
