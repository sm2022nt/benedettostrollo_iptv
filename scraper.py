import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://broppalone.com"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_latest_match_url():
    try:
        res = requests.get(BASE_URL, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if BASE_URL in href or href.startswith('/'):
                if any(x in href for x in ['/calcio/', '/partita/', '/live/', '/stream/']):
                    return href if href.startswith('http') else BASE_URL + href
        return BASE_URL
    except Exception as e:
        return BASE_URL

def main():
    match_url = get_latest_match_url()
    stream_links = []
    
    try:
        res = requests.get(match_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        iframes = soup.find_all('iframe')
        for idx, iframe in enumerate(iframes[:4], start=1):
            src = iframe.get('src')
            if src:
                stream_links.append((f"Player {idx}", src))
    except Exception as e:
        print(f"Errore: {e}")

    # Scrittura M3U compatibile con Smarters / webOS
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U x-tvg-url=\"\"\n")
        if stream_links:
            for name, url in stream_links:
                f.write(f'#EXTINF:-1 tvg-id="{name}" tvg-name="{name}" group-title="Eventi Live",{name}\n')
                f.write(f"{url}\n")
        else:
            f.write('#EXTINF:-1 tvg-id="P1" tvg-name="Player 1" group-title="Eventi Live",Player 1\n')
            f.write("https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8\n")
            f.write('#EXTINF:-1 tvg-id="P2" tvg-name="Player 2" group-title="Eventi Live",Player 2\n')
            f.write("https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8\n")

if __name__ == "__main__":
    main()
