import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Accept-Language": "en-US,en;q=0.9"
}

def brand_scraper(url):
    print(f"Starting to scrape {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        
        # Print first 1000 characters of the response for debugging
        print("Response preview:", response.text[:1000])

        soup = BeautifulSoup(response.text, "html.parser")
        categories = []
        processed_ids = set()  # To track processed category IDs

        # Find all table rows with class viewCatList__row
        rows = soup.find_all('tr', class_='viewCatList__row')
        print(f"Found {len(rows)} category rows")
        
        if not rows:
            print("No category rows found")
            return []

        for row in rows:
            # Find all cells in this row
            cells = row.find_all('td')
            for cell in cells:
                try:
                    # Find the first link with class PBLink that has an href with PBCATID
                    link_tag = cell.find('a', class_='PBLink', href=lambda x: x and 'PBCATID=' in x)
                    if not link_tag or not link_tag.get('href'):
                        continue
                        
                    full_url = urljoin(url, link_tag['href'])
                    
                    # Extract category ID and name from URL parameters
                    parsed = urlparse(full_url)
                    params = parse_qs(parsed.query)
                    
                    cat_id = params.get('PBCATID', [''])[0] or 'N/A'
                    
                    # Skip if we've already processed this category
                    if cat_id in processed_ids:
                        continue
                        
                    processed_ids.add(cat_id)
                    
                    # Get category name from the h3 with class PBCatSubTitle
                    name_tag = cell.find('h3', class_='PBCatSubTitle')
                    cat_name = name_tag.get_text(strip=True) if name_tag else ''
                    
                    # If no name in h3, try to get it from URL params
                    if not cat_name:
                        cat_name = params.get('PBCATName', [''])[0].strip()
                    
                    # Find image URL - look for img tag with class imgcat
                    img_tag = cell.find('img', class_='imgcat')
                    img_url = urljoin(url, img_tag['src']) if img_tag and 'src' in img_tag.attrs else None
                    
                    # Only add if we have at least an ID or a name
                    if cat_id != 'N/A' or cat_name:
                        category = {
                            "id": cat_id,
                            "name": cat_name or f"Unnamed Category {len(categories) + 1}",
                            "url": full_url,
                            "image_url": img_url
                        }
                        categories.append(category)
                        
                except Exception as e:
                    print(f"Error processing category: {str(e)}")
                    continue
                    
        return categories
        
    except Exception as e:
        print(f"Error fetching or parsing page: {str(e)}")
        return []

if __name__ == "__main__":
    URL = "https://www.pieces-quad-dole.fr/PBSCCatalog.asp?CatID=4260325"
    
    try:
        print(f"Scraping categories from {URL}")
        data = brand_scraper(URL)
        
        if not data:
            print("No categories found!")
        else:
            print(f"\nSuccessfully scraped {len(data)} categories:")
            for item in data:
                print(f"- {item['name']} (ID: {item['id']})")
            
            # Save to JSON file
            output_file = 'brands.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\nCategories saved to {output_file}")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")