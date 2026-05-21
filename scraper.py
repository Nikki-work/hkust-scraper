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
        print(f"❌ Failed to reach web server: {e}")
        return None

def clean_text(text):
    if not text:
        return ""
    return " ".join(text.strip().split())

def process_carousel_block(soup_container, source_label):
    """Processes slider cards exactly as they appear in the visual carousel row."""
    extracted_items = []
    
    # Locate all slider/carousel slide cards inside the container block
    cards = soup_container.find_all(class_=lambda x: x and any(k in x.lower() for k in ['slide', 'views-row', 'card-item']))
    
    for card in cards:
        # 1. Parse the Headline text link
        headline_elem = card.find(["a", "h3", "h4"], class_=lambda x: x is None or 'title' in x.lower())
        if not headline_elem:
            continue
            
        headline = clean_text(headline_elem.text)
        
        # Guardrails: Skip navigation elements or useless metadata labels
        if len(headline) < 12 or any(word in headline.lower() for word in ["view all", "read more", "more news"]):
            continue

        # 2. Extract and rebuild the structural Month + Day calendar graphic block
        date_str = ""
        date_container = card.find(class_=lambda x: x and any(k in x.lower() for k in ['date', 'calendar', 'time']))
        
        if date_container:
            # Look for sub-elements representing distinct month/day elements inside the badge
            month_elems = date_container.find_all(class_=lambda x: x and 'month' in x.lower())
            day_elems = date_container.find_all(class_=lambda x: x and 'day' in x.lower())
            
            if month_elems and day_elems:
                months = [clean_text(m.text) for m in month_elems]
                days = [clean_text(d.text) for d in day_elems]
                
                if len(months) == 2 and len(days) == 2: # Date ranges like JUN 17 - JUN 19
                    date_str = f"{months[0]} {days[0]} - {months[1]} {days[1]}"
                elif len(months) == 1 and len(days) == 1: # Single dates like FEB 10
                    date_str = f"{months[0]} {days[0]}"
                else:
                    date_str = clean_text(date_container.text)
            else:
                date_str = clean_text(date_container.text)
        
        # Clean up any leftover code formatting inside the date field
        date_str = clean_text(date_str)
        if not date_str:
            date_str = "Recent Featured"

        extracted_items.append({
            "Source": source_label,
            "Date": date_str,
            "Headline": headline
        })
        
    return extracted_items

def scrape_huma_slider():
    print("🎯 Extracting HUMA Carousel Row...")
    html = fetch_html("https://huma.hkust.edu.hk/")
    if not html: return []
    
    soup = BeautifulSoup(html, "html.parser")
    data = []
    
    # Isolate the specific homepage slider rows for News and Events blocks
    panels = soup.find_all("div", class_=lambda x: x and any(k in x.lower() for k in ['block-views', 'view-news', 'view-events']))
    for panel in panels:
        data.extend(process_carousel_block(panel, "HUMA (Home Slider)"))
        
    return data

def scrape_sosc_slider():
    print("🎯 Extracting SOSC Carousel Row...")
    html = fetch_html("https://sosc.hkust.edu.hk/")
    if not html: return []
    
    soup = BeautifulSoup(html, "html.parser")
    data = []
    
    # Isolate the frontpage component modules where events/news blocks live
    panels = soup.find_all("div", class_=lambda x: x and any(k in x.lower() for k in ['block-views', 'news', 'event']))
    for panel in panels:
        data.extend(process_carousel_block(panel, "SOSC (Home Slider)"))
        
    return data

def main():
    print("🚀 Launching Precision Slider Scraper Engine...")
    existing_headlines = set()
    
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_headlines.add(clean_text(row["Headline"]))
                
    # Gather cards strictly displaying on active desktop slider components
    live_cards = scrape_huma_slider() + scrape_sosc_slider()
    
    items_to_add = []
    for item in live_cards:
        if item["Headline"] not in existing_headlines:
            items_to_add.append(item)
            existing_headlines.add(item["Headline"]) # Local cross-check blocking
            
    print(f"📊 Run analysis complete. Found {len(items_to_add)} unique new slide announcements.")
    
    if items_to_add:
        file_exists = os.path.exists(CSV_FILE)
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Source", "Date", "Headline", "Scraped At"]) 
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for item in items_to_add:
                writer.writerow([item["Source"], item["Date"], item["Headline"], timestamp])
        print("✅ news.csv beautifully updated.")
    else:
        print("🤷‍♂️ Everything is synchronized. No changes found in sliders today.")

if __name__ == "__main__":
    main()
