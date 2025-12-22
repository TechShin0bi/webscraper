import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7",
    "Accept-Language": "en-US,en;q=0.9"
}

def scrape_categories(model_url):
    """Scrape categories from a single model URL"""
    print(f"Scraping categories from: {model_url}")
    try:
        response = requests.get(model_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        categories = []
        processed_ids = set()

        # Find all category rows
        rows = soup.find_all('tr', class_='viewCatList__row')
        if not rows:
            print(f"No category rows found in {model_url}")
            return []

        for row in rows:
            # Find all category cells in the row
            cells = row.find_all('td', class_=lambda x: x and 'oxcell' in x)
            
            for cell in cells:
                try:
                    # Find the category link
                    link = cell.find('a', class_='PBLink')
                    if not link or not link.get('href'):
                        continue
                    
                    # Get category URL
                    category_url = urljoin(model_url, link['href'])
                    
                    # Extract category ID from URL
                    category_id = None
                    if 'PBCATID=' in category_url:
                        category_id = category_url.split('PBCATID=')[1].split('&')[0]
                    
                    # Skip if we've already processed this category
                    if not category_id or category_id in processed_ids:
                        continue
                    processed_ids.add(category_id)
                    
                    # Get category name
                    name_tag = cell.find('h3', class_='PBCatSubTitle')
                    category_name = name_tag.get_text(strip=True) if name_tag else 'Unnamed Category'
                    
                    categories.append({
                        "id": category_id,
                        "name": category_name,
                        "url": category_url
                    })
                    
                except Exception as e:
                    print(f"Error processing category: {str(e)}")
                    continue
        
        return categories
        
    except Exception as e:
        print(f"Error scraping {model_url}: {str(e)}")
        return []

def main():
    # Load models from the existing JSON file
    try:
        with open('brand_models.json', 'r', encoding='utf-8') as f:
            models = json.load(f)
    except FileNotFoundError:
        print("Error: brand_models.json not found. Please run model_scraper.py first.")
        return
    
    all_categories = []
    total_models = len(models)
    
    for i, model in enumerate(models, 1):
        print(f"\nProcessing model {i}/{total_models}: {model['name']} ({model['brand_name']})")
        categories = scrape_categories(model['url'])
        
        # Add model reference to each category
        for category in categories:
            category['model_id'] = model['id']
            category['model_name'] = model['name']
            category['brand_id'] = model['brand_id']
            category['brand_name'] = model['brand_name']
        
        all_categories.extend(categories)
        print(f"Found {len(categories)} categories for {model['name']}")
        
        # Be nice to the server
        time.sleep(1)
    
    # Save all categories to a new JSON file
    with open('model_categories.json', 'w', encoding='utf-8') as f:
        json.dump(all_categories, f, ensure_ascii=False, indent=2)
    
    print(f"\nScraping complete! Found {len(all_categories)} categories across {total_models} models.")
    print("Results saved to model_categories.json")

if __name__ == "__main__":
    main()
