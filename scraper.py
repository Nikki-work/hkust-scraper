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

def scrape_huma(content_type):
    # content_type will be either 'news' or 'events'
    url = f"https://huma.hkust.edu.hk/{content_type}"
    print(f"Scraping HUMA {content_type.upper()}...")
    html = fetch_html(url)
    if not html: return []
    
    soup = BeautifulSoup(html, "html.parser")
    data = []
    
    # Target elements inside list structures
    items = soup.find_all("li") or soup.find_all("div", class_=lambda x: x and 'item' in x.lower())
    
    for item in items:
        headline_elem = item.find(["a", "h2", "h3", "h4"])
        date_elem = item.find(["span", "div", "time", "p"], class_=lambda x: x and 'date' in x.lower())
        
        if headline_elem:
            headline = headline_elem.text.strip()
            # Clean out excessive spacing that tricks the duplicate checker
            headline = " ".join(headline.split())
            
            # Skip short links or navigation structural items
            if len(headline) < 10 or "load more" in headline.lower():
                continue
                
            date = date_elem.text.strip() if date_elem else "See Link/No Date"
            date = " ".join(date.split())
            
            data.append({
                "Source": f"HUMA ({content_type.capitalize()})",
                "Date": date,
                "Headline": headline
            })
            
    return data

def scrape_sosc():
    # SOSC hosts its news and events on different endpoints; we target the main index layout
    url = "https://sosc.hkust.edu.hk/"
    print("Scraping SOSC News & Events Home Panel...")
    html = fetch_html(url)
    if not html: return []
    
    soup = BeautifulSoup(html, "html.parser")
    data = []
    
    # 1. Pull SOSC News Items
    news_items = soup.find_all("div", class_=lambda x: x and 'news' in x.lower())
    for item in news_items:
        link = item.find("a")
        if link and len(link.text.strip()) > 10:
            headline = " ".join(link.text.strip().split())
            data.append({"Source": "SOSC (News)", "Date": "Recent News", "Headline": headline})
            
    # 2. Pull SOSC Upcoming Events
    event_items = soup.find_all("li") or soup.find_all("div", class_=lambda x: x and 'event' in x.lower())
    for item in event_items:
        # Check for textual clues to ensure it's an event box item
        text_content = item.text.strip()
        if any(keyword in text_content.lower() for keyword in ["presentation", "seminar", "lecture", "talk", "symposium"]):
            lines = [line.strip() for line in text_content.split("\n") if line.strip()]
            if len(lines) >= 2:
                # Typically date elements sit at the beginning of event structural components
                date = lines[0]
                headline = " ".join(lines[1:])
                if len(headline) > 12:
                    data.append({"Source": "SOSC (Event)", "Date": date, "Headline": headline})
                    
    return data

def main():
    print("🚀 Running Upgraded Deep-Scraper System...")
    existing_headlines = set()
    
    # Read existing database entries to build a clean tracking record
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Sanitize the check string to prevent spacing duplication bugs
                clean_head = " ".join(row["Headline"].split())
                existing_headlines.add(clean_head)
                
    # Gather everything across both news channels and event streams
    fresh_scrapes = scrape_huma("news") + scrape_huma("events") + scrape_sosc()
    
    # Filter using our strict tracking set
    items_to_add = []
    for item in fresh_scrapes:
        if item["Headline"] not in existing_headlines:
            items_to_add.append(item)
            existing_headlines.add(item["Headline"]) # Instantly track to catch inline duplicates
            
    print(f"📊 Filter Complete. Identified {len(items_to_add)} truly unique new posts.")
    
    if items_to_add:
        file_exists = os.path.exists(CSV_FILE)
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Source", "Date", "Headline", "Scraped At"]) 
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for item in items_to_add:
                writer.writerow([item["Source"], item["Date"], item["Headline"], timestamp])
        print("✅ news.csv has been updated cleanly.")
    else:
        print("🤷‍♂️ No new updates found across either division today.")

if __name__ == "__main__":
    main()
