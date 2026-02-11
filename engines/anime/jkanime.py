import requests, re, sys
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": "https://jkanime.net/"
}

def buscar_anime(nombre):
    # JKAnime usa minúsculas y guiones bajos en su buscador URL
    query = nombre.replace(" ", "_").lower()
    url = f"https://jkanime.net/buscar/{query}/1/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        resultados = []
        for item in soup.select(".anime__item"):
            link_tag = item.select_one("a")
            title_tag = item.select_one("h5")
            if link_tag and title_tag:
                resultados.append((title_tag.text.strip(), link_tag['href']))
        return resultados
    except: return []

def obtener_episodios(url_anime):
    try:
        res = requests.get(url_anime, headers=HEADERS, timeout=10)
        last_cap = re.search(r'var last_cap = (.*?);', res.text).group(1)
        return [f"Episodio {i}" for i in range(int(last_cap), 0, -1)]
    except: return ["Episodio 1"]

def obtener_video_server(url_anime, num):
    url_cap = f"{url_anime.rstrip('/')}/{num}/"
    try:
        res = requests.get(url_cap, headers=HEADERS, timeout=10)
        # Extraer links directos de los iframes
        scripts = re.findall(r"video\[\d+\] = '<iframe.*?src=\"(.*?)\"", res.text)
        links = [s if s.startswith('http') else 'https:' + s for s in scripts]
        # Filtrar servidores conocidos que funcionan bien en mpv
        validos = [l for l in links if any(srv in l for srv in ["ok.ru", "stwish", "mixdrop", "voex", "mega"])]
        return " ".join(validos)
    except: return None

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(1)
    accion, dato = sys.argv[1], sys.argv[2]
    if accion == "buscar":
        for t, l in buscar_anime(dato): print(f"{t} --> {l}")
    elif accion == "caps":
        for e in obtener_episodios(dato): print(e)
    elif accion == "ver":
        print(obtener_video_server(dato, sys.argv[3]))