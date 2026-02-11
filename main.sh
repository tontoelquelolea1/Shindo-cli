#!/bin/bash

# --- CONFIGURACIÓN ---
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
FLV_SCRIPT="$SCRIPT_DIR/engines/anime/animeflv.py"
JK_SCRIPT="$SCRIPT_DIR/engines/anime/jkanime.py"
TMP_FLV="/tmp/shindo_flv.txt"
TMP_JK="/tmp/shindo_jk.txt"

# --- AUTOPROTECCIÓN DE PERMISOS (Seguridad ASIR) ---
# Nos aseguramos de que solo tú puedas leer/escribir/ejecutar los motores
chmod 700 "$FLV_SCRIPT" "$JK_SCRIPT" 2>/dev/null

# Limpieza automática al salir
trap 'rm -f "$TMP_FLV" "$TMP_JK"' EXIT

print_logo() {
    clear
    echo -e "\e[1;35m"
    cat << "EOF"
  ██████  ██░ ██  ██▓ ███▄    █ ▓█████▄  ▒█████  
▒██    ▒ ▓██░ ██ ▓██▒ ██ ▀█   █ ▒██▀ ██▌▒██▒  ██▒
░ ▓██▄   ▒██▀▀██ ▒██▒▓██  ▀█ ██▒░██   █▌▒██░  ██▒
  ▒   ██▒░▓█ ░ ██ ░██░▓██▒  ▐▌██▒░▓█▄   ▌▒██   ██░
▒██████▒▒░▓█▒ ░██▒░██░▒██░   ▓██░░▒████▓ ░ ████▓▒░
EOF
    echo -e "\e[1;36m              --- SHINDO CLI v2.2 ---          \e[0m\n"
}

# --- BÚSQUEDA ---
print_logo
read -r -p " SEARCH > " busqueda
if [ -z "$busqueda" ]; then exit 1; fi

echo -e "\e[1;30m[*] Escaneando AnimeFLV + JKAnime...\e[0m"

# Lanzamiento paralelo seguro
python3 "$FLV_SCRIPT" "buscar" "$busqueda" > "$TMP_FLV" & PID1=$!
python3 "$JK_SCRIPT" "buscar" "$busqueda" > "$TMP_JK" & PID2=$!
wait $PID1 $PID2 2>/dev/null

# Etiquetado de fuentes
[ -s "$TMP_FLV" ] && sed -i 's/$/ [AnimeFLV]/' "$TMP_FLV"
[ -s "$TMP_JK" ] && sed -i 's/$/ [JKAnime]/' "$TMP_JK"

resultados=$(cat "$TMP_FLV" "$TMP_JK" 2>/dev/null)

if [ -z "$resultados" ]; then
    echo -e "\e[1;31m[-] Sin resultados en los servidores.\e[0m"
    exit 1
fi

seleccion=$(echo -e "$resultados" | fzf --prompt="ANIME > " --height=40% --reverse --border)
if [ -z "$seleccion" ]; then exit 0; fi

url_anime=$(echo "$seleccion" | awk -F " --> " '{print $2}' | awk '{print $1}')
nombre=$(echo "$seleccion" | awk -F " --> " '{print $1}')

if [[ "$seleccion" == *"[JKAnime]"* ]]; then
    SCRIPT="$JK_SCRIPT"; ref="https://jkanime.net/"; origen="JKAnime"
else
    SCRIPT="$FLV_SCRIPT"; ref="https://www3.animeflv.net/"; origen="AnimeFLV"
fi

# --- LISTADO DE EPISODIOS ---
print_logo
echo -e "\e[1;33m[+] Cargando episodios desde $origen...\e[0m"
lista_caps=$(python3 "$SCRIPT" "caps" "$url_anime")
cap_elegido=$(echo "$lista_caps" | fzf --prompt="EPISODIO > " --height=40% --reverse --border)
if [ -z "$cap_elegido" ]; then exit 0; fi
num=$(echo "$cap_elegido" | awk '{print $2}')

# --- REPRODUCCIÓN ---
while true; do
    print_logo
    echo -e "\e[1;32m>> PLAYING: $nombre - CAP $num ($origen)\e[0m"
    
    links=$(python3 "$SCRIPT" "ver" "$url_anime" "$num")
    exito=0
    
    if [ -n "$links" ]; then
        for link in $links; do
            node=$(echo "$link" | awk -F[/:] '{print $4}')
            echo -e "\e[1;30m[Streaming: $node]\e[0m"
            
            if mpv "$link" --referrer="$ref" --user-agent="Mozilla/5.0" --fs --network-timeout=10 --msg-level=all=no; then
                exito=1
                break
            fi
        done
    fi

    if [ $exito -eq 0 ]; then
        echo -e "\e[1;31m[-] Nodo caído. Intenta con otra fuente.\e[0m"
        break
    fi

    # --- AUTO-NEXT ---
    echo -e "\n\e[1;36m>>> SIGUIENTE CAPÍTULO EN 15 SEGUNDOS...\e[0m"
    echo -e "\e[1;30m[Enter: Ya! | q: Salir]\e[0m"
    
    if read -r -t 15 -n 1 respuesta; then
        if [[ "$respuesta" == "q" ]]; then
            echo -e "\nDesconectando..."
            break
        fi
    fi

    num=$((num + 1))
done