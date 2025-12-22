import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7",
    "Accept-Language": "en-US,en;q=0.9"
}

def scrape_models(brand_url):
    """Scrape models from a single brand URL"""
    print(f"Scraping models from: {brand_url}")
    try:
        response = requests.get(brand_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        models = []
        processed_ids = set()  # To avoid duplicates

        # Find all model rows
        rows = soup.find_all('tr', class_='viewCatList__row')
        print(rows)
        if not rows:
            print(f"No model rows found in {brand_url}")
            return []

        for row in rows:
            # Find all model cells in the row
            cells = row.find_all('td', class_=lambda x: x and 'oxcell' in x)
            
            for cell in cells:
                try:
                    # Find the model link
                    link = cell.find('a', class_='PBLink')
                    if not link or not link.get('href'):
                        continue
                    
                    # Get model URL
                    model_url = urljoin(brand_url, link['href'])
                    
                    # Extract model ID from URL
                    model_id = None
                    if 'PBCATID=' in model_url:
                        model_id = model_url.split('PBCATID=')[1].split('&')[0]
                    
                    # Skip if we've already processed this model
                    if model_id in processed_ids:
                        continue
                    processed_ids.add(model_id)
                    
                    # Get model name
                    name_tag = cell.find('h3', class_='PBCatSubTitle')
                    model_name = name_tag.get_text(strip=True) if name_tag else 'Unnamed Model'
                    
                    # Get model image
                    img_tag = cell.find('img', class_='imgcat')
                    img_url = urljoin(brand_url, img_tag['src']) if img_tag and 'src' in img_tag.attrs else None
                    
                    models.append({
                        "id": model_id,
                        "name": model_name,
                        "url": model_url,
                        "image_url": img_url
                    })
                    
                except Exception as e:
                    print(f"Error processing model: {str(e)}")
                    continue
        
        return models
        
    except Exception as e:
        print(f"Error scraping {brand_url}: {str(e)}")
        return []

def main():
    # Load brands from the existing JSON file
    with open('brands.json', 'r', encoding='utf-8') as f:
        brands = json.load(f)
    
    all_models = []
    
    for brand in brands:
        print(f"\nProcessing brand: {brand['name']}")
        models = scrape_models(brand['url'])
        
        # Add brand reference to each model
        for model in models:
            model['brand_id'] = brand['id']
            model['brand_name'] = brand['name']
        
        all_models.extend(models)
        print(f"Found {len(models)} models for {brand['name']}")
        
        # Be nice to the server
        time.sleep(2)
    
    # Save all models to a new JSON file
    with open('brand_models.json', 'w', encoding='utf-8') as f:
        json.dump(all_models, f, ensure_ascii=False, indent=2)
    
    print(f"\nScraping complete! Found {len(all_models)} models across {len(brands)} brands.")
    print("Results saved to brand_models.json")

if __name__ == "__main__":
    main()
