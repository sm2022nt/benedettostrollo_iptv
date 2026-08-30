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

# ⚠️ INSERISCI QUI I LINK REALI DELLE PAGINE WEB DA MONITORARE
TARGET_URLS = [
    {"name": "Player 1", "url": "https://sito-esempio-1.com/diretta"},
    {"name": "Player 2", "url": "https://sito-esempio-2.com/diretta"},
]


def extract_stream_url(page_url):
    try:
        response = requests.get(page_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        content = response.text

        # 1. Cerca link .m3u8 o .ts diretti nel codice sorgente
        m3u8_matches = re.findall(
            r'https?://[^\s\'"]+\.(?:m3u8|ts)[^\s\'"]*', content
        )
        if m3u8_matches:
            return m3u8_matches[0]

        # 2. Cerca all'interno di eventuali iframe
        soup = BeautifulSoup(content, "html.parser")
        for iframe in soup.find_all("iframe"):
            iframe_src = iframe.get("src")
            if iframe_src:
                if not iframe_src.startswith("http"):
                    base_url = "/".join(page_url.split("/")[:3])
                    iframe_src = base_url + iframe_src

                iframe_res = requests.get(
                    iframe_src, headers=HEADERS, timeout=10
                )
                stream_matches = re.findall(
                    r'https?://[^\s\'"]+\.(?:m3u8|ts)[^\s\'"]*', iframe_res.text
                )
                if stream_matches:
                    return stream_matches[0]

    except Exception as e:
        print(f"Errore su {page_url}: {e}")

    return None


def build_playlist():
    playlist = ["#EXTM3U"]

    for target in TARGET_URLS:
        stream_url = extract_stream_url(target["url"])
        if stream_url:
            playlist.append(
                f'#EXTINF:-1 group-title="Eventi Live",{target["name"]}'
            )
            playlist.append(stream_url)
            print(f"OK: {target['name']} -> {stream_url}")
        else:
            print(f"ERRORE: Nessun flusso trovato per {target['name']}")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(playlist) + "\n")


if __name__ == "__main__":
    build_playlist()
