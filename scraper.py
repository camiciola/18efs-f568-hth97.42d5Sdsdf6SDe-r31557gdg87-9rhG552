import json
import re
from datetime import datetime
from urllib.parse import urlparse
import urllib.request
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

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

def scrape_antimafiaduemila():
    try:
        print("Scraping antimafiaduemila.com...")
        url = "https://www.antimafiaduemila.com"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read()
        soup = BeautifulSoup(html, "html.parser")
        news_list = []
        articles = soup.find_all("article", limit=30)
        if not articles:
            articles = soup.find_all("div", class_=re.compile("article|post|news"), limit=30)
        for article in articles:
            title_elem = article.find(["h1", "h2", "h3", "a"])
            link_elem = article.find("a", href=True)
            desc_elem = article.find(["p", "div"], class_=re.compile("summary|excerpt|description"))
            if title_elem:
                title = title_elem.get_text(strip=True)
                link = ""
                if link_elem:
                    link = link_elem["href"]
                    if not link.startswith("http"):
                        link = url + link
                description = ""
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                if title and len(title) > 10:
                    news_list.append({
                        "title": title,
                        "link": link,
                        "description": description,
                        "pub_date": "",
                        "source": "antimafiaduemila.com"
                    })
        print("Trovate " + str(len(news_list)) + " notizie da antimafiaduemila.com")
        return news_list
    except Exception as e:
        print("Errore scraping antimafiaduemila.com: " + str(e))
        return []

def scrape_ansa():
    try:
        print("Scraping ANSA...")
        url = "https://www.ansa.it/sito/notizie/cronaca/cronaca.shtml"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read()
        soup = BeautifulSoup(html, "html.parser")
        news_list = []
        articles = soup.find_all(["h3", "h4"], limit=30)
        for article in articles:
            link_elem = article.find("a", href=True)
            if link_elem:
                title = link_elem.get_text(strip=True)
                link = link_elem["href"]
                if not link.startswith("http"):
                    link = "https://www.ansa.it" + link
                if title and len(title) > 10:
                    news_list.append({
                        "title": title,
                        "link": link,
                        "description": "",
                        "pub_date": "",
                        "source": "ansa.it"
                    })
        print("Trovate " + str(len(news_list)) + " notizie da ANSA")
        return news_list
    except Exception as e:
        print("Errore scraping ANSA: " + str(e))
        return []

def fetch_all_news():
    all_news = []
    all_news.extend(scrape_antimafiaduemila())
    all_news.extend(scrape_ansa())
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
