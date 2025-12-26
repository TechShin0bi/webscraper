import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7",
    "Accept-Language": "en-US,en;q=0.9"
}

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return None
    return ' '.join(text.split())

def extract_additional_details(product_url):
    """Extract additional details from product page"""
    try:
        response = requests.get(product_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        details = {
            'extra_images': [],
            'product_code': None,
            'description': None,
            'specifications': {}
        }
        
        # Extract product code
        code_span = soup.find('div', class_='PBItemSku')
        if code_span:
            code_text = code_span.get_text(strip=True)
            # Extract just the code part, e.g., "Code: 44 210 50ADLY" -> "44 210 50ADLY"
            code = code_text.replace('(Code:', '').replace(')', '').strip()
            details['product_code'] = code
        
        # Extract description if available
        desc_div = soup.find('div', class_='PBItemDescription')
        if desc_div:
            details['description'] = clean_text(desc_div.get_text())
        
        # Extract all images
        main_img_div = soup.find('div', class_='c-ox-imgzoom__main')
        if main_img_div:
            main_img = main_img_div.find('img')
            if main_img and 'src' in main_img.attrs:
                main_img_url = urljoin(product_url, main_img['src'])
                if main_img_url not in details['extra_images']:
                    details['extra_images'].append(main_img_url)
        
        # Extract additional images from the carousel
        thumbnails = soup.find_all('div', class_='mcs-item')
        for thumb in thumbnails:
            img_tag = thumb.find('img')
            if img_tag and 'src' in img_tag.attrs:
                img_url = urljoin(product_url, img_tag['src'])
                # Convert thumbnail URL to larger image URL if possible
                img_url = img_url.replace('-small.', '-big.')  # Try to get larger version
                if img_url not in details['extra_images']:
                    details['extra_images'].append(img_url)
        
        # Extract images from data-image attributes
        for img in soup.find_all(attrs={"data-image": True}):
            img_filename = img['data-image']
            if img_filename:
                # Construct the full image URL using the provided pattern
                full_img_url = f"https://www.pieces-quad-dole.fr/{img_filename}"
                if full_img_url not in details['extra_images']:
                    details['extra_images'].append(full_img_url)
        
        # Extract specifications if available
        spec_tables = soup.find_all('table', class_='PBSpecTbl')
        for table in spec_tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = clean_text(cells[0].get_text())
                    value = clean_text(cells[1].get_text())
                    if key and value:
                        details['specifications'][key] = value
        
        return details
        
    except Exception as e:
        print(f"Error extracting details from {product_url}: {str(e)}")
        return None



def main():
    # Load existing products
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
    except FileNotFoundError:
        print("Error: products.json not found. Please run product_scraper.py first.")
        return
    
    
    total_products = len(products)
    print(f"Found {total_products} products to process")
    
    # Process each product
    for i, product in enumerate(products, 1):
        if not product.get('url'):
            print(f"\nSkipping product {i}/{total_products}: No URL provided")
            continue
            
        print(f"\nProcessing product {i}/{total_products}: {product.get('name')}")
        print(f"URL: {product['url']}")
        
        # Get additional details
        details = extract_additional_details(product['url'])
        if details:
            # Update product with additional details
            product.update(details)
            print(f"  - Found {len(details.get('extra_images', []))} additional images")
            if details.get('product_code'):
                print(f"  - Product code: {details['product_code']}")
            if details.get('description'):
                print(f"  - Description: {details['description'][:100]}...")
        
        # Be nice to the server
        time.sleep(2)
        
        # Save progress every 10 products or on final product
        if i % 10 == 0 or i == total_products:
            with open('products_enhanced.json', 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            print(f"\nSaved progress after {i} products")
    
    print("\nProcessing complete! Enhanced product data saved to products_enhanced.json")

if __name__ == "__main__":
    main()