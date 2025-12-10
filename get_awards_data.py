#!/usr/bin/env python3
"""
Fetch winners and nominees for major English-language fiction awards from Wikipedia.
Awards covered: Pulitzer Prize for Fiction, National Book Award for Fiction, Booker Prize
Years: 2000-2025
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Optional
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_page(url: str, retries: int = 3) -> Optional[BeautifulSoup]:
    """
    Fetch a webpage with retry logic.
    
    Args:
        url: The URL to fetch
        retries: Number of retry attempts
        
    Returns:
        BeautifulSoup object or None if failed
    """
    for attempt in range(retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Educational Research Project)'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Failed to fetch {url} after {retries} attempts")
                return None


def clean_text(text: str) -> str:
    """Clean and normalize text by removing extra whitespace and citations."""
    if not text:
        return ""
    # Remove citation brackets [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text.strip()


def extract_year_from_text(text: str) -> Optional[int]:
    """Extract a 4-digit year from text."""
    match = re.search(r'\b(19|20)\d{2}\b', text)
    if match:
        return int(match.group(0))
    return None


def scrape_pulitzer_prize() -> List[Dict]:
    """
    Scrape Pulitzer Prize for Fiction winners and finalists from Wikipedia.
    
    Returns:
        List of dictionaries containing award data
    """
    url = "https://en.wikipedia.org/wiki/Pulitzer_Prize_for_Fiction"
    logger.info(f"Fetching Pulitzer Prize data from {url}")
    
    soup = fetch_page(url)
    if not soup:
        return []
    
    awards_data = []
    
    # Find the tables with winners - there are two tables (1918-1979 and 1980-present)
    tables = soup.find_all('table', {'class': 'wikitable'})
    
    # We need the second table which covers 1980-2025
    target_table = tables[1] if len(tables) > 1 else tables[0] if tables else None
    
    if not target_table:
        logger.warning("Could not find Pulitzer Prize table")
        return []
    
    rows = target_table.find_all('tr')
    
    for row in rows[1:]:  # Skip header row
        cells = row.find_all(['td', 'th'])
        if len(cells) < 4:
            continue
            
        # Extract year from first column (cell 0)
        year_text = clean_text(cells[0].get_text())
        year = extract_year_from_text(year_text)
        
        if not year or year < 2000 or year > 2025:
            continue
        
        # Table structure:
        # Cell 0: Year
        # Cell 1: Empty (Winner designation)
        # Cell 2: Author name
        # Cell 3: Book title (in italics)
        # Cell 4: Publisher
        # Cell 5: Genre
        # Cell 6: Author's origin
        # Cell 7: Finalists (in "Author, Title" format)
        
        author_cell = cells[2] if len(cells) > 2 else None
        title_cell = cells[3] if len(cells) > 3 else None
        publisher_cell = cells[4] if len(cells) > 4 else None
        
        if author_cell and title_cell:
            author = clean_text(author_cell.get_text())
            # Extract just the name, remove birth year
            author = re.sub(r'\s*\([^)]*\)\s*', '', author).strip()
            
            # Try to find italicized title
            title_elem = title_cell.find('i')
            if title_elem:
                title = clean_text(title_elem.get_text())
            else:
                title = clean_text(title_cell.get_text())
            
            # Extract publisher
            publisher = ""
            if publisher_cell:
                publisher = clean_text(publisher_cell.get_text())
                # Remove year in parentheses from publisher
                publisher = re.sub(r'\s*\(\d{4}\)\s*', '', publisher).strip()
            
            # Handle special case for 2012 when no award was given
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
        
        # Parse finalists from cell 7
        if len(cells) > 7:
            finalists_cell = cells[7]
            
            # Check if finalists are in a list structure (most common format)
            list_items = finalists_cell.find_all('li')
            
            if list_items:
                # Parse list items: each item is "Author, Title" format
                for item in list_items:
                    # Get the author link
                    author_link = item.find('a')
                    if not author_link:
                        continue
                    
                    fin_author = clean_text(author_link.get_text())
                    
                    # Get the title (in italics)
                    title_elem = item.find('i')
                    if title_elem:
                        fin_title = clean_text(title_elem.get_text())
                    else:
                        # Try to extract title from text after author
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
                # Fallback: if not in list format, try parsing text directly
                # Some years have "Author, Title" separated by line breaks
                finalists_text = finalists_cell.get_text()
                
                # Use links to identify entries - each author link typically marks a new entry
                author_links = finalists_cell.find_all('a')
                
                for author_link in author_links:
                    fin_author = clean_text(author_link.get_text())
                    
                    # Try to find the title in italics near this author
                    # Get the parent element and look for <i> tags
                    parent = author_link.parent
                    title_elem = parent.find('i') if parent else None
                    
                    if title_elem:
                        fin_title = clean_text(title_elem.get_text())
                    else:
                        # Try to extract from text after the author link
                        # Pattern: "Author, Title" or "Author Title"
                        full_text = parent.get_text() if parent else ""
                        if ', ' in full_text:
                            # Split on comma after author name
                            author_pos = full_text.find(fin_author)
                            if author_pos != -1:
                                after_author = full_text[author_pos + len(fin_author):]
                                if after_author.startswith(','):
                                    # Extract until next capital letter or end
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
    
    logger.info(f"Found {len(awards_data)} Pulitzer Prize entries")
    return awards_data


def scrape_national_book_award() -> List[Dict]:
    """
    Scrape National Book Award for Fiction winners and finalists from Wikipedia.
    
    Returns:
        List of dictionaries containing award data
    """
    url = "https://en.wikipedia.org/wiki/National_Book_Award_for_Fiction"
    logger.info(f"Fetching National Book Award data from {url}")
    
    soup = fetch_page(url)
    if not soup:
        return []
    
    awards_data = []
    
    # Find tables with award information
    # The page has multiple tables organized by decade
    # Tables 6-8 cover 2000s, 2010s, and 2020s
    tables = soup.find_all('table', {'class': 'wikitable'})
    
    for table in tables:
        rows = table.find_all('tr')
        
        # Check if this table has the expected structure (Year, Author, Title, Result columns)
        if len(rows) > 0:
            headers = rows[0].find_all('th')
            header_text = ' '.join([h.get_text().strip() for h in headers]).lower()
            
            # Only process tables with the correct structure
            if 'year' not in header_text or 'author' not in header_text:
                continue
        
        current_year = None
        
        for row in rows[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            
            if len(cells) == 0:
                continue
            
            # Check if first cell contains a year (indicates new year row)
            first_cell_text = clean_text(cells[0].get_text())
            year = extract_year_from_text(first_cell_text)
            
            if year and 2000 <= year <= 2025:
                # This row starts a new year section
                current_year = year
                
                # This row has: Year, Author, Title, Result, Ref (5 cells)
                if len(cells) >= 4:
                    author = clean_text(cells[1].get_text())
                    
                    # Extract title (usually in italics)
                    title_elem = cells[2].find('i')
                    if title_elem:
                        title = clean_text(title_elem.get_text())
                    else:
                        title = clean_text(cells[2].get_text())
                    
                    # Extract result (Winner or Finalist)
                    result = clean_text(cells[3].get_text())
                    
                    # Determine status
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
                # Continuation row (no year column due to rowspan)
                # Structure: Author, Title, Result, Ref (4 cells)
                author = clean_text(cells[0].get_text())
                
                # Extract title
                title_elem = cells[1].find('i')
                if title_elem:
                    title = clean_text(title_elem.get_text())
                else:
                    title = clean_text(cells[1].get_text())
                
                # Extract result
                result = clean_text(cells[2].get_text())
                
                # Determine status
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
    
    logger.info(f"Found {len(awards_data)} National Book Award entries")
    return awards_data


def scrape_booker_prize() -> List[Dict]:
    """
    Scrape Booker Prize winners, shortlist and longlist from Wikipedia.
    
    Returns:
        List of dictionaries containing award data
    """
    # Use the dedicated page with shortlist/longlist data
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
        
        # Check if first cell has rowspan (indicates year or status header)
        rowspan = first_cell.get('rowspan')
        
        # Check if this is a year row
        year = extract_year_from_text(first_cell_text)
        if year and 2000 <= year <= 2025:
            current_year = year
            # Next rows will be for this year until we hit another year
            # Check if there's a status in the next cell or if this row has data
            if len(cells) >= 4:  # Year + Status + Author + Title (+ Publisher)
                # This row has: Year | Winner | Author | Title | Publisher
                second_cell = clean_text(cells[1].get_text())
                if 'winner' in second_cell.lower():
                    current_status = 'Winner'
                    author = clean_text(cells[2].get_text())
                    title_elem = cells[3].find('i')
                    title = clean_text(title_elem.get_text()) if title_elem else clean_text(cells[3].get_text())
                    publisher = clean_text(cells[4].get_text()) if len(cells) > 4 else ""
                    
                    if author and title:
                        entry = {
                            'Year': current_year,
                            'Award': 'Booker Prize',
                            'Status': current_status,
                            'Title': title,
                            'Author': author
                        }
                        if publisher:
                            entry['Publisher'] = publisher
                        awards_data.append(entry)
                        logger.info(f"Found Booker Prize {current_status} for {current_year}: {title} by {author}")
            continue
        
        # Check if this is a status row (Winner, Shortlist, Longlist)
        if 'winner' in first_cell_text.lower():
            current_status = 'Winner'
            # Data might be in same row or next rows
            if len(cells) >= 3:  # Status + Author + Title (+ Publisher)
                author = clean_text(cells[1].get_text())
                title_elem = cells[2].find('i')
                title = clean_text(title_elem.get_text()) if title_elem else clean_text(cells[2].get_text())
                publisher = clean_text(cells[3].get_text()) if len(cells) > 3 else ""
                
                if author and title:
                    entry = {
                        'Year': current_year,
                        'Award': 'Booker Prize',
                        'Status': current_status,
                        'Title': title,
                        'Author': author
                    }
                    if publisher:
                        entry['Publisher'] = publisher
                    awards_data.append(entry)
                    logger.info(f"Found Booker Prize {current_status} for {current_year}: {title} by {author}")
            continue
            
        elif 'shortlist' in first_cell_text.lower():
            current_status = 'Shortlist'
            # Data might be in same row
            if len(cells) >= 3:
                author = clean_text(cells[1].get_text())
                title_elem = cells[2].find('i')
                title = clean_text(title_elem.get_text()) if title_elem else clean_text(cells[2].get_text())
                publisher = clean_text(cells[3].get_text()) if len(cells) > 3 else ""
                
                if author and title:
                    entry = {
                        'Year': current_year,
                        'Award': 'Booker Prize',
                        'Status': current_status,
                        'Title': title,
                        'Author': author
                    }
                    if publisher:
                        entry['Publisher'] = publisher
                    awards_data.append(entry)
                    logger.info(f"Found Booker Prize {current_status} for {current_year}: {title} by {author}")
            continue
            
        elif 'longlist' in first_cell_text.lower():
            current_status = 'Longlist'
            # Data might be in same row
            if len(cells) >= 3:
                author = clean_text(cells[1].get_text())
                title_elem = cells[2].find('i')
                title = clean_text(title_elem.get_text()) if title_elem else clean_text(cells[2].get_text())
                publisher = clean_text(cells[3].get_text()) if len(cells) > 3 else ""
                
                if author and title:
                    entry = {
                        'Year': current_year,
                        'Award': 'Booker Prize',
                        'Status': current_status,
                        'Title': title,
                        'Author': author
                    }
                    if publisher:
                        entry['Publisher'] = publisher
                    awards_data.append(entry)
                    logger.info(f"Found Booker Prize {current_status} for {current_year}: {title} by {author}")
            continue
        
        # If we're here, this is a continuation row (no year/status in first cell)
        # Data structure: Author | Title | Publisher
        if current_year and current_status and len(cells) >= 2:
            author = clean_text(cells[0].get_text())
            title_elem = cells[1].find('i')
            title = clean_text(title_elem.get_text()) if title_elem else clean_text(cells[1].get_text())
            publisher = clean_text(cells[2].get_text()) if len(cells) > 2 else ""
            
            if author and title and len(author) > 1 and len(title) > 1:
                entry = {
                    'Year': current_year,
                    'Award': 'Booker Prize',
                    'Status': current_status,
                    'Title': title,
                    'Author': author
                }
                if publisher:
                    entry['Publisher'] = publisher
                awards_data.append(entry)
                logger.info(f"Found Booker Prize {current_status} for {current_year}: {title} by {author}")
    
    logger.info(f"Found {len(awards_data)} Booker Prize entries")
    return awards_data


def validate_data(data: List[Dict]) -> List[Dict]:
    """
    Validate and clean the collected data.
    
    Args:
        data: List of award dictionaries
        
    Returns:
        Cleaned and validated data
    """
    validated = []
    
    for entry in data:
        # Check required fields
        if not all(key in entry for key in ['Year', 'Award', 'Status', 'Title', 'Author']):
            logger.warning(f"Skipping entry with missing fields: {entry}")
            continue
        
        # Validate year range
        year = entry.get('Year')
        if year is None or not isinstance(year, int) or not (2000 <= year <= 2025):
            logger.warning(f"Skipping entry with invalid year: {entry.get('Year')} in {entry.get('Title', 'Unknown')}")
            continue
        
        # Check for empty values
        if not entry.get('Title') or not entry.get('Author'):
            logger.warning(f"Skipping entry with empty title/author: {entry}")
            continue
        
        validated.append(entry)
    
    return validated


def save_to_json(data: List[Dict], filename: str, output_dir: str = '.'):
    """
    Save data to a JSON file.
    
    Args:
        data: List of award dictionaries
        filename: Output filename
        output_dir: Output directory (default: current directory)
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(data)} entries to {filepath}")


def main():
    """Main execution function."""
    logger.info("Starting literary awards data collection...")
    
    output_dir = '/Users/sosaha/Library/CloudStorage/OneDrive-Adobe/Acrobat Desktop 2019-2022/Documents/cs598-fdc-literary-awards/data'
    
    # Scrape Pulitzer Prize
    try:
        logger.info("\n" + "="*60)
        pulitzer_data = scrape_pulitzer_prize()
        validated_pulitzer = validate_data(pulitzer_data)
        
        if validated_pulitzer:
            save_to_json(validated_pulitzer, 'pulitzer_prize.json', output_dir)
            winners = sum(1 for x in validated_pulitzer if x['Status'] == 'Winner')
            finalists = len(validated_pulitzer) - winners
            logger.info(f"Pulitzer Prize: {len(validated_pulitzer)} total ({winners} winners, {finalists} finalists)")
        else:
            logger.warning("No valid Pulitzer Prize data collected")
    except Exception as e:
        logger.error(f"Error scraping Pulitzer Prize: {e}", exc_info=True)
    
    # Scrape National Book Award
    try:
        logger.info("\n" + "="*60)
        nba_data = scrape_national_book_award()
        validated_nba = validate_data(nba_data)
        
        if validated_nba:
            save_to_json(validated_nba, 'national_book_award.json', output_dir)
            winners = sum(1 for x in validated_nba if x['Status'] == 'Winner')
            finalists = len(validated_nba) - winners
            logger.info(f"National Book Award: {len(validated_nba)} total ({winners} winners, {finalists} finalists)")
        else:
            logger.warning("No valid National Book Award data collected")
    except Exception as e:
        logger.error(f"Error scraping National Book Award: {e}", exc_info=True)
    
    # Scrape Booker Prize
    try:
        logger.info("\n" + "="*60)
        booker_data = scrape_booker_prize()
        validated_booker = validate_data(booker_data)
        
        if validated_booker:
            save_to_json(validated_booker, 'booker_prize.json', output_dir)
            winners = sum(1 for x in validated_booker if x['Status'] == 'Winner')
            finalists = len(validated_booker) - winners
            logger.info(f"Booker Prize: {len(validated_booker)} total ({winners} winners, {finalists} finalists)")
        else:
            logger.warning("No valid Booker Prize data collected")
    except Exception as e:
        logger.error(f"Error scraping Booker Prize: {e}", exc_info=True)
    
    logger.info("\n" + "="*60)
    logger.info("Data collection complete!")
    logger.info(f"JSON files saved in: {output_dir}")
    logger.info("="*60)


if __name__ == "__main__":
    main()

