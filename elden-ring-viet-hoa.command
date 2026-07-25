#!/bin/sh
# Chay Elden Ring ban Viet hoa (The Red Team) qua ModEngine2 trong CrossOver bottle "Steam".
# Thay cho file Elden_Ring_VHTRT.bat cua ban Windows.

WINE="/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine"
BOTTLE="Steam"
GAME='C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game'

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

echo "Dang khoi dong Elden Ring (Viet hoa)..."
exec "$WINE" --bottle "$BOTTLE" --workdir "$GAME" \
  --cx-app "$GAME"'\modengine2_launcher.exe' \
  -t er -c '.\config_eldenring.toml'
