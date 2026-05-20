import csv
import os
import requests
from bs4 import BeautifulSoup
import datetime

CSV_FILE = "news.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return None

def scrape_shss():
    print("Scraping SHSS...")
    html = fetch_html("https://shss.hkust.edu.hk/news")
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    data = []
    try:
        articles = soup.find_all("div", class_=lambda x: x and 'news' in x.lower()) or soup.find_all("article")
        for article in articles:
            headline_elem = article.find(["h2", "h3", "h4", "a"])
            date_elem = article.find(["span", "div", "p", "time"], class_=lambda x: x and 'date' in x.lower())
            headline = headline_elem.text.strip() if headline_elem else None
            date = date_elem.text.strip() if date_elem else "No Date Provided"
            if headline and len(headline) > 3:
                data.append({"Source": "SHSS", "Date": date, "Headline": headline})
    except Exception as e:
        print(f"⚠️ Error parsing SHSS: {e}")
    return data

def scrape_sosc():
    print("Scraping SOSC...")
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
        print(f"⚠️ Error parsing SOSC: {e}")
    return data

def main():
    print("🚀 Starting HKUST Scraper...")
    existing_headlines = set()
    
    # 1. Read existing data so we don't write duplicates
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_headlines.add(row["Headline"])
                
    # 2. Scrape the websites
    new_data = scrape_shss() + scrape_sosc()
    
    # 3. Filter for items we haven't seen before
    items_to_add = [item for item in new_data if item["Headline"] not in existing_headlines]
    print(f"📊 Found {len(items_to_add)} NEW items to add.")
    
    # 4. Save directly to CSV
    if items_to_add:
        file_exists = os.path.exists(CSV_FILE)
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Source", "Date", "Headline", "Scraped At"]) 
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for item in items_to_add:
                writer.writerow([item["Source"], item["Date"], item["Headline"], timestamp])
        print("✅ Saved to news.csv!")

if __name__ == "__main__":
    main()
