#!/usr/bin/env python3
"""Fetch winners and nominees for major English-language fiction awards from Wikipedia
Awards: Pulitzer Prize, National Book Award, Booker Prize (2000-2025)"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Optional
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_page(url: str, retries: int = 3) -> Optional[BeautifulSoup]:
    for attempt in range(retries):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Educational Research Project)'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\[\d+\]', '', text)
    text = ' '.join(text.split())
    return text.strip()


def extract_year_from_text(text: str) -> Optional[int]:
    match = re.search(r'\b(19|20)\d{2}\b', text)
    return int(match.group(0)) if match else None


def scrape_pulitzer_prize() -> List[Dict]:
    url = "https://en.wikipedia.org/wiki/Pulitzer_Prize_for_Fiction"
    logger.info(f"Fetching Pulitzer Prize data from {url}")
    
    soup = fetch_page(url)
    if not soup:
        return []
    
    awards_data = []
    # TODO: handle page format changes if Wikipedia updates structure
    tables = soup.find_all('table', {'class': 'wikitable'})
    
    # Use the second table (1980-present)
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
                logger.info(f"Found Pulitzer winner for {year}: {title} by {author}")
        
        # Parse finalists from cell 7
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
    
    logger.info(f"Found {len(awards_data)} Pulitzer Prize entries")
    return awards_data


def scrape_national_book_award() -> List[Dict]:
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
    
    logger.info(f"Found {len(awards_data)} National Book Award entries")
    return awards_data


def scrape_booker_prize() -> List[Dict]:
    url = "https://en.wikipedia.org/wiki/List_of_winners_and_nominated_authors_of_the_Booker_Prize"
    logger.info(f"Fetching Booker Prize data from {url}")
    
    soup = fetch_page(url)
    if not soup:
        return []
    
    awards_data = []
    table = soup.find('table', {'class': 'wikitable'})
    
    if not table:
        logger.warning("Could not find Booker Prize table")
        return []
    
    rows = table.find_all('tr')
    
    current_year = None
    current_status = None
    
    for row in rows[1:]:
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            continue
        
        first_cell = cells[0]
        first_cell_text = clean_text(first_cell.get_text())
        
        # Check if this is a year row
        year = extract_year_from_text(first_cell_text)
        if year and 2000 <= year <= 2025:
            current_year = year
            if len(cells) >= 4:
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
        
        # Check if this is a status row
        if 'winner' in first_cell_text.lower():
            current_status = 'Winner'
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
            
        elif 'shortlist' in first_cell_text.lower():
            current_status = 'Shortlist'
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
        
        # Continuation row
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
    validated = []
    
    for entry in data:
        if not all(key in entry for key in ['Year', 'Award', 'Status', 'Title', 'Author']):
            continue
        
        year = entry.get('Year')
        if not year or not isinstance(year, int) or not (2000 <= year <= 2025):
            continue
        
        if not entry.get('Title') or not entry.get('Author'):
            continue
        
        validated.append(entry)
    
    return validated


def save_to_json(data: List[Dict], filename: str, output_dir: str = '.'):
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(data)} entries to {filepath}")


def main():
    logger.info("Starting literary awards data collection...")
    
    output_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(output_dir, exist_ok=True)
    
    # Scrape Pulitzer Prize
    logger.info("\n" + "="*60)
    logger.info("Scraping Pulitzer Prize for Fiction")
    logger.info("="*60)
    pulitzer_data = scrape_pulitzer_prize()
    if pulitzer_data:
        validated_pulitzer = validate_data(pulitzer_data)
        save_to_json(validated_pulitzer, 'pulitzer_prize.json', output_dir)
    
    time.sleep(2)
    
    # Scrape National Book Award
    logger.info("\n" + "="*60)
    logger.info("Scraping National Book Award for Fiction")
    logger.info("="*60)
    nba_data = scrape_national_book_award()
    if nba_data:
        validated_nba = validate_data(nba_data)
        save_to_json(validated_nba, 'national_book_award.json', output_dir)
    
    time.sleep(2)
    
    # Scrape Booker Prize
    logger.info("\n" + "="*60)
    logger.info("Scraping Booker Prize")
    logger.info("="*60)
    booker_data = scrape_booker_prize()
    if booker_data:
        validated_booker = validate_data(booker_data)
        save_to_json(validated_booker, 'booker_prize.json', output_dir)
    
    # Summary
    total = len(pulitzer_data) + len(nba_data) + len(booker_data)
    logger.info("\n" + "="*60)
    logger.info("DATA COLLECTION COMPLETE")
    logger.info("="*60)
    logger.info(f"Total entries collected: {total}")
    logger.info(f"  Pulitzer Prize: {len(pulitzer_data)}")
    logger.info(f"  National Book Award: {len(nba_data)}")
    logger.info(f"  Booker Prize: {len(booker_data)}")
    logger.info(f"\nJSON files saved to: {output_dir}")


if __name__ == '__main__':
    main()
