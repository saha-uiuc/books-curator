#!/usr/bin/env python3
"""
Scraper for Pulitzer Prize for Fiction from Wikipedia.
Captures winners (with publisher info) and finalists from 2000-2025.
"""

import logging
import re
from typing import List, Dict
from .scraper_utils import fetch_page, clean_text, extract_year_from_text, validate_data, save_to_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def scrape_pulitzer_prize(output_file: str = None) -> List[Dict]:
    """Scrape Pulitzer Prize winners and finalists from Wikipedia"""
    url = "https://en.wikipedia.org/wiki/Pulitzer_Prize_for_Fiction"
    logger.info(f"Fetching Pulitzer Prize data from {url}")
    
    soup = fetch_page(url)
    if not soup:
        return []
    
    awards_data = []
    
    tables = soup.find_all('table', {'class': 'wikitable'})
    # Use second table (1980-present)
    target_table = tables[1] if len(tables) > 1 else tables[0] if tables else None
    
    if not target_table:
        logger.warning("Could not find Pulitzer Prize table")
        return []
    
    rows = target_table.find_all('tr')
    
    for row in rows[1:]:
        cells = row.find_all(['td', 'th'])
        if len(cells) < 4:
            continue
            
        year_text = clean_text(cells[0].get_text())
        year = extract_year_from_text(year_text)
        
        if not year or year < 2000 or year > 2025:
            continue
        
        # Cell 2: Author, Cell 3: Title, Cell 4: Publisher, Cell 7: Finalists
        author_cell = cells[2] if len(cells) > 2 else None
        title_cell = cells[3] if len(cells) > 3 else None
        publisher_cell = cells[4] if len(cells) > 4 else None
        
        if author_cell and title_cell:
            author = clean_text(author_cell.get_text())
            author = re.sub(r'\s*\([^)]*\)\s*', '', author).strip()  # Remove birth year
            
            title_elem = title_cell.find('i')
            title = clean_text(title_elem.get_text()) if title_elem else clean_text(title_cell.get_text())
            
            publisher = ""
            if publisher_cell:
                publisher = clean_text(publisher_cell.get_text())
                publisher = re.sub(r'\s*\(\d{4}\)\s*', '', publisher).strip()
            
            if 'not awarded' in title.lower() or 'no award' in title.lower():
                logger.info(f"Pulitzer Prize not awarded in {year}")
                continue
            
            if title and author:
                winner_entry = {
                    'Year': year,
                    'Award': 'Pulitzer Prize for Fiction',
                    'Status': 'Winner',
                    'Title': title,
                    'Author': author
                }
                if publisher:
                    winner_entry['Publisher'] = publisher
                
                awards_data.append(winner_entry)
                logger.info(f"Found Pulitzer winner for {year}: {title} by {author} ({publisher})")
        
        # Parse finalists
        if len(cells) > 7:
            finalists_cell = cells[7]
            list_items = finalists_cell.find_all('li')
            
            if list_items:
                for item in list_items:
                    author_link = item.find('a')
                    if not author_link:
                        continue
                    
                    fin_author = clean_text(author_link.get_text())
                    
                    title_elem = item.find('i')
                    if title_elem:
                        fin_title = clean_text(title_elem.get_text())
                    else:
                        text = item.get_text()
                        if ', ' in text:
                            parts = text.split(', ', 1)
                            fin_title = clean_text(parts[1])
                        else:
                            continue
                    
                    if fin_author and fin_title:
                        finalist_entry = {
                            'Year': year,
                            'Award': 'Pulitzer Prize for Fiction',
                            'Status': 'Finalist',
                            'Title': fin_title,
                            'Author': fin_author
                        }
                        awards_data.append(finalist_entry)
                        logger.info(f"Found Pulitzer finalist for {year}: {fin_title} by {fin_author}")
            else:
                # Fallback for non-list format
                author_links = finalists_cell.find_all('a')
                
                for author_link in author_links:
                    fin_author = clean_text(author_link.get_text())
                    parent = author_link.parent
                    title_elem = parent.find('i') if parent else None
                    
                    if title_elem:
                        fin_title = clean_text(title_elem.get_text())
                    else:
                        full_text = parent.get_text() if parent else ""
                        if ', ' in full_text:
                            author_pos = full_text.find(fin_author)
                            if author_pos != -1:
                                after_author = full_text[author_pos + len(fin_author):]
                                if after_author.startswith(','):
                                    title_match = re.match(r',\s*([^A-Z]+(?:[A-Z][^A-Z]*)?)', after_author)
                                    if title_match:
                                        fin_title = clean_text(title_match.group(1))
                                    else:
                                        continue
                                else:
                                    continue
                            else:
                                continue
                        else:
                            continue
                    
                    if fin_author and fin_title and len(fin_title) > 3:
                        finalist_entry = {
                            'Year': year,
                            'Award': 'Pulitzer Prize for Fiction',
                            'Status': 'Finalist',
                            'Title': fin_title,
                            'Author': fin_author
                        }
                        awards_data.append(finalist_entry)
                        logger.info(f"Found Pulitzer finalist for {year}: {fin_title} by {fin_author}")
    
    validated_data = validate_data(awards_data)
    logger.info(f"Found {len(validated_data)} Pulitzer Prize entries")
    
    if output_file:
        save_to_json(validated_data, output_file, backup=True)
    
    return validated_data


if __name__ == "__main__":
    # Run as standalone script
    output_path = "/Users/sosaha/Library/CloudStorage/OneDrive-Adobe/Acrobat Desktop 2019-2022/Documents/cs598-fdc-literary-awards/data/pulitzer_prize.json"
    data = scrape_pulitzer_prize(output_path)
    print(f"\nCollected {len(data)} Pulitzer Prize entries")
    
    # Show summary
    winners = sum(1 for x in data if x['Status'] == 'Winner')
    finalists = len(data) - winners
    print(f"Winners: {winners}, Finalists: {finalists}")

