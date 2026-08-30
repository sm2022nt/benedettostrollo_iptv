import re
import requests
from bs4 import BeautifulSoup

HOME_URL = "https://www.broppalone.com"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def estrai_stream():
    try:
        # 1. Visita la Home Page
        print("Accesso alla Home Page...")
        res_home = requests.get(HOME_URL, headers=headers, timeout=15)
        soup_home = BeautifulSoup(res_home.text, 'html.parser')

        # 2. Trova il link al primo articolo della partita
        articolo_url = None
        for a in soup_home.find_all('a', href=True):
            href = a['href']
            if "/notizia/" in href:
                articolo_url = href if href.startswith("http") else HOME_URL + href
                break

        if not articolo_url:
            print("Nessun articolo '/notizia/' trovato, uso la home.")
            articolo_url = HOME_URL

        print(f"Notizia individuata: {articolo_url}")

        # 3. Visita la pagina dell'articolo
        res_articolo = requests.get(articolo_url, headers=headers, timeout=15)
        soup_articolo = BeautifulSoup(res_articolo.text, 'html.parser')

        # 4. Individua tutti gli iframe (Player 1, 2, 3, 4)
        iframes = soup_articolo.find_all('iframe')
        stream_links = []

        # Cerca i link .m3u8 anche direttamente nella pagina principale
        match_main = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', res_articolo.text)
        for link in match_main:
            if link not in stream_links:
                stream_links.append(link)

        # Scansiona ciascun iframe per trovare il link di ogni player
        for idx, iframe in enumerate(iframes, start=1):
            src = iframe.get('src')
            if src:
                iframe_url = src if src.startswith("http") else ("https:" + src if src.startswith("//") else HOME_URL + src)
                try:
                    print(f"Scansione Player {idx}: {iframe_url}")
                    res_iframe = requests.get(iframe_url, headers=headers, timeout=10)
                    matches = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', res_iframe.text)
                    for link in matches:
                        if link not in stream_links:
                            stream_links.append(link)
                except Exception as e:
                    print(f"Impossibile aprire l'iframe {idx}: {e}")

        # 5. Genera il file della playlist M3U con tutti i flussi trovati
        if stream_links:
            m3u_content = "#EXTM3U\n"
            for index, stream_url in enumerate(stream_links, start=1):
                m3u_content += f'#EXTINF:-1 tvg-logo="" group-title="Calcio Live", Partita del Giorno - Player {index}\n{stream_url}\n'
                print(f"Trovato Player {index}: {stream_url}")

            with open("playlist.m3u", "w", encoding="utf-8") as f:
                f.write(m3u_content)
            print(f"\nSUCCESS: Salvati {len(stream_links)} player nella playlist IPTV.")
        else:
            print("ERRORE: Nessun flusso .m3u8 individuato nei player.")

    except Exception as e:
        print(f"Si è verificato un errore: {e}")

if __name__ == "__main__":
    estrai_stream()
