#!/bin/bash
# Obtenemos la ruta actual de forma segura
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] Instalando Shindo-CLI..."

# Damos permisos a tus archivos locales
chmod +x "$DIR/main.sh"
chmod +x "$DIR/engines/anime/"*.py

# Creamos el comando global (esto es lo que requiere sudo)
sudo ln -sf "$DIR/main.sh" /usr/local/bin/shindo-cli

echo "[+] Instalación terminada. Comando: shindo-cli"