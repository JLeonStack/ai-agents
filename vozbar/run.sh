#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
"$ROOT/build_app.sh"
open "$ROOT/VozBar.app"
echo "VozBar abierto. Hold Option para dictar. Permisos: Micrófono, Reconocimiento de voz, Accesibilidad."
