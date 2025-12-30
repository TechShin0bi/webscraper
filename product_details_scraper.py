import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import ijson
import os
from tempfile import NamedTemporaryFile
from decimal import Decimal
import numbers

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
                img_url = img_url.replace('-small.', '-big.')  # Try to get larger version
                if img_url not in details['extra_images']:
                    details['extra_images'].append(img_url)
        
        # Extract images from data-image attributes
        for img in soup.find_all(attrs={"data-image": True}):
            img_filename = img['data-image']
            if img_filename:
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

def process_products(input_file, output_file, batch_size=10):
    """Process products in batches to handle large files efficiently"""
    processed_count = 0
    batch = []
    temp_file = f"{output_file}.tmp"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f, \
             open(temp_file, 'w', encoding='utf-8') as out_f:
            
            out_f.write('[\n')
            first_item = True
            
            # Custom JSON encoder to handle Decimal objects
            class DecimalEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, Decimal):
                        return float(obj)
                    if isinstance(obj, numbers.Number):
                        return float(obj)
                    return super().default(obj)

            # Use ijson to parse the file efficiently
            for product in ijson.items(f, 'item'):
                if 'extra_images' in product:
                    # Write existing product as is
                    if not first_item:
                        out_f.write(',\n')
                    json.dump(product, out_f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
                    first_item = False
                    continue
                
                # Process product that needs extra_images
                print(f"\nProcessing product: {product.get('name')}")
                print(f"URL: {product.get('url')}")
                
                details = extract_additional_details(product.get('url'))
                if details:
                    product.update(details)
                    print(f"  - Found {len(details.get('extra_images', []))} additional images")
                    if details.get('product_code'):
                        print(f"  - Product code: {details['product_code']}")
                
                # Add to batch
                if not first_item:
                    out_f.write(',\n')
                json.dump(product, out_f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
                first_item = False
                
                processed_count += 1
                if processed_count % batch_size == 0:
                    print(f"\nProcessed {processed_count} products...")
                    out_f.flush()
                    os.fsync(out_f.fileno())
                
                # Be nice to the server
                time.sleep(1)
            
            out_f.write('\n]')
        
        # Replace original file with the updated one
        os.replace(temp_file, output_file)
        print(f"\nProcessing complete! Updated {processed_count} products in {output_file}")
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise

def main():
    input_file = 'products.json'
    output_file = 'products_enhanced.json'
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return
    
    print(f"Starting to process products from {input_file}")
    process_products(input_file, output_file)

if __name__ == "__main__":
    main()