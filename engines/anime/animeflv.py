import requests
import re
import sys
import json
from bs4 import BeautifulSoup

# Headers para evitar que la web nos bloquee
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www3.animeflv.net/"
}

def buscar_anime(nombre):
    busqueda = nombre.replace(" ", "+")
    url = f"https://www3.animeflv.net/browse?q={busqueda}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        resultados = []
        for articulo in soup.find_all('article', class_='Anime'):
            titulo = articulo.find('h3', class_='Title').text
            link = "https://www3.animeflv.net" + articulo.find('a')['href']
            resultados.append((titulo, link))
        return resultados
    except Exception:
        return []

def obtener_episodios(url_anime):
    try:
        response = requests.get(url_anime, headers=HEADERS, timeout=10)
        # Extraemos el array de episodios oculto en el JavaScript de la página
        script_datos = re.search(r'var episodes = \[(.*?)\];', response.text)
        if script_datos:
            lista_raw = script_datos.group(1)
            episodios = re.findall(r'\[(\d+),\d+\]', lista_raw)
            return episodios 
        return []
    except Exception:
        return []

def obtener_video_server(url_anime, numero_capitulo):
    # Construimos la URL del capítulo: nombre-del-anime-numero
    slug = url_anime.split("/")[-1]
    url_capitulo = f"https://www3.animeflv.net/ver/{slug}-{numero_capitulo}"
    
    try:
        response = requests.get(url_capitulo, headers=HEADERS, timeout=10)
        # Buscamos el objeto JSON 'videos' que contiene todos los servidores
        match = re.search(r'var videos = (\{.*?\});', response.text)
        if match:
            datos = json.loads(match.group(1))
            # Obtenemos la lista de servidores subtitulados
            servidores_list = datos.get("SUB", [])
            
            # Extraemos solo los enlaces (campo 'code')
            enlaces = []
            for s in servidores_list:
                if 'code' in s:
                    # Algunos links vienen sin protocolo, los arreglamos
                    link = s['code']
                    if link.startswith('//'):
                        link = 'https:' + link
                    enlaces.append(link)
            
            # Devolvemos todos los links separados por un espacio para el bucle for de Bash
            return " ".join(enlaces)
    except Exception:
        pass
    return None

# --- LÓGICA DE COMANDOS ---
if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)

    accion = sys.argv[1]
    dato_principal = sys.argv[2]

    if accion == "buscar":
        res = buscar_anime(dato_principal)
        for titulo, link in res:
            print(f"{titulo} --> {link}")

    elif accion == "caps":
        caps = obtener_episodios(dato_principal)
        for c in caps:
            print(f"Episodio {c}")

    elif accion == "ver":
        # Aquí necesitamos el tercer argumento (número de capítulo)
        if len(sys.argv) == 4:
            num_cap = sys.argv[3]
            links = obtener_video_server(dato_principal, num_cap)
            if links:
                print(links)