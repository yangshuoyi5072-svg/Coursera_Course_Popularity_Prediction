import json
import os

def merge_images():
    # File paths
    batch_file = 'coursera_all_products_batch.json'
    target_file = 'Courses_Advanced_Features.json'
    output_file = 'Courses_With_Images.json'
    
    print(f"Loading {batch_file}...")
    with open(batch_file, 'r', encoding='utf-8') as f:
        batch_data = json.load(f)
        
    # Create mapping: course URL -> imageUrl
    # The batch file has a 'products' list
    products = batch_data.get('products', [])
    url_to_image = {}
    
    print(f"Indexing {len(products)} products from batch file...")
    for p in products:
        url = p.get('url')
        img = p.get('imageUrl')
        if url and img:
            url_to_image[url] = img
            
    print(f"Found {len(url_to_image)} images.")
    
    print(f"Loading {target_file}...")
    with open(target_file, 'r', encoding='utf-8') as f:
        target_data = json.load(f)
        
    courses = target_data['courses']
    matched_count = 0
    
    print(f"Merging images into {len(courses)} courses...")
    for c in courses:
        url = c.get('url')
        if url in url_to_image:
            c['cover_image_url'] = url_to_image[url]
            matched_count += 1
            
    print(f"Successfully added images to {matched_count} courses ({matched_count/len(courses)*100:.1f}%).")
    
    # Save result
    target_data['courses'] = courses
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(target_data, f, indent=2, ensure_ascii=False)
        
    print(f"Saved merged dataset to {output_file}")

if __name__ == "__main__":
    merge_images()
