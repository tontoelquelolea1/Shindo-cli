import sys
import requests
import re
from bs4 import BeautifulSoup

# Mantenemos la sesión para que el servidor nos reconozca
session = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": "https://jkanime.net/",
}

def buscar(nombre):
    query = nombre.replace(" ", "-").lower()
    url_directa = f"https://jkanime.net/{query}/"
    try:
        res = session.get(url_directa, headers=HEADERS, timeout=10)
        if res.status_code == 200 and "página no encontrada" not in res.text.lower():
            soup = BeautifulSoup(res.text, 'html.parser')
            titulo = soup.find('h1').text.strip() if soup.find('h1') else nombre.capitalize()
            print(f"{titulo} --> {url_directa}")
            return
        
        # Si falla el directo, usamos el buscador
        url_search = f"https://jkanime.net/buscar/{nombre.replace(' ', '%20')}/1/"
        res = session.get(url_search, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        for anime in soup.select(".anime__item"):
            t = anime.select_one("h5").text.strip()
            l = anime.select_one("a")['href']
            print(f"{t} --> {l}")
    except:
        pass

def caps(url_anime):
    try:
        res = session.get(url_anime, headers=HEADERS, timeout=10)
        html = res.text
        total = 1

        # 1. RASTREO POR VARIABLE JS (Varios nombres posibles)
        match = re.search(r'(?:last_cap|max_cap|total_episodes|capitulos)\s*[:=]\s*["\']?(\d+)["\']?', html, re.I)
        
        if match:
            total = int(match.group(1))
        else:
            # 2. RASTREO POR ENLACES (Buscamos el número más alto en la página)
            # JKAnime pone enlaces como /naruto/1/, /naruto/220/
            slug = url_anime.strip('/').split('/')[-1]
            pattern = re.compile(rf'/{slug}/(\d+)/')
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', href=pattern)
            
            numeros = []
            for l in links:
                m = pattern.search(l['href'])
                if m: numeros.append(int(m.group(1)))
            
            if numeros:
                total = max(numeros)
            else:
                # 3. RASTREO POR TEXTO (Ej: "Episodios: 220")
                match_text = re.search(r'(?:Episodios|Capítulos)\s*:\s*(\d+)', soup.get_text(), re.I)
                if match_text:
                    total = int(match_text.group(1))

        # Generamos la lista del último al primero
        for i in range(total, 0, -1):
            print(f"Episodio {i}")
    except Exception:
        print("Episodio 1")

def ver(url_anime, cap):
    url_video = f"{url_anime.rstrip('/')}/{cap}/"
    try:
        res = session.get(url_video, headers=HEADERS, timeout=10)
        links = re.findall(r"video\[\d+\] = '<iframe.*?src=\"(.*?)\"", res.text)
        for link in links:
            clean_link = link if link.startswith('http') else 'https:' + link
            if all(x not in clean_link for x in ["um2.php", "ads", "facebook"]):
                print(clean_link)
    except:
        pass

if __name__ == "__main__":
    if len(sys.argv) < 3: exit()
    accion = sys.argv[1]
    if accion == "buscar": buscar(sys.argv[2])
    elif accion == "caps": caps(sys.argv[2])
    elif accion == "ver": ver(sys.argv[2], sys.argv[3])