import requests, json, re, time, os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://www.1377x.to"
HEADERS = {"User-Agent": "Mozilla/5.0"}
PLACEHOLDER = "https://via.placeholder.com/300x450/333/fff?text=No+Image"

def clean(text): return re.sub(r'\s+', ' ', text).strip() if text else ""

def scrape_page(page):
    url = f"{BASE}/cat/Movies/{page}/"
    print(f"Scraping {url}")
    res = requests.get(url, headers=HEADERS, timeout=15)
    if res.status_code != 200: return []
    soup = BeautifulSoup(res.text, 'html.parser')
    rows = soup.select("table.table-list tbody tr")
    movies = []

    for row in rows:
        try:
            a = row.select_one("td.coll-1 a[href^='/torrent/']")
            if not a: continue
            title = clean(a.text)
            detail_url = urljoin(BASE, a['href'])
            size = clean(row.select_one("td.coll-4.size").text)
            seeds = clean(row.select_one("td.coll-2.seeds").text)

            time.sleep(0.8)
            dres = requests.get(detail_url, headers=HEADERS, timeout=15)
            if dres.status_code != 200: continue
            dsoup = BeautifulSoup(dres.text, 'html.parser')

           
            poster = ""
            img = dsoup.select_one(".torrent-image img")
            if img and img.get("src"):
                src = img["src"].strip()
                if src.startswith("http"):
                    poster = src
                elif src.startswith("/"):
                    poster = BASE + src
                else:
                    poster = ""
            
            if not poster or "missing" in poster.lower():
                poster = PLACEHOLDER

         
            imdb = ""
            link = dsoup.find("a", href=re.compile(r"imdb\.com/title/tt\d+"))
            if link:
                match = re.search(r"tt\d+", link["href"])
                if match: imdb = match.group()

            
            stream = ""
            iframe = dsoup.select_one(".plays iframe")
            if iframe and iframe.get("src"): stream = iframe["src"]

            magnet = ""
            mag = dsoup.find("a", href=re.compile(r"magnet:\?"))
            if mag: magnet = mag["href"]

            movies.append({
                "title": title,
                "poster": poster,      
                "size": size,
                "seeds": int(seeds) if seeds.isdigit() else 0,
                "imdb": imdb,
                "stream": stream,
                "magnet": magnet
            })
        except Exception as e:
            print("Row error:", e)
            continue
    return movies

if __name__ == "__main__":
    page = int(os.getenv("SCRAPER_PAGE", "1"))
    data = scrape_page(page)

    all_data = {}
    if os.path.exists("../data_1337x.json"):
        try:
            with open("../data_1337x.json", "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    loaded = json.loads(content)
                    if isinstance(loaded, dict):
                        all_data = loaded
        except: pass

    all_data[str(page)] = data

    with open("../data_1337x.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(data)} movies for page {page}")