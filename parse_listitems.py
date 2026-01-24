#!/usr/bin/env python3
"""
Parse listitem elements from the saved HTML page source.
Extract their attributes, positions, and other metadata.
"""

import json
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime


def parse_listitems(html_file):
    """Parse listitem elements from HTML file."""
    print(f"📄 Reading HTML file: {html_file}")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all elements with role="listitem"
    listitems = soup.find_all(attrs={'role': 'listitem'})
    
    print(f"\n✅ Found {len(listitems)} listitem elements\n")
    
    # Parse each listitem
    items_data = []
    for idx, item in enumerate(listitems, 1):
        print(f"🔍 Listitem #{idx}")
        
        # Extract style attributes
        style_attr = item.get('style', '')
        style_dict = {}
        if style_attr:
            # Parse style string into dict
            for prop in style_attr.split(';'):
                if ':' in prop:
                    key, value = prop.split(':', 1)
                    style_dict[key.strip()] = value.strip()
        
        # Extract position from style
        position_info = {
            'width': style_dict.get('width', 'N/A'),
            'top': style_dict.get('top', 'N/A'),
            'left': style_dict.get('left', 'N/A'),
            'position': style_dict.get('position', 'N/A'),
        }
        
        # Find images and videos within this listitem
        images = item.find_all('img')
        videos = item.find_all('video')
        
        image_urls = [img.get('src', '') for img in images if img.get('src')]
        video_urls = [vid.get('src', '') for vid in videos if vid.get('src')]
        alt_texts = [img.get('alt', '') for img in images if img.get('alt')]
        
        # Extract other metadata
        item_data = {
            'index': idx,
            'position': position_info,
            'images': image_urls,
            'videos': video_urls,
            'alt_texts': alt_texts,
            'num_images': len(images),
            'num_videos': len(videos),
        }
        
        items_data.append(item_data)
        
        # Print summary for this item
        print(f"  Position: {position_info}")
        print(f"  Images: {len(images)}, Videos: {len(videos)}")
        if alt_texts:
            print(f"  Alt text: {alt_texts[0]}")
        print()
    
    return items_data


def save_parsed_data(data, output_file=None):
    """Save parsed data to JSON file."""
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'parsed_listitems_{timestamp}.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved parsed data to: {output_file}")
    return output_file


def analyze_positions(items_data):
    """Analyze the positions of listitems."""
    print("\n📊 Position Analysis:")
    print("-" * 60)
    
    # Extract position values
    positions = []
    for item in items_data:
        pos = item['position']
        try:
            left = int(pos['left'].replace('px', ''))
            top = int(pos['top'].replace('px', ''))
            width = int(pos['width'].replace('px', ''))
            positions.append((item['index'], left, top, width))
        except (ValueError, AttributeError):
            continue
    
    if not positions:
        print("⚠️ No valid position data found")
        return
    
    # Sort by left position (columns)
    positions.sort(key=lambda x: (x[1], x[2]))  # Sort by left, then top
    
    print(f"\nItems sorted by position (left, top):")
    for idx, left, top, width in positions:
        print(f"  Item #{idx:2d}: left={left:4d}px, top={top:3d}px, width={width:3d}px")
    
    # Detect columns
    unique_lefts = sorted(set(pos[1] for pos in positions))
    print(f"\n📏 Detected {len(unique_lefts)} columns:")
    for col_num, left_val in enumerate(unique_lefts, 1):
        items_in_col = [p for p in positions if p[1] == left_val]
        print(f"  Column {col_num} (left={left_val}px): {len(items_in_col)} items")


def main():
    # Find the most recent HTML file
    html_files = sorted(Path('.').glob('page_source_*.html'))
    
    if not html_files:
        print("❌ No page_source_*.html files found!")
        print("Run fetch_page_source.py first.")
        return
    
    html_file = html_files[-1]  # Use most recent
    print(f"🎯 Using HTML file: {html_file}\n")
    
    # Parse listitems
    items_data = parse_listitems(html_file)
    
    # Save to JSON
    output_file = save_parsed_data(items_data)
    
    # Analyze positions
    analyze_positions(items_data)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Successfully parsed {len(items_data)} listitem elements")
    print(f"📁 Data saved to: {output_file}")
    print("=" * 60)


if __name__ == '__main__':
    main()
