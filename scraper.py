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
        print(f"❌ Failed to fetch {url}: {e}")
        return None

def scrape_shss():
    print("Scraping SHSS News...")
    html = fetch_html("https://shss.hkust.edu.hk/news")
    if not html: return []
    
    soup = BeautifulSoup(html, "html.parser")
    data = []
    try:
        # Fallback selectors check broad classes to protect against layout changes
        articles = soup.find_all("div", class_=lambda x: x and 'news' in x.lower()) or soup.find_all("article")
        for article in articles:
            headline_elem = article.find(["h2", "h3", "h4", "a"])
            date_elem = article.find(["span", "div", "p", "time"], class_=lambda x: x and 'date' in x.lower())
            
            headline = headline_elem.text.strip() if headline_elem else None
            date = date_elem.text.strip() if date_elem else "No Date Provided"
            
            if headline and len(headline) > 3:
                data.append({"Source": "SHSS", "Date": date, "Headline": headline})
    except Exception as e:
        print(f"⚠️ Error parsing SHSS layout: {e}")
    return data

def scrape_sosc():
    print("Scraping SOSC Events & News...")
    html = fetch_html("https://sosc.hkust.edu.hk/news")
    if not html: return []
    
    soup = BeautifulSoup(html, "html.parser")
    data = []
    try:
        articles = soup.find_all("article") or soup.find_all("div", class_=lambda x: x and 'item' in x.lower())
        for article in articles:
            headline_elem = article.find(["h2", "h3", "h4", "a"])
            date_elem = article.find(["span", "div", "p", "time"], class_=lambda x: x and 'date' in x.lower())
            
            headline = headline_elem.text.strip() if headline_elem else None
            date = date_elem.text.strip() if date_elem else "No Date Provided"
            
            if headline and len(headline) > 3:
                data.append({"Source": "SOSC", "Date": date, "Headline": headline})
    except Exception as e:
        print(f"⚠️ Error parsing SOSC layout: {e}")
    return data

def main():
    print("🚀 Starting HKUST Cloud Scraper...")
    existing_headlines = set()
    
    # Read existing database entries to prevent row duplication
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_headlines.add(row["Headline"])
                
    # Gather live details
    fresh_scrapes = scrape_shss() + scrape_sosc()
    
    # Filter out updates we already captured previously
    items_to_add = [item for item in fresh_scrapes if item["Headline"] not in existing_headlines]
    print(f"📊 Identified {len(items_to_add)} NEW items to commit.")
    
    if items_to_add:
        file_exists = os.path.exists(CSV_FILE)
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Source", "Date", "Headline", "Scraped At"]) 
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for item in items_to_add:
                writer.writerow([item["Source"], item["Date"], item["Headline"], timestamp])
        print("✅ Local news.csv updated.")
    else:
        print("🤷‍♂️ Everything is up-to-date. No new events found today.")

if __name__ == "__main__":
    main()
