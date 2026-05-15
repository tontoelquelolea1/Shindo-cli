import requests
import re
import sys
import json
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
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
    except: return []

def obtener_episodios(url_anime):
    try:
        response = requests.get(url_anime, headers=HEADERS, timeout=10)
        script_datos = re.search(r'var episodes = \[(.*?)\];', response.text)
        if script_datos:
            lista_raw = script_datos.group(1)
            episodios = re.findall(r'\[(\d+),\d+\]', lista_raw)
            return episodios 
        return []
    except: return []

def obtener_video_server(url_anime, numero_capitulo):
    slug = url_anime.split("/")[-1]
    url_capitulo = f"https://www3.animeflv.net/ver/{slug}-{numero_capitulo}"
    
    try:
        response = requests.get(url_capitulo, headers=HEADERS, timeout=10)
        match = re.search(r'var videos = (\{.*?\});', response.text)
        if match:
            datos = json.loads(match.group(1))
            servidores_list = datos.get("SUB", [])
            
            enlaces = []
            # Prioridad: stape y sbs suelen ser los más estables
            # Lista negra: eliminamos los que dieron error en tu log (yourupload, mailru, etc)
            blacklist = ['yourupload', 'mailru', 'mega']
            
            # Ordenar: primero stape/sbs, luego el resto, ignorar blacklist
            servidores_list.sort(key=lambda x: x.get('server', '').lower() not in ['stape', 'sbs'])

            for s in servidores_list:
                server_name = s.get('server', '').lower()
                if any(bad in server_name for bad in blacklist):
                    continue
                
                if 'code' in s:
                    link = s['code'].replace('\\/', '/')
                    if link.startswith('//'): link = 'https:' + link
                    enlaces.append(link)
            
            return " ".join(enlaces)
    except: pass
    return None

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(1)
    accion = sys.argv[1]
    dato_principal = sys.argv[2]

    if accion == "buscar":
        res = buscar_anime(dato_principal)
        for titulo, link in res: print(f"{titulo} --> {link}")
    elif accion == "caps":
        caps = obtener_episodios(dato_principal)
        for c in caps: print(f"Episodio {c}")
    elif accion == "ver":
        if len(sys.argv) == 4:
            links = obtener_video_server(dato_principal, sys.argv[3])
            if links: print(links)