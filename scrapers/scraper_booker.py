#!/usr/bin/env python3
"""
Scraper for Booker Prize from Wikipedia.
Captures winners, shortlist, and longlist from 2000-2025.
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


def scrape_booker_prize(output_file: str = None) -> List[Dict]:
    """Scrape Booker Prize winners, shortlist and longlist from Wikipedia"""
    url = "https://en.wikipedia.org/wiki/List_of_winners_and_nominated_authors_of_the_Booker_Prize"
    logger.info(f"Fetching Booker Prize data from {url}")
    
    soup = fetch_page(url)
    if not soup:
        return []
    
    awards_data = []
    
    # Find the main table with all data
    table = soup.find('table', {'class': 'wikitable'})
    
    if not table:
        logger.warning("Could not find Booker Prize table")
        return []
    
    rows = table.find_all('tr')
    
    current_year = None
    current_status = None
    
    for row in rows[1:]:  # Skip header
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            continue
        
        # Check first cell for year or status
        first_cell = cells[0]
        first_cell_text = clean_text(first_cell.get_text())
        
        # Check if this is a year row
        year = extract_year_from_text(first_cell_text)
        if year and 2000 <= year <= 2025:
            current_year = year
            if len(cells) >= 4:
                second_cell = clean_text(cells[1].get_text())
                if "winner" in second_cell.lower():
                    current_status = "Winner"
                    author = clean_text(cells[2].get_text())
                    title_elem = cells[3].find("i")
                    title = clean_text(title_elem.get_text()) if title_elem else clean_text(cells[3].get_text())
                    publisher = clean_text(cells[4].get_text()) if len(cells) > 4 else ""
                    
                    if author and title:
                        entry = {
                            "Year": current_year,
                            "Award": "Booker Prize",
                            "Status": current_status,
                            "Title": title,
                            "Author": author
                        }
                        if publisher:
                            entry["Publisher"] = publisher
                        awards_data.append(entry)
                        logger.info(f"Found Booker Prize {current_status} for {current_year}: {title} by {author}")
            continue
        
        # Check status rows
        if "winner" in first_cell_text.lower():
            current_status = "Winner"
            if len(cells) >= 3:
                author = clean_text(cells[1].get_text())
                title_elem = cells[2].find("i")
                title = clean_text(title_elem.get_text()) if title_elem else clean_text(cells[2].get_text())
                publisher = clean_text(cells[3].get_text()) if len(cells) > 3 else ""
                
                if author and title:
                    entry = {
                        "Year": current_year,
                        "Award": "Booker Prize",
                        "Status": current_status,
                        "Title": title,
                        "Author": author
                    }
                    if publisher:
                        entry["Publisher"] = publisher
                    awards_data.append(entry)
                    logger.info(f"Found Booker Prize {current_status} for {current_year}: {title} by {author}")
            continue
            
        elif "shortlist" in first_cell_text.lower():
            current_status = "Shortlist"
            if len(cells) >= 3:
                author = clean_text(cells[1].get_text())
                title_elem = cells[2].find("i")
                title = clean_text(title_elem.get_text()) if title_elem else clean_text(cells[2].get_text())
                publisher = clean_text(cells[3].get_text()) if len(cells) > 3 else ""
                
                if author and title:
                    entry = {
                        "Year": current_year,
                        "Award": "Booker Prize",
                        "Status": current_status,
                        "Title": title,
                        "Author": author
                    }
                    if publisher:
                        entry["Publisher"] = publisher
                    awards_data.append(entry)
                    logger.info(f"Found Booker Prize {current_status} for {current_year}: {title} by {author}")
            continue
            
        elif "longlist" in first_cell_text.lower():
            current_status = "Longlist"
            if len(cells) >= 3:
                author = clean_text(cells[1].get_text())
                title_elem = cells[2].find("i")
                title = clean_text(title_elem.get_text()) if title_elem else clean_text(cells[2].get_text())
                publisher = clean_text(cells[3].get_text()) if len(cells) > 3 else ""
                
                if author and title:
                    entry = {
                        "Year": current_year,
                        "Award": "Booker Prize",
                        "Status": current_status,
                        "Title": title,
                        "Author": author
                    }
                    if publisher:
                        entry["Publisher"] = publisher
                    awards_data.append(entry)
                    logger.info(f"Found Booker Prize {current_status} for {current_year}: {title} by {author}")
            continue
        
        # Continuation row
        if current_year and current_status and len(cells) >= 2:
            author = clean_text(cells[0].get_text())
            title_elem = cells[1].find("i")
            title = clean_text(title_elem.get_text()) if title_elem else clean_text(cells[1].get_text())
            publisher = clean_text(cells[2].get_text()) if len(cells) > 2 else ""
            
            if author and title and len(author) > 1 and len(title) > 1:
                entry = {
                    "Year": current_year,
                    "Award": "Booker Prize",
                    "Status": current_status,
                    "Title": title,
                    "Author": author
                }
                if publisher:
                    entry["Publisher"] = publisher
                awards_data.append(entry)
                logger.info(f"Found Booker Prize {current_status} for {current_year}: {title} by {author}")
    
    validated_data = validate_data(awards_data)
    logger.info(f"Found {len(validated_data)} Booker Prize entries")
    
    if output_file:
        save_to_json(validated_data, output_file, backup=True)
    
    return validated_data


if __name__ == "__main__":
    output_path = "/Users/sosaha/Library/CloudStorage/OneDrive-Adobe/Acrobat Desktop 2019-2022/Documents/cs598-fdc-literary-awards/data/booker_prize.json"
    data = scrape_booker_prize(output_path)
    print(f"\nCollected {len(data)} Booker Prize entries")
    
    # Show summary
    winners = sum(1 for x in data if x['Status'] == 'Winner')
    shortlist = sum(1 for x in data if x['Status'] == 'Shortlist')
    longlist = sum(1 for x in data if x['Status'] == 'Longlist')
    print(f"Winners: {winners}, Shortlist: {shortlist}, Longlist: {longlist}")

