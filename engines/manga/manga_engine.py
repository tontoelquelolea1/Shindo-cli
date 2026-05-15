import sys
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://lectortmo.vip/"
}

# ==================== MOTOR NOVELCOOL ====================
def buscar_novelcool(query):
    query_busqueda = query.replace(" ", "+")
    url = f"https://es.novelcool.com/search?name={query_busqueda}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.find_all("div", class_="book-item")
        for item in items:
            link_tag = item.find("a", class_="book-name")
            if not link_tag:
                link_tag = item.select_one(".book-name a") or item.find("a")
            if link_tag:
                title = link_tag.get_text(strip=True)
                link = link_tag['href']
                if link.startswith("/"):
                    link = f"https://es.novelcool.com{link}"
                months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                clean_title = title
                for m in months:
                    if m in clean_title:
                        clean_title = clean_title.split(m)[0].strip()
                print(f"{clean_title} [NovelCool] --> {link}")
    except Exception:
        pass

def caps_novelcool(url_manga):
    try:
        res = requests.get(url_manga, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        container = soup.find("div", class_="chapter-list-item") or soup.find("div", class_="chapter-item-list")
        links = container.find_all("a") if container else [a for a in soup.find_all("a", href=True) if "/chapter/" in a['href']]
        vistos = set()
        for l in reversed(links):
            title = l.get_text(strip=True)
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            for m in months:
                if m in title:
                    title = title.split(m)[0].strip()
            href = l['href']
            if href.startswith("/"):
                href = f"https://es.novelcool.com{href}"
            if href not in vistos:
                print(f"{title} --> {href}")
                vistos.add(href)
    except Exception as e:
        print(f"Error en capítulos NovelCool: {e}")

# ==================== MOTOR LECTOR TMO ====================
def buscar_tmo(query):
    query_busqueda = query.replace(" ", "+")
    url = f"https://lectortmo.vip/search?query={query_busqueda}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Filtramos directamente por los contenedores de las tarjetas de manga
        items = soup.find_all("div", class_="manga-box") or soup.select(".manga-card, .book-item, .manga-item")
        if not items:
            # Fallback secundario si cambian las clases: buscar enlaces con /manga/ estrictos
            items = [a for a in soup.find_all("a", href=True) if "/manga/" in a['href'] and not "/manga-type/" in a['href']]
            
        vistos = set()
        for item in items:
            link_tag = item if item.name == "a" else item.find("a", href=True)
            if link_tag and "/manga/" in link_tag['href'] and not "/manga-type/" in link_tag['href']:
                link = link_tag['href']
                if link.startswith("/"):
                    link = f"https://lectortmo.vip{link}"
                
                # Intentamos obtener un título limpio
                title_tag = link_tag.find(["h3", "h4", "h2", "span"]) or link_tag
                title = title_tag.get_text(strip=True)
                
                # Evitar arrastrar paginaciones o textos genéricos de la interfaz
                if link not in vistos and title and len(title) > 2 and "capítulo" not in title.lower():
                    print(f"{title} [LectorTMO] --> {link}")
                    vistos.add(link)
    except Exception:
        pass

def caps_tmo(url_manga):
    try:
        res = requests.get(url_manga, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Encontrar los enlaces que lleven la estructura de capítulos de TMO
        links = [a for a in soup.find_all("a", href=True) if "/chapter/" in a['href'] or "/viewer/" in a['href']]
        vistos = set()
        
        # Los listamos a la inversa para que el primer capítulo aparezca arriba
        for l in reversed(links):
            href = l['href']
            if href.startswith("/"):
                href = f"https://lectortmo.vip{href}"
            
            title = l.get_text(strip=True)
            if not title:
                # Si el tag está vacío, sacamos el número del propio enlace
                title = f"Capítulo {href.split('/')[-1]}"
                
            if href not in vistos:
                print(f"{title} --> {href}")
                vistos.add(href)
    except Exception as e:
        print(f"Error en capítulos LectorTMO: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python manga_engine.py [buscar|caps] [query|url]")
        sys.exit(1)

    action = sys.argv[1]
    param = sys.argv[2]

    if action == "buscar":
        buscar_novelcool(param)
        buscar_tmo(param)
    elif action == "caps":
        if "novelcool.com" in param:
            caps_novelcool(param)
        elif "lectortmo.vip" in param:
            caps_tmo(param)
