import feedparser
import json
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Configurazione
OUTPUT_FILE = 'news_data.json'

# Keyword per categorizzare le notizie
KEYWORDS_NDRANGHETA = [
    'ndrangheta', 'ndranghet', 'mafia calabra', 'cosca',
    'reggio calabria', 'vibo valentia', 'catanzaro', 'cosenza',
    'calabria', 'aspromonte', 'locride', 'ionio calabra',
    'arresto', 'arresti', 'ordinanza', 'custodia cautelare',
    'scarcerazione', 'scarcerato', 'fine pena',
    'cocaina', 'hashish', 'droga', 'traffico internazionale',
    'omicidio', 'agguato', 'spari', 'killer', 'attentato',
    'auto in fiamme', 'incendio', 'gambizzato',
    'sequestro', 'blitz', 'operazione', 'maxi-operazione',
    'ros', 'carabinieri', 'guardia di finanza', 'dda',
    'procura', 'antimafia'
]

KEYWORDS_HIGH_PRIORITY = [
    'scarcerato', 'fine pena', 'boss fuori', 'libertà',
    'omicidio', 'agguato', 'spari', 'killer', 'attentato',
    'auto in fiamme', 'gambizzato',
    'maxi-sequestro', 'tonnellate', 'maxi-operazione', 'blitz'
]

# Fonti RSS
RSS_FEEDS = [
    # Antimafia Duemila
    'https://www.antimafiaduemila.com/feed/rss',
    
    # ANSA Calabria
    'https://www.ansa.it/sito/notizie/cronaca/cronaca_rss.xml',
    
    # Altri feed locali (da aggiungere)
    # 'https://www.lacnews24.it/feed/',
    # 'https://www.quotidianodelsud.it/feed/',
]

def is_calabria_related(text):
    """Verifica se la notizia riguarda la Calabria o la 'Ndrangheta"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in KEYWORDS_NDRANGHETA)

def calculate_priority(text):
    """Calcola la priorità della notizia basata sulle keyword"""
    text_lower = text.lower()
    score = 0
    for keyword in KEYWORDS_HIGH_PRIORITY:
        if keyword in text_lower:
            score += 10
    return score

def categorize_news(text):
    """Categorizza la notizia"""
    text_lower = text.lower()
    categories = []
    
    if any(word in text_lower for word in ['arresto', 'arresti', 'ordinanza', 'custodia']):
        categories.append('arresti')
    if any(word in text_lower for word in ['scarcerazione', 'scarcerato', 'fine pena', 'libertà']):
        categories.append('scarcerazioni')
    if any(word in text_lower for word in ['cocaina', 'hashish', 'droga', 'sequestro']):
        categories.append('droga')
    if any(word in text_lower for word in ['omicidio', 'agguato', 'spari', 'killer', 'attentato', 'incendio']):
        categories.append('sangue')
    
    return categories if categories else ['generico']

def fetch_news_from_rss():
    """Scarica le notizie dai feed RSS"""
    all_news = []
    
    for feed_url in RSS_FEEDS:
        try:
            print(f"Leggendo: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:20]:  # Prime 20 notizie per feed
                title = entry.get('title', '')
                summary = entry.get('summary', entry.get('description', ''))
                link = entry.get('link', '')
                published = entry.get('published', '')
                
                # Rimuovi tag HTML dal summary
                summary = re.sub('<[^<]+?>', '', summary)
                
                # Verifica se riguarda la Calabria/'Ndrangheta
                full_text = f"{title} {summary}"
                
                if is_calabria_related(full_text):
                    priority = calculate_priority(full_text)
                    categories = categorize_news(full_text)
                    
                    news_item = {
                        'title': title,
                        'summary': summary[:300] + '...' if len(summary) > 300 else summary,
                        'link': link,
                        'published': published,
                        'source': urlparse(feed_url).netloc,
                        'priority': priority,
                        'categories': categories,
                        'is_ndrangheta': True,
                        '
