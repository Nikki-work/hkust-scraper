import csv
import os
import requests
from bs4 import BeautifulSoup
import datetime

CSV_FILE = "news.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Failed to reach {url}: {e}")
        return None

def clean_text(text):
    """Removes messy whitespace, tabs, and line breaks completely."""
    if not text:
        return ""
    return " ".join(text.strip().split())

def is_useless(headline):
    """Filters out interface buttons, structural navigation artifacts, and tiny fragments."""
    lower_h = headline.lower()
    banned_phrases = [
        "read more", "view all", "more events", "load more", "all news", 
        "quick links", "search", "menu", "sitemap", "contact us", "home",
        "humanities", "division of humanities"
    ]
    if len(headline) < 12: # True academic headlines are never this short
        return True
    return any(phrase in lower_h for phrase in banned_phrases)

def scrape_huma_homepage():
    print("Scraping HUMA Front Page Panels...")
    html = fetch_html("https://huma.hkust.edu.hk/")
    if not html: return []
    
    soup = BeautifulSoup(html, "html.parser")
    data = []
    
    # Target frontend grid layout panels used on the HUMA home landing container
    blocks = soup.find_all(["div", "article"], class_=lambda x: x and any(k in x.lower() for k in ['news', 'event', 'views-row', 'post']))
    
    for block in blocks:
        headline_elem = block.find(["a", "h2", "h3", "h4"])
        date_elem = block.find(["span", "div", "time", "p"], class_=lambda x: x and 'date' in x.lower())
        
        if headline_elem:
            headline = clean_text(headline_elem.text)
            if is_useless(headline):
                continue
                
            date = clean_text(date_elem.text) if date_elem else "Featured on HUMA Home"
            
            data.append({
                "Source": "HUMA (Home Panel)",
                "Date": date,
                "Headline": headline
            })
    return data

def scrape_sosc_homepage():
    print("Scraping SOSC Front Page Panels...")
    html = fetch_html("https://sosc.hkust.edu.hk/")
    if not html: return []
    
    soup = BeautifulSoup(html, "html.parser")
    data = []
    
    # Target columns and summary rows on the SOSC landing page
    containers = soup.find_all("div", class_=lambda x: x and any(k in x.lower() for k in ['panel', 'block', 'news', 'event', 'view-content']))
    
    for container in containers:
        items = container.find_all(["li", "div", "article"], class_=lambda x: x and any(k in x.lower() for k in ['item', 'row', 'title'])) or [container]
        for item in items:
            headline_elem = item.find(["a", "h2", "h3", "h4"]) or (item if item.name in ["h2", "h3", "h4", "a"] else None)
            date_elem = item.find(["span", "div", "p"], class_=lambda x: x and 'date' in x.lower())
            
            if headline_elem:
                headline = clean_text(headline_elem.text)
                if is_useless(headline):
                    continue
                
                date = clean_text(date_elem.text) if date_elem else "Featured on SOSC Home"
                
                data.append({
                    "Source": "SOSC (Home Panel)",
                    "Date": date,
                    "Headline": headline
                })
    return data

def main():
    print("🚀 Running Clean HUMA & SOSC Dashboard Scraper...")
    existing_headlines = set()
    
    # Read existing history records
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_headlines.add(clean_text(row["Headline"]))
                
    # Gather layout streams exclusively from active landing matrices
    front_page_items = scrape_huma_homepage() + scrape_sosc_homepage()
    
    # Filter and commit strictly unique entries
    items_to_add = []
    for item in front_page_items:
        if item["Headline"] not in existing_headlines:
            items_to_add.append(item)
            existing_headlines.add(item["Headline"]) # Local block loop check
            
    print(f"📊 Filter Complete. Found {len(items_to_add)} fresh updates across HUMA & SOSC.")
    
    if items_to_add:
        file_exists = os.path.exists(CSV_FILE)
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Source", "Date", "Headline", "Scraped At"]) 
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for item in items_to_add:
                writer.writerow([item["Source"], item["Date"], item["Headline"], timestamp])
        print("✅ news.csv cleanly updated.")
    else:
        print("🤷‍♂️ No new front-page items spotted on either dashboard today.")

if __name__ == "__main__":
    main()
