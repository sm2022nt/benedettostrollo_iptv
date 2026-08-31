import os
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.broppalone.com/",
}

HOME_URL = "https://www.broppalone.com/"


def get_match_links():
    """Estrae tutti i link delle partite dalla home page."""
    match_urls = []
    try:
        response = requests.get(HOME_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if "/notizia/" in href:
                if not href.startswith("http"):
                    href = "https://www.broppalone.com" + href

                title = href.split("/notizia/")[-1].strip("/").replace("-", " ").title()

                item = {"name": title, "url": href}
                if item not in match_urls:
                    match_urls.append(item)

    except Exception as e:
        print(f"Errore lettura home page: {e}")

    return match_urls


def extract_stream_url(page_url):
    """Analizza la pagina della notizia e gli iframe collegati per trovare il file .m3u8."""
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        res = session.get(page_url, timeout=10)
        content = res.text

        # 1. Ricerca diretta nel codice sorgente della pagina
        matches = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', content)
        if matches:
            return matches[0]

        # 2. Analisi degli iframe presenti nella pagina
        soup = BeautifulSoup(content, "html.parser")
        iframes = soup.find_all("iframe")

        for iframe in iframes:
            src = iframe.get("src") or iframe.get("data-src")
            if not src:
                continue

            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = "https://www.broppalone.com" + src

            try:
                # Ispeziona l'iframe interno al player
                iframe_res = session.get(src, timeout=10)
                iframe_text = iframe_res.text

                # Cerca link m3u8 dentro l'iframe
                m3u8_inside = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', iframe_text)
                if m3u8_inside:
                    return m3u8_inside[0]

                # Cerca variabili JavaScript con lo stream (es. source: '...', file: '...')
                js_matches = re.findall(r'(?:file|source|src)\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']', iframe_text)
                if js_matches:
                    return js_matches[0]

            except Exception:
                continue

    except Exception as e:
        print(f"Errore estrazione da {page_url}: {e}")

    return None


def build_playlist():
    playlist = ["#EXTM3U"]
    matches = get_match_links()
    print(f"Partite trovate in home page: {len(matches)}")

    for match in matches:
        print(f"Elaborazione: {match['name']}...")
        stream_url = extract_stream_url(match["url"])

        if stream_url:
            playlist.append(f'#EXTINF:-1 group-title="Eventi Live",{match["name"]}')
            playlist.append(stream_url)
            print(f"  -> Link estratto: {stream_url}")
        else:
            print("  -> NESSUN FLUSSO TROVATO (Player dinamico o protetto)")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(playlist) + "\n")


if __name__ == "__main__":
    build_playlist()
