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
        print(f"Errore recupero home: {e}")
        return BASE_URL

def extract_m3u8_from_url(url):
    try:
        res = requests.get(url, headers=headers, timeout=10)
        m3u8_matches = re.findall(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', res.text)
        if m3u8_matches:
            return m3u8_matches[0]
        
        soup = BeautifulSoup(res.text, 'html.parser')
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src')
            if src:
                if not src.startswith('http'):
                    src = 'https:' + src if src.startswith('//') else BASE_URL + src
                iframe_res = requests.get(src, headers=headers, timeout=10)
                sub_matches = re.findall(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', iframe_res.text)
                if sub_matches:
                    return sub_matches[0]
    except Exception as e:
        print(f"Errore estrazione da {url}: {e}")
    return None

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
                if not src.startswith('http'):
                    src = 'https:' + src if src.startswith('//') else BASE_URL + src
                link = extract_m3u8_from_url(src)
                if link:
                    stream_links.append((f"Player {idx}", link))
    except Exception as e:
        print(f"Errore main: {e}")

    # Scrittura formato M3U standard per Smarters / TiviMate
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        if stream_links:
            for name, url in stream_links:
                f.write(f'#EXTINF:-1 tvg-id="{name}" tvg-name="{name}" group-title="Eventi Live",{name}\n')
                f.write(f"{url}\n")
        else:
            # Canali fallback con formattazione completa
            f.write('#EXTINF:-1 tvg-id="player1" tvg-name="Player 1" group-title="Eventi Live",Player 1 (In attesa)\n')
            f.write("https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8\n")
            f.write('#EXTINF:-1 tvg-id="player2" tvg-name="Player 2" group-title="Eventi Live",Player 2 (In attesa)\n')
            f.write("https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8\n")

    print("Playlist generata con successo!")

if __name__ == "__main__":
    main()
