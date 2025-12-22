import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7",
    "Accept-Language": "en-US,en;q=0.9"
}

def clean_price(price_str):
    """Extract numeric price from string"""
    if not price_str:
        return None
    # Remove non-numeric characters except comma and dot
    clean = re.sub(r'[^\d,.]', '', price_str)
    # Replace comma with dot and convert to float
    return float(clean.replace(',', '.'))

def scrape_products(category_url):
    """Scrape products from a single category URL"""
    print(f"Scraping products from: {category_url}")
    try:
        response = requests.get(category_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        products = []
        
        # Find all product rows
        rows = soup.find_all('tr', class_='viewItemList__row')
        if not rows:
            print(f"No product rows found in {category_url}")
            return []
            
        for row in rows:
            try:
                # Get product cells
                cells = row.find_all('td', class_=lambda x: x and 'oxcell' in x and 'oxfirstcol' not in x)
                
                for cell in cells:
                    # Skip empty cells
                    if not cell.get('data-pdt-id'):
                        continue
                        
                    # Extract product ID and SKU
                    product_id = cell.get('data-pdt-id')
                    sku = cell.get('data-pdt-sku', '').strip()
                    
                    # Get product name
                    name_tag = cell.find('h3', class_='PBMainTxt')
                    name = name_tag.get_text(strip=True) if name_tag else 'Unnamed Product'
                    
                    # Get product URL
                    link_tag = cell.find('a', class_='PBLink')
                    product_url = urljoin(category_url, link_tag['href']) if link_tag and 'href' in link_tag.attrs else None
                    
                    # Get image URL
                    img_tag = cell.find('img', class_='imgthumbnail')
                    img_url = urljoin(category_url, img_tag['src']) if img_tag and 'src' in img_tag.attrs else None
                    
                    # Get price
                    price_tag = cell.find('span', class_='PBSalesPrice')
                    price = clean_price(price_tag.get_text(strip=True)) if price_tag else None
                    
                    # Get stock status
                    stock_status = 'Out of Stock'
                    stock_qty = 0
                    stock_tag = cell.find('span', class_='PBMsgInStock')
                    if stock_tag:
                        stock_status = stock_tag.get_text(strip=True)
                        # Try to extract quantity if available
                        qty_match = re.search(r'\((\d+)', cell.text)
                        if qty_match:
                            stock_qty = int(qty_match.group(1))
                    
                    products.append({
                        'id': product_id,
                        'sku': sku,
                        'name': name,
                        'url': product_url,
                        'image_url': img_url,
                        'price': price,
                        'stock_status': stock_status,
                        'stock_quantity': stock_qty
                    })
                    
            except Exception as e:
                print(f"Error processing product: {str(e)}")
                continue
                
        return products
        
    except Exception as e:
        print(f"Error scraping {category_url}: {str(e)}")
        return []

def main():
    # Load categories from the existing JSON file
    try:
        with open('model_categories.json', 'r', encoding='utf-8') as f:
            categories = json.load(f)
    except FileNotFoundError:
        print("Error: model_categories.json not found. Please run category_scraper.py first.")
        return
    
    all_products = []
    total_categories = len(categories)
    
    for i, category in enumerate(categories, 1):
        print(f"\nProcessing category {i}/{total_categories}: {category['name']} (Model: {category['model_name']})")
        products = scrape_products(category['url'])
        
        # Add category, model, and brand references to each product
        for product in products:
            product.update({
                'category_id': category['id'],
                'category_name': category['name'],
                'model_id': category['model_id'],
                'model_name': category['model_name'],
                'brand_id': category['brand_id'],
                'brand_name': category['brand_name']
            })
        
        all_products.extend(products)
        print(f"Found {len(products)} products in {category['name']}")
        
        # Be nice to the server
        time.sleep(2)
    
    # Save all products to a new JSON file
    output_file = 'products.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    
    print(f"\nScraping complete! Found {len(all_products)} products across {total_categories} categories.")
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
