import json
import re
from datetime import datetime
from urllib.parse import urlparse
import urllib.request
import xml.etree.ElementTree as ET

OUTPUT_FILE = "news_data.json"

KEYWORDS_NDRANGHETA = [
    "ndrangheta", "ndranghet", "mafia", "cosca",
    "reggio calabria", "vibo valentia", "catanzaro", "cosenza",
    "calabria", "aspromonte", "locride",
    "arresto", "arresti", "ordinanza", "custodia cautelare",
    "scarcerazione", "scarcerato", "fine pena",
    "cocaina", "hashish", "droga",
    "omicidio", "agguato", "spari", "killer", "attentato",
    "auto in fiamme", "incendio", "gambizzato",
    "sequestro", "blitz", "operazione",
    "carabinieri", "guardia di finanza", "dda",
    "procura", "antimafia"
]

KEYWORDS_HIGH_PRIORITY = [
    "scarcerato", "fine pena", "boss fuori",
    "omicidio", "agguato", "spari", "killer", "attentato",
    "auto in fiamme", "gambizzato",
    "maxi-sequestro", "tonnellate", "maxi-operazione", "blitz"
]

RSS_FEEDS = [
    "https://www.antimafiaduemila.com/home/feed/rss",
    "https://www.ansa.it/sito/ansait_rss.xml",
    "https://rss.corriere.it/rss/home.xml",
    "https://www.repubblica.it/rss/homepage/rss2.0.xml"
]

def is_calabria_related(text):
    text_lower = text.lower()
    for keyword in KEYWORDS_NDRANGHETA:
        if keyword in text_lower:
            return True
    return False

def calculate_priority(text):
    text_lower = text.lower()
    score = 0
    for keyword in KEYWORDS_HIGH_PRIORITY:
        if keyword in text_lower:
            score = score + 10
    return score

def categorize_news(text):
    text_lower = text.lower()
    categories = []
    if "arresto" in text_lower or "arresti" in text_lower or "ordinanza" in text_lower:
        categories.append("arresti")
    if "scarcerazione" in text_lower or "scarcerato" in text_lower or "fine pena" in text_lower:
        categories.append("scarcerazioni")
    if "cocaina" in text_lower or "hashish" in text_lower or "droga" in text_lower:
        categories.append("droga")
    if "omicidio" in text_lower or "agguato" in text_lower or "spari" in text_lower or "attentato" in text_lower or "incendio" in text_lower:
        categories.append("sangue")
    if len(categories) == 0:
        categories.append("generico")
    return categories

def parse_rss_feed(feed_url):
    try:
        print("Leggendo: " + feed_url)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        req = urllib.request.Request(feed_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_content = response.read()
        root = ET.fromstring(xml_content)
        items = root.findall(".//item")
        if len(items) == 0:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        news_list = []
        count = 0
        for item in items[:30]:
            title_elem = item.find("title")
            link_elem = item.find("link")
            desc_elem = item.find("description")
            date_elem = item.find("pubDate")
            if title_elem is None:
                title_elem = item.find("{http://www.w3.org/2005/Atom}title")
            if link_elem is None:
                link_elem = item.find("{http://www.w3.org/2005/Atom}link")
            if desc_elem is None:
                desc_elem = item.find("{http://www.w3.org/2005/Atom}summary")
            if date_elem is None:
                date_elem = item.find("{http://www.w3.org/2005/Atom}published")
            title = title_elem.text if title_elem is not None else ""
            link = ""
            if link_elem is not None:
                if link_elem.text:
                    link = link_elem.text
                elif link_elem.get("href"):
                    link = link_elem.get("href")
            description = desc_elem.text if desc_elem is not None else ""
            pub_date = date_elem.text if date_elem is not None else ""
            if title:
                description = re.sub("<[^<]+?>", "", description)
                news_list.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "pub_date": pub_date,
                    "source": urlparse(feed_url).netloc
                })
                count = count + 1
        print("Trovate " + str(count) + " notizie da " + urlparse(feed_url).netloc)
        return news_list
    except Exception as e:
        print("Errore con " + feed_url + ": " + str(e))
        return []

def fetch_all_news():
    all_news = []
    for feed_url in RSS_FEEDS:
        news = parse_rss_feed(feed_url)
        for n in news:
            all_news.append(n)
    return all_news

def process_news(raw_news):
    processed = []
    for item in raw_news:
        full_text = item["title"] + " " + item["description"]
        is_ndrangheta = is_calabria_related(full_text)
        priority = calculate_priority(full_text) if is_ndrangheta else 0
        categories = categorize_news(full_text) if is_ndrangheta else ["generale"]
        summary = item["description"]
        if len(summary) > 300:
            summary = summary[:300] + "..."
        news_item = {
            "title": item["title"],
            "summary": summary,
            "link": item["link"],
            "published": item["pub_date"],
            "source": item["source"],
            "priority": priority,
            "categories": categories,
            "is_ndrangheta": is_ndrangheta,
            "is_high_priority": priority >= 20
        }
        processed.append(news_item)
    return processed

def save_to_json(news_data):
    news_data.sort(key=lambda x: x["priority"], reverse=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        data = {
            "last_update": datetime.now().isoformat(),
            "total_news": len(news_data),
            "news": news_data
        }
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Salvate " + str(len(news_data)) + " notizie")

def main():
    print("Avvio scraper notizie...")
    print("=" * 50)
    raw_news = fetch_all_news()
    print("Trovate " + str(len(raw_news)) + " notizie grezze")
    print("=" * 50)
    processed_news = process_news(raw_news)
    ndrangheta_count = sum(1 for n in processed_news if n["is_ndrangheta"])
    print("Notizie Ndrangheta/Calabria: " + str(ndrangheta_count))
    print("Notizie generali: " + str(len(processed_news) - ndrangheta_count))
    print("=" * 50)
    save_to_json(processed_news)
    print("Completato!")

if __name__ == "__main__":
    main()
