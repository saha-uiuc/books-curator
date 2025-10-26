#!/usr/bin/env python3
"""Fetch literary book data from Google Books API for years 2020-2025"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import os
import shutil


class GoogleBooksAPIFetcher:
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        
    def search_books(self, 
                    query: str, 
                    start_year: int = 2020, 
                    end_year: int = 2025,
                    max_results: int = 40,
                    start_index: int = 0,
                    max_retries: int = 3) -> Dict:
        params = {
            'q': query,
            'maxResults': min(max_results, 40),
            'startIndex': start_index,
            'printType': 'books',
            'langRestrict': 'en',
            'orderBy': 'relevance'
        }
        
        if self.api_key:
            params['key'] = self.api_key
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(self.BASE_URL, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = (2 ** attempt) * 5
                    if attempt < max_retries - 1:
                        print(f"Rate limited. Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"Rate limit exceeded after {max_retries} attempts.")
                        return {}
                else:
                    print(f"HTTP Error: {e}")
                    return {}
            except requests.exceptions.RequestException as e:
                print(f"Error fetching data: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return {}
        
        return {}
    
    def get_book_count(self, query: str) -> int:
        params = {
            'q': query,
            'maxResults': 1,
            'printType': 'books',
            'langRestrict': 'en'
        }
        
        if self.api_key:
            params['key'] = self.api_key
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('totalItems', 0)
        except:
            return 0
    
    def extract_book_info(self, item: Dict, start_year: int = 2020, end_year: int = 2025) -> Optional[Dict]:
        volume_info = item.get('volumeInfo', {})
        
        # Extract and validate publication year
        published_date = volume_info.get('publishedDate', '')
        year = None
        if published_date:
            try:
                year = int(published_date.split('-')[0])
            except (ValueError, IndexError):
                pass
        
        # print(f"DEBUG: year={year}, date={published_date}")
        if year is None or year < start_year or year > end_year:
            return None
        
        book_data = {
            "title": volume_info.get("title", "N/A"),
            "authors": volume_info.get("authors", []),
            "publisher": volume_info.get("publisher", "N/A"),
            "published_date": published_date,
            "year": year,
            "categories": volume_info.get("categories", []),
            "page_count": volume_info.get("pageCount", 0),
            "language": volume_info.get("language", "en"),
            "isbn_10": None,
            "isbn_13": None,
            "google_books_id": item.get("id", "N/A"),
        }
        
        # Extract ISBNs
        for identifier in volume_info.get('industryIdentifiers', []):
            if identifier.get('type') == 'ISBN_10':
                book_data['isbn_10'] = identifier.get('identifier')
            elif identifier.get('type') == 'ISBN_13':
                book_data['isbn_13'] = identifier.get('identifier')
        
        return book_data
    
    def fetch_literary_books(self, 
                            start_year: int = 2020, 
                            end_year: int = 2025,
                            max_books: int = 200,
                            delay: float = 1.0,
                            search_by_year: bool = True) -> List[Dict]:
        all_books = []
        seen_ids = set()
        
        print(f"Fetching literary books from {start_year} to {end_year}...")
        print(f"Target: {max_books} books")
        print(f"Search strategy: {'Year-by-year' if search_by_year else 'General search'}\n")
        
        if search_by_year:
            for year in range(start_year, end_year + 1):
                if len(all_books) >= max_books:
                    break
                
                print(f"\nSearching books from {year}...")
                
                year_queries = [
                    f'subject:fiction {year}',
                    f'subject:literary fiction {year}',
                ]
                
                for query in year_queries:
                    if len(all_books) >= max_books:
                        break
                    
                    start_index = 0
                    max_per_query = 40
                    
                    while len(all_books) < max_books and start_index < max_per_query:
                        response = self.search_books(
                            query=query,
                            start_year=start_year,
                            end_year=end_year,
                            start_index=start_index
                        )
                        
                        items = response.get('items', [])
                        if not items:
                            break
                        
                        new_books = 0
                        for item in items:
                            book_info = self.extract_book_info(item, start_year, end_year)
                            if (book_info and 
                                book_info['google_books_id'] not in seen_ids and
                                book_info['year'] == year):
                                all_books.append(book_info)
                                seen_ids.add(book_info['google_books_id'])
                                new_books += 1
                                
                                if len(all_books) >= max_books:
                                    break
                        
                        if new_books > 0:
                            print(f"  Found {new_books} books from {year} (Total: {len(all_books)})")
                        
                        start_index += 40
                        
                        if len(items) < 40:
                            break
                        
                        time.sleep(delay)
        else:
            # Focus on literary, award-winning, and prize-winning fiction
            search_queries = [
                'subject:fiction award winning',
                'subject:literary fiction',
                'subject:fiction bestseller',
                'subject:contemporary fiction',
                'subject:fiction prize',
                'subject:fiction award',
                'subject:literary award',
                'subject:fiction pulitzer',
                'subject:fiction booker',
                'subject:fiction national book award',
                'subject:fiction novel prize',
                'subject:literary bestseller',
                'subject:contemporary literary fiction',
                'subject:fiction critically acclaimed',
                'subject:fiction notable',
            ]
            
            for query in search_queries:
                if len(all_books) >= max_books:
                    break
                    
                print(f"\nSearching: {query}")
                start_index = 0
                max_api_results = 1000
                
                while len(all_books) < max_books and start_index < max_api_results:
                    print(f"  Fetching results {start_index} to {start_index + 40}...", end=' ')
                    
                    response = self.search_books(
                        query=query,
                        start_year=start_year,
                        end_year=end_year,
                        start_index=start_index
                    )
                    
                    items = response.get('items', [])
                    if not items:
                        print("No more results.")
                        break
                    
                    new_books = 0
                    for item in items:
                        book_info = self.extract_book_info(item, start_year, end_year)
                        if book_info and book_info['google_books_id'] not in seen_ids:
                            all_books.append(book_info)
                            seen_ids.add(book_info['google_books_id'])
                            new_books += 1
                            
                            if len(all_books) >= max_books:
                                break
                    
                    print(f"Found {new_books} new books (Total: {len(all_books)})")
                    
                    start_index += 40
                    
                    if len(all_books) >= max_books or len(items) < 40:
                        break
                    
                    time.sleep(delay)
        
        return all_books
    
    def save_to_json(self, books: List[Dict], filename: str = None):
        if filename is None:
            filename = 'google_books.json'
        
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        filepath = os.path.join(data_dir, filename)
        
        self._backup_file_if_exists(filepath)
        
        output_data = {
            'metadata': {
                'source': 'Google Books API',
                'fetch_date': datetime.now().isoformat(),
                'total_books': len(books),
                'year_range': '2020-2025'
            },
            'books': books
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSUCCESS: Data saved to: {filepath}")
        print(f"   Total books: {len(books)}")
    
    def _backup_file_if_exists(self, filepath: str) -> None:
        if not os.path.exists(filepath):
            return
        
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            return
        
        file_dir = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        base_name, ext = os.path.splitext(filename)
        
        parent_dir = os.path.dirname(file_dir)
        backup_dir = os.path.join(parent_dir, 'data_backup')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_filename = f"{base_name}_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        shutil.copy2(filepath, backup_path)
        print(f"Backed up existing file: {backup_filename}")


def main():
    api_key = "AIzaSyA1DjQVSOBDlvlligfxGsLsVgubBRrBzvI"
    
    print("Using Google Books API key")
    
    fetcher = GoogleBooksAPIFetcher(api_key=api_key)
    
    books = fetcher.fetch_literary_books(
        start_year=2020,
        end_year=2025,
        max_books=5000,
        delay=1.0,
        search_by_year=False
    )
    
    if books:
        fetcher.save_to_json(books, filename='google_books.json')
        
        print("\nStatistics:")
        year_counts = {}
        for book in books:
            year = book.get('year')
            year_counts[year] = year_counts.get(year, 0) + 1
        
        for year in sorted(year_counts.keys()):
            print(f"   {year}: {year_counts[year]} books")
    else:
        print("\nERROR: No books were fetched.")


if __name__ == '__main__':
    main()
