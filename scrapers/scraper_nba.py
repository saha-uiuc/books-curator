#!/usr/bin/env python3
"""
Scraper for National Book Award for Fiction from Wikipedia.
Captures winners and finalists from 2000-2025.
"""

import logging
from typing import List, Dict
from .scraper_utils import fetch_page, clean_text, extract_year_from_text, validate_data, save_to_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def scrape_national_book_award(output_file: str = None) -> List[Dict]:
    """Scrape National Book Award winners and finalists from Wikipedia"""
    url = "https://en.wikipedia.org/wiki/National_Book_Award_for_Fiction"
    logger.info(f"Fetching National Book Award data from {url}")
    
    soup = fetch_page(url)
    if not soup:
        return []
    
    awards_data = []
    
    tables = soup.find_all('table', {'class': 'wikitable'})
    
    for table in tables:
        rows = table.find_all('tr')
        
        if len(rows) > 0:
            headers = rows[0].find_all('th')
            header_text = ' '.join([h.get_text().strip() for h in headers]).lower()
            
            if 'year' not in header_text or 'author' not in header_text:
                continue
        
        current_year = None
        
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) == 0:
                continue
            
            first_cell_text = clean_text(cells[0].get_text())
            year = extract_year_from_text(first_cell_text)
            
            if year and 2000 <= year <= 2025:
                current_year = year
                
                if len(cells) >= 4:
                    author = clean_text(cells[1].get_text())
                    
                    title_elem = cells[2].find('i')
                    title = clean_text(title_elem.get_text()) if title_elem else clean_text(cells[2].get_text())
                    
                    result = clean_text(cells[3].get_text())
                    
                    if 'winner' in result.lower():
                        status = 'Winner'
                    elif 'finalist' in result.lower() or 'nominee' in result.lower():
                        status = 'Finalist'
                    else:
                        continue
                    
                    if title and author:
                        awards_data.append({
                            'Year': current_year,
                            'Award': 'National Book Award for Fiction',
                            'Status': status,
                            'Title': title,
                            'Author': author
                        })
                        logger.info(f"Found NBA {status} for {current_year}: {title} by {author}")
            
            elif current_year and len(cells) >= 3:
                # Continuation row
                author = clean_text(cells[0].get_text())
                
                title_elem = cells[1].find('i')
                title = clean_text(title_elem.get_text()) if title_elem else clean_text(cells[1].get_text())
                
                result = clean_text(cells[2].get_text())
                
                if 'winner' in result.lower():
                    status = 'Winner'
                elif 'finalist' in result.lower() or 'nominee' in result.lower():
                    status = 'Finalist'
                else:
                    continue
                
                if title and author:
                    awards_data.append({
                        'Year': current_year,
                        'Award': 'National Book Award for Fiction',
                        'Status': status,
                        'Title': title,
                        'Author': author
                    })
                    logger.info(f"Found NBA {status} for {current_year}: {title} by {author}")
    
    validated_data = validate_data(awards_data)
    logger.info(f"Found {len(validated_data)} National Book Award entries")
    
    if output_file:
        save_to_json(validated_data, output_file, backup=True)
    
    return validated_data


if __name__ == "__main__":
    # Run as standalone script
    output_path = "/Users/sosaha/Library/CloudStorage/OneDrive-Adobe/Acrobat Desktop 2019-2022/Documents/cs598-fdc-literary-awards/data/national_book_award.json"
    data = scrape_national_book_award(output_path)
    print(f"\nCollected {len(data)} National Book Award entries")
    
    # Show summary
    winners = sum(1 for x in data if x['Status'] == 'Winner')
    finalists = len(data) - winners
    print(f"Winners: {winners}, Finalists: {finalists}")

