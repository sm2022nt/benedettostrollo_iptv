import os
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

HOME_URL = "https://www.broppalone.com/"

def get_match_links(page):
    """Raccoglie le pagine degli eventi dalla home."""
    match_urls = []
    try:
        page.goto(HOME_URL, wait_until="domcontentloaded", timeout=15000)
        content = page.content()
        soup = BeautifulSoup(content, "html.parser")

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
        print(f"Errore scansione Home Page: {e}")
    
    return match_urls

def extract_m3u8_stream(context, match_url):
    """Apre la pagina e intercetta il link .m3u8 al volo senza attendere il caricamento completo."""
    found_stream = []
    page = context.new_page()

    # Intercetta il link .m3u8 appena passa in rete
    def handle_request(request):
        url = request.url
        if ".m3u8" in url and not found_stream:
            print(f"  -> Trovato m3u8: {url}")
            found_stream.append(url)

    page.on("request", handle_request)

    try:
        # Usa 'domcontentloaded' invece di 'networkidle' per non bloccarsi
        page.goto(match_url, wait_until="domcontentloaded", timeout=12000)
        
        # Attende massimo 5 secondi per catturare lo streaming
        for _ in range(10):
            if found_stream:
                break
            page.wait_for_timeout(500)

    except Exception as e:
        print(f"Avviso durante caricamento {match_url}: {e}")
    finally:
        page.close()

    return found_stream[0] if found_stream else None

def main():
    playlist = ["#EXTM3U"]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        home_page = context.new_page()
        matches = get_match_links(home_page)
        home_page.close()

        print(f"Eventi trovati in Home Page: {len(matches)}")

        for match in matches:
            print(f"Analisi: {match['name']}...")
            stream_url = extract_m3u8_stream(context, match["url"])
            
            if stream_url:
                playlist.append(f'#EXTINF:-1 group-title="Eventi Live",{match["name"]}')
                playlist.append(stream_url)
            else:
                print("  -> Nessun flusso .m3u8 intercettato.")

        browser.close()

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(playlist) + "\n")

if __name__ == "__main__":
    main()
