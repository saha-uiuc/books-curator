#!/usr/bin/env python3
"""
Open Library API Data Fetcher
Fetches literary book data with public reception metrics from Open Library API
for years 2020-2025
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import os
import shutil


class OpenLibraryAPIFetcher:
    """Fetches book data from Open Library API"""
    
    SEARCH_URL = "https://openlibrary.org/search.json"
    WORKS_URL = "https://openlibrary.org/works"
    RATINGS_URL = "https://openlibrary.org/works"
    
    def __init__(self):
        """Initialize the Open Library API fetcher"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LiteraryAwardsResearch/1.0 (Educational Research Project)'
        })
        
    def search_books(self, 
                    query: str,
                    year: int,
                    limit: int = 100,
                    offset: int = 0) -> Dict:
        """
        Search for books using Open Library API
        
        Args:
            query: Search query (e.g., "fiction", "literary fiction")
            year: Publication year to filter
            limit: Maximum results per request (max 100)
            offset: Starting offset for pagination
            
        Returns:
            Dictionary containing API response
        """
        params = {
            'q': query,
            'first_publish_year': year,
            'limit': min(limit, 100),  # API limit is 100
            'offset': offset,
            'fields': 'key,title,author_name,first_publish_year,publisher,isbn,subject,ratings_average,ratings_count,want_to_read_count,currently_reading_count,already_read_count,number_of_pages_median,language',
        }
        
        try:
            response = self.session.get(self.SEARCH_URL, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return {}
    
    def get_work_details(self, work_key: str) -> Optional[Dict]:
        """
        Get detailed information about a work including ratings
        
        Args:
            work_key: Open Library work key (e.g., "/works/OL45804W")
            
        Returns:
            Dictionary with work details
        """
        try:
            # Get work details
            work_url = f"https://openlibrary.org{work_key}.json"
            response = self.session.get(work_url, timeout=10)
            response.raise_for_status()
            work_data = response.json()
            
            # Get ratings
            ratings_url = f"https://openlibrary.org{work_key}/ratings.json"
            ratings_response = self.session.get(ratings_url, timeout=10)
            if ratings_response.status_code == 200:
                ratings_data = ratings_response.json()
            else:
                ratings_data = {}
            
            return {
                'work_data': work_data,
                'ratings_data': ratings_data
            }
        except requests.exceptions.RequestException as e:
            print(f"Error fetching work details for {work_key}: {e}")
            return None
    
    def extract_book_info(self, item: Dict, start_year: int = 2020, end_year: int = 2025) -> Optional[Dict]:
        """
        Extract relevant information from a book item
        
        Args:
            item: Book item from API response
            start_year: Minimum publication year (inclusive)
            end_year: Maximum publication year (inclusive)
            
        Returns:
            Dictionary with extracted book information
        """
        try:
            # Extract publication year
            year = item.get('first_publish_year')
            
            # Only include books from the specified year range
            if year is None or year < start_year or year > end_year:
                return None
            
            # Extract subjects and check if it's fiction
            subjects = item.get('subject', [])
            if subjects:
                subjects_lower = [s.lower() for s in subjects[:10]]  # Limit to first 10
                is_fiction = any('fiction' in s for s in subjects_lower)
                if not is_fiction:
                    return None  # Skip non-fiction books
            
            book_data = {
                'title': item.get('title', 'N/A'),
                'authors': item.get('author_name', []),
                'year': year,
                'publishers': item.get('publisher', [])[:3] if item.get('publisher') else [],  # Limit to 3
                'isbn': item.get('isbn', [])[:2] if item.get('isbn') else [],  # Get first 2 ISBNs
                'subjects': subjects[:10] if subjects else [],  # Limit to 10 subjects
                'language': item.get('language', [])[:3] if item.get('language') else [],  # Top 3 languages
                'number_of_pages': item.get('number_of_pages_median'),
                
                # Public reception metrics
                'ratings_average': item.get('ratings_average'),
                'ratings_count': item.get('ratings_count', 0),
                'want_to_read_count': item.get('want_to_read_count', 0),
                'currently_reading_count': item.get('currently_reading_count', 0),
                'already_read_count': item.get('already_read_count', 0),
                
                # Open Library identifiers
                'openlibrary_key': item.get('key', 'N/A'),
            }
            
            return book_data
            
        except Exception as e:
            print(f"Error extracting book info: {e}")
            return None
    
    def fetch_literary_books(self, 
                            start_year: int = 2020, 
                            end_year: int = 2025,
                            max_books: int = 5000,
                            delay: float = 1.0) -> List[Dict]:
        """
        Fetch literary fiction books from the specified year range
        
        Args:
            start_year: Start year for search (inclusive)
            end_year: End year for search (inclusive)
            max_books: Maximum number of books to fetch
            delay: Delay between API requests (seconds) to respect rate limits
            
        Returns:
            List of book dictionaries
        """
        all_books = []
        seen_keys = set()
        
        # Search queries for literary fiction
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
        
        # Search year by year for better results
        for year in range(start_year, end_year + 1):
            if len(all_books) >= max_books:
                break
            
            print(f"\nSearching books from {year}...")
            
            for query in search_queries:
                if len(all_books) >= max_books:
                    break
                
                print(f"  Query: {query}")
                offset = 0
                max_offset = 500  # Limit to avoid too many requests
                
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
        """
        Save books data to JSON file with backup of existing file
        
        Args:
            books: List of book dictionaries
            filename: Output filename (default: openlibrary_books.json)
        """
        if filename is None:
            filename = 'openlibrary_books.json'
        
        # Ensure data directory exists
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        filepath = os.path.join(data_dir, filename)
        
        # Backup existing file if it exists
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
        
        print(f"\nData saved to: {filepath}")
        print(f"   Total books: {len(books)}")
        
        return filepath
    
    def _backup_file_if_exists(self, filepath: str) -> None:
        """
        Create a backup of the file if it exists and has data.
        Backup is saved to data_backup/ folder with timestamp: filename_YYYYMMDDHHmmSS.ext
        
        Args:
            filepath: Path to the file to backup
        """
        if not os.path.exists(filepath):
            return
        
        # Check file size
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            return
        
        # Get the directory and filename
        file_dir = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        base_name, ext = os.path.splitext(filename)
        
        # Create backup directory relative to the data directory
        parent_dir = os.path.dirname(file_dir)
        backup_dir = os.path.join(parent_dir, 'data_backup')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup with full timestamp (YYYYMMDDHHmmSS)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_filename = f"{base_name}_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        try:
            shutil.copy2(filepath, backup_path)
            print(f" Backed up existing file: {backup_filename}")
        except Exception as e:
            print(f" Failed to backup file: {e}")


def main():
    """Main execution function"""
    
    print("Using Open Library API (no API key required)")
    
    fetcher = OpenLibraryAPIFetcher()
    
    # Fetch books
    books = fetcher.fetch_literary_books(
        start_year=2020,
        end_year=2025,
        max_books=5000,
        delay=1.0
    )
    
    # Save to JSON
    if books:
        fetcher.save_to_json(books, filename='openlibrary_books.json')
        
        # Print some statistics
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
        print("\nNo books were fetched.")


if __name__ == '__main__':
    main()

