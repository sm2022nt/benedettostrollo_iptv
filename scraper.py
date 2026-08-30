import os
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

HOME_URL = "https://www.broppalone.com/"


def get_match_links():
    """Scansiona la home page e trova tutti i link delle notizie/partite."""
    match_urls = []
    try:
        response = requests.get(HOME_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Cerca tutti i link che contengono '/notizia/'
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if "/notizia/" in href:
                # Gestisce URL relativi o completi
                if not href.startswith("http"):
                    href = "https://www.broppalone.com" + href
                
                # Pulisce il nome della partita dallo slug dell'URL
                title = href.split("/notizia/")[-1].replace("/", "").replace("-", " ").title()
                
                if {"name": title, "url": href} not in match_urls:
                    match_urls.append({"name": title, "url": href})

    except Exception as e:
        print(f"Errore durante la scansione della Home: {e}")

    return match_urls


def extract_stream_url(page_url):
    """Cerca il flusso .m3u8 o .ts dentro la pagina della partita o negli iframe."""
    try:
        response = requests.get(page_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        content = response.text

        # 1. Cerca link diretti .m3u8 o .ts
        m3u8_matches = re.findall(
            r'https?://[^\s\'"]+\.(?:m3u8|ts)[^\s\'"]*', content
        )
        if m3u8_matches:
            return m3u8_matches[0]

        # 2. Cerca negli iframe incorporati
        soup = BeautifulSoup(content, "html.parser")
        for iframe in soup.find_all("iframe"):
            iframe_src = iframe.get("src")
            if iframe_src:
                if not iframe_src.startswith("http"):
                    iframe_src = "https://www.broppalone.com" + iframe_src

                iframe_res = requests.get(iframe_src, headers=HEADERS, timeout=10)
                stream_matches = re.findall(
                    r'https?://[^\s\'"]+\.(?:m3u8|ts)[^\s\'"]*', iframe_res.text
                )
                if stream_matches:
                    return stream_matches[0]

    except Exception as e:
        print(f"Errore durante l'estrazione su {page_url}: {e}")

    return None


def build_playlist():
    playlist = ["#EXTM3U"]
    matches = get_match_links()
    print(f"Trovate {len(matches)} partite in home page.")

    for match in matches:
        print(f"Analizzo: {match['name']}...")
        stream_url = extract_stream_url(match["url"])
        
        if stream_url:
            playlist.append(f'#EXTINF:-1 group-title="Eventi Live",{match["name"]}')
            playlist.append(stream_url)
            print(f"  -> OK: {stream_url}")
        else:
            print(f"  -> KO: Nessun flusso trovato.")

    # Salva il file M3U
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(playlist) + "\n")

    print("File playlist.m3u generato con successo!")


if __name__ == "__main__":
    build_playlist()
