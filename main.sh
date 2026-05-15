#!/bin/bash

# --- CONFIGURACIÓN ---
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
FLV_SCRIPT="$SCRIPT_DIR/engines/anime/animeflv.py"
JK_SCRIPT="$SCRIPT_DIR/engines/anime/jkanime.py"
MANGA_SCRIPT="$SCRIPT_DIR/engines/manga/manga_engine.py"

# Archivos temporales para búsquedas en paralelo
TMP_FLV="/tmp/shindo_flv.txt"
TMP_JK="/tmp/shindo_jk.txt"
TMP_MG="/tmp/shindo_mg.txt"

# Limpieza automática al salir
trap 'rm -f "$TMP_FLV" "$TMP_JK" "$TMP_MG"' EXIT

print_logo() {
    clear
    echo -e "\e[1;35m"
    cat << "EOF"
  ██████  ██░ ██  ██▓ ███▄    █ ▓█████▄  ▒█████      ▄████▄   ██▓     ██▓
▒██    ▒ ▓██░ ██▒▓██▒ ██ ▀█   █ ▒██▀ ██▌▒██▒  ██▒   ▒██▀ ▀█  ▓██▒    ▓██▒
░ ▓██▄   ▒██▀▀██░▒██▒▓██  ▀█ ██▒░██   █▌▒██░  ██▒   ▒▓█    ▄ ▒██░    ▒██▒
  ▒   ██▒░▓█ ░██ ░██░▓██▒  ▐▌██▒░▓█▄   ▌▒██   ██░   ▒▓▓▄ ▄██▒▒██░    ░██░
▒██████▒▒░▓█▒░██▓░██░▒██░   ▓██░░▒████▓ ░ ████▓▒░   ▒ ▓███▀ ░░██████▒░██░
EOF
    echo -e "\e[0m"
}

# --- MENU PRINCIPAL ---
print_logo
echo -e "\e[1;36m=== PANEL DE CONTROL SHINDO ===\e[0m"
echo -e " 1) \e[1;32m[ANIME]\e[0m Buscar en AnimeFLV + JKAnime"
echo -e " 2) \e[1;33m[MANGA]\e[0m Buscar en NovelCool + LectorTMO"
echo -e " q) Salir"
echo "--------------------------------"
read -r -p " SELECCIÓN > " modo

if [[ "$modo" == "q" || -z "$modo" ]]; then exit 0; fi

# --- INTERFAZ DE BÚSQUEDA ---
print_logo
read -r -p " INTRODUCE TU BÚSQUEDA > " busqueda
if [ -z "$busqueda" ]; then echo "Búsqueda vacía."; exit 1; fi

echo -e "\e[1;30m[*] Escaneando servidores en tiempo real...\e[0m"

if [[ "$modo" == "1" ]]; then
    # Lanzamiento en paralelo para agilizar la respuesta
    python3 "$FLV_SCRIPT" "buscar" "$busqueda" > "$TMP_FLV" & PID1=$!
    python3 "$JK_SCRIPT" "buscar" "$busqueda" > "$TMP_JK" & PID2=$!
    wait $PID1 $PID2 2>/dev/null
    [ -s "$TMP_FLV" ] && sed -i 's/$/ [AnimeFLV]/' "$TMP_FLV"
    [ -s "$TMP_JK" ] && sed -i 's/$/ [JKAnime]/' "$TMP_JK"
    resultados=$(cat "$TMP_FLV" "$TMP_JK" 2>/dev/null)
else
    python3 "$MANGA_SCRIPT" "buscar" "$busqueda" > "$TMP_MG"
    resultados=$(cat "$TMP_MG" 2>/dev/null)
fi

if [ -z "$resultados" ]; then
    echo -e "\e[1;31m[-] No se encontraron coincidencias.\e[0m"
    exit 1
fi

# Filtro interactivo mediante FZF
seleccion=$(echo -e "$resultados" | fzf --prompt="SELECCIONAR SERIE > " --height=40% --reverse --border)
if [ -z "$seleccion" ]; then exit 0; fi

url_base=$(echo "$seleccion" | awk -F " --> " '{print $2}' | awk '{print $1}')
nombre=$(echo "$seleccion" | awk -F " --> " '{print $1}')

# --- OBTENCIÓN DE CAPÍTULOS ---
print_logo
echo -e "\e[1;34m[+] Extrayendo índices de reproducción de: $nombre...\e[0m"

if [[ "$modo" == "1" ]]; then
    if [[ "$seleccion" == *"[JKAnime]"* ]]; then 
        SCRIPT="$JK_SCRIPT"; ref="https://jkanime.net/"; origen="JKAnime"
    else 
        SCRIPT="$FLV_SCRIPT"; ref="https://www3.animeflv.net/"; origen="AnimeFLV"
    fi
else
    SCRIPT="$MANGA_SCRIPT"
    if [[ "$seleccion" == *"[LectorTMO]"* ]]; then origen="LectorTMO"; ref="https://lectortmo.vip/"; else origen="NovelCool"; ref="https://es.novelcool.com/"; fi
fi

lista_caps=$(python3 "$SCRIPT" "caps" "$url_base")
if [ -z "$lista_caps" ]; then echo "Error al obtener capítulos."; exit 1; fi

cap_elegido=$(echo "$lista_caps" | fzf --prompt="SELECCIONAR CAPÍTULO > " --height=40% --reverse --border)
if [ -z "$cap_elegido" ]; then exit 0; fi

# Aislar variables de navegación
current_url=$(echo "$cap_elegido" | awk -F " --> " '{print $2}')
num_cap=$(echo "$cap_elegido" | awk -F " --> " '{print $1}')

# --- BUCLE CONTINUO (MODO SALÓN / CONTROL REMOTO) ---
while true; do
    print_logo
    echo -e "\e[1;42m REPRODUCIENDO: $nombre - $num_cap [$origen] \e[0m"
    echo -e "\e[1;30m[Tip: Si usas MPV, maneja el volumen y tiempo con las flechas del móvil vía SSH]\e[0m\n"
    
    if [[ "$modo" == "1" ]]; then
        # Extraer el número plano del string para los motores de anime
        num_solo=$(echo "$num_cap" | grep -oP '\d+' | head -1)
        links=$(python3 "$SCRIPT" "ver" "$url_base" "$num_solo")
        exito=0
        
        # Intentar reproducción limpia nativa
        for link in $links; do
            echo -e "\e[1;30m[Lanzando nodo de streaming público...]\e[0m"
            if mpv "$link" --referrer="$ref" --user-agent="Mozilla/5.0" --fs --network-timeout=10 --msg-level=all=no; then
                exito=1
                break
            fi
        done
        
        # Plan B Automático: Navegador en modo aplicación aislada si MPV falla
        if [ $exito -eq 0 ]; then
            echo -e "\e[1;33m[*] Nodo directo incompatible. Abriendo interfaz web optimizada...\e[0m"
            # Intentar Chrome, si no usar Firefox en modo Kiosko
            google-chrome --app="$current_url" --start-fullscreen 2>/dev/null || firefox --kiosk "$current_url" &
        fi
    else
        # Lanzamiento del visualizador de Manga en Pantalla Completa Aislada
        echo -e "\e[1;34m[*] Proyectando visualizador de manga...\e[0m"
        google-chrome --app="$current_url" --start-fullscreen 2>/dev/null || firefox --kiosk "$current_url" &
    fi

    # --- CONTROLADOR DE FLUJO ---
    echo -e "\n\e[1;36m>>> OPCIONES DE CONTROL (Desde el sofá):\e[0m"
    echo -e " [Enter] Cargar siguiente capítulo automáticamente"
    echo -e " [q]     Cerrar y volver al menú principal"
    echo "----------------------------------------------------"
    read -r -p " CONTROL > " comando

    if [[ "$comando" == "q" ]]; then
        # Matar procesos de navegadores en segundo plano si abrimos el Plan B o el Manga
        pkill -f "google-chrome --app" 2>/dev/null
        pkill -f "firefox --kiosk" 2>/dev/null
        break
    fi

    # Buscar la línea actual en la lista y saltar a la inmediatamente posterior
    next_line=$(echo "$lista_caps" | grep -A 1 "$current_url" | tail -n 1)
    current_url=$(echo "$next_line" | awk -F " --> " '{print $2}')
    num_cap=$(echo "$next_line" | awk -F " --> " '{print $1}')

    if [[ -z "$next_line" || "$current_url" == "" ]]; then
        echo -e "\e[1;33m[-] Has alcanzado el último capítulo disponible.\e[0m"
        sleep 2
        break
    fi
    
    # Limpieza preventiva de ventanas anteriores antes de abrir el siguiente ciclo
    pkill -f "google-chrome --app" 2>/dev/null
    pkill -f "firefox --kiosk" 2>/dev/null
done