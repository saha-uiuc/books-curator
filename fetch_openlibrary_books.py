#!/usr/bin/env python3
"""Fetch literary book data with public reception metrics from Open Library API"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import os
import shutil


class OpenLibraryAPIFetcher:
    SEARCH_URL = "https://openlibrary.org/search.json"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LiteraryAwardsResearch/1.0 (Educational Research Project)'
        })
        
    def search_books(self, 
                    query: str,
                    year: int,
                    limit: int = 100,
                    offset: int = 0) -> Dict:
        params = {
            "q": query,
            "first_publish_year": year,
            "limit": min(limit, 100),
            "offset": offset,
            "fields": 'key,title,author_name,first_publish_year,publisher,isbn,subject,ratings_average,ratings_count,want_to_read_count,currently_reading_count,already_read_count,number_of_pages_median,language',
        }
        
        try:
            response = self.session.get(self.SEARCH_URL, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except:
            return {}
    
    def extract_book_info(self, item: Dict, start_year: int = 2020, end_year: int = 2025) -> Optional[Dict]:
        year = item.get('first_publish_year')
        
        if year is None or year < start_year or year > end_year:
            return None
        
        # Check if it's fiction
        subjects = item.get('subject', [])
        if subjects:
            subjects_lower = [s.lower() for s in subjects[:10]]
            is_fiction = any('fiction' in s for s in subjects_lower)
            if not is_fiction:
                return None
        
        book_data = {
            'title': item.get('title', 'N/A'),
            'authors': item.get('author_name', []),
            'year': year,
            'publishers': item.get('publisher', [])[:3] if item.get('publisher') else [],
            'isbn': item.get('isbn', [])[:2] if item.get('isbn') else [],
            'subjects': subjects[:10] if subjects else [],
            'language': item.get('language', [])[:3] if item.get('language') else [],
            'number_of_pages': item.get('number_of_pages_median'),
            
            # Public reception metrics
            'ratings_average': item.get('ratings_average'),
            'ratings_count': item.get('ratings_count', 0),
            'want_to_read_count': item.get('want_to_read_count', 0),
            'currently_reading_count': item.get('currently_reading_count', 0),
            'already_read_count': item.get('already_read_count', 0),
            
            'openlibrary_key': item.get('key', 'N/A'),
        }
        
        return book_data
    
    def fetch_literary_books(self, 
                            start_year: int = 2020, 
                            end_year: int = 2025,
                            max_books: int = 5000,
                            delay: float = 1.0) -> List[Dict]:
        all_books = []
        seen_keys = set()
        
        search_queries = [
            'fiction',
            'literary fiction',
            'contemporary fiction',
            'fiction award',
            'fiction prize',
        ]
        
        print(f"Fetching literary books from Open Library API...")
        print(f"Year range: {start_year} to {end_year}")
        print(f"Target: {max_books} books\n")
        
        for year in range(start_year, end_year + 1):
            if len(all_books) >= max_books:
                break
            
            print(f"\nSearching books from {year}...")
            
            for query in search_queries:
                if len(all_books) >= max_books:
                    break
                
                print(f"  Query: {query}")
                offset = 0
                max_offset = 500
                
                while len(all_books) < max_books and offset < max_offset:
                    response = self.search_books(
                        query=query,
                        year=year,
                        limit=100,
                        offset=offset
                    )
                    
                    docs = response.get('docs', [])
                    if not docs:
                        break
                    
                    new_books = 0
                    for doc in docs:
                        book_info = self.extract_book_info(doc, start_year, end_year)
                        if book_info and book_info['openlibrary_key'] not in seen_keys:
                            all_books.append(book_info)
                            seen_keys.add(book_info['openlibrary_key'])
                            new_books += 1
                            
                            if len(all_books) >= max_books:
                                break
                    
                    if new_books > 0:
                        print(f"    Offset {offset}: Found {new_books} new books (Total: {len(all_books)})")
                    
                    offset += 100
                    
                    if len(docs) < 100:
                        break
                    
                    time.sleep(delay)
        
        return all_books
    
    def save_to_json(self, books: List[Dict], filename: str = None):
        if filename is None:
            filename = 'openlibrary_books.json'
        
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        filepath = os.path.join(data_dir, filename)
        
        self._backup_file_if_exists(filepath)
        
        output_data = {
            'metadata': {
                'source': 'Open Library API',
                'fetch_date': datetime.now().isoformat(),
                'total_books': len(books),
                'year_range': '2020-2025',
                'note': 'Includes public reception metrics: ratings, want_to_read, currently_reading, already_read counts'
            },
            'books': books
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSUCCESS: Data saved to: {filepath}")
        print(f"   Total books: {len(books)}")
        
        return filepath
    
    def _backup_file_if_exists(self, filepath: str) -> None:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
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
    print("Using Open Library API (no API key required)")
    
    fetcher = OpenLibraryAPIFetcher()
    
    books = fetcher.fetch_literary_books(
        start_year=2020,
        end_year=2025,
        max_books=5000,
        delay=1.0
    )
    
    if books:
        fetcher.save_to_json(books, filename='openlibrary_books.json')
        
        print("\nStatistics:")
        year_counts = {}
        books_with_ratings = 0
        total_ratings = 0
        
        for book in books:
            year = book.get('year')
            year_counts[year] = year_counts.get(year, 0) + 1
            
            if book.get('ratings_count', 0) > 0:
                books_with_ratings += 1
                total_ratings += book.get('ratings_count', 0)
        
        print("\n  Books by year:")
        for year in sorted(year_counts.keys()):
            print(f"    {year}: {year_counts[year]} books")
        
        print(f"\n  Public reception metrics:")
        print(f"    Books with ratings: {books_with_ratings} ({books_with_ratings/len(books)*100:.1f}%)")
        print(f"    Total ratings: {total_ratings:,}")
        if books_with_ratings > 0:
            print(f"    Average ratings per book: {total_ratings/books_with_ratings:.1f}")
    else:
        print("\nERROR: No books were fetched.")


if __name__ == '__main__':
    main()
