#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  python3 -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/pip" install -r "$ROOT/requirements.txt"
fi

PY="$ROOT/.venv/bin/python"
PREFIX="$("$PY" -c 'import sys; print(sys.base_prefix)')"
INCLUDE="$("$PY" -c 'import sysconfig; print(sysconfig.get_config_var("INCLUDEPY"))')"
LIBDIR="$("$PY" -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR"))')"
SITE="$("$PY" -c 'import site; print(site.getsitepackages()[0])')"

APP="$ROOT/VozBar.app"
MACOS="$APP/Contents/MacOS"

rm -rf "$APP"
mkdir -p "$MACOS"
cp "$ROOT/macos/Info.plist" "$APP/Contents/Info.plist"

clang -o "$MACOS/VozBar" "$ROOT/macos/launcher.c" \
  -DPYTHON_HOME="\"$PREFIX\"" \
  -DPYTHON_SITE="\"$SITE\"" \
  -I"$INCLUDE" \
  -lpython3.10 \
  -L"$LIBDIR" \
  -Wl,-rpath,"$LIBDIR" \
  -ldl \
  -framework CoreFoundation

chmod +x "$MACOS/VozBar"
codesign --force --sign - "$APP" >/dev/null
echo "Built $APP"
