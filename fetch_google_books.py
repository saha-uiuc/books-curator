#!/usr/bin/env python3
"""
Google Books API Data Fetcher
Fetches literary book data from Google Books API for years 2020-2025
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import os
import shutil


class GoogleBooksAPIFetcher:
    """Fetches book data from Google Books API"""
    
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Google Books API fetcher
        
        Args:
            api_key: Optional Google Books API key for higher rate limits
                    If not provided, will use the free tier (limited to 1000 requests/day)
        """
        self.api_key = api_key
        self.session = requests.Session()
        
    def search_books(self, 
                    query: str, 
                    start_year: int = 2020, 
                    end_year: int = 2025,
                    max_results: int = 40,
                    start_index: int = 0,
                    max_retries: int = 3) -> Dict:
        """
        Search for books using Google Books API with retry logic
        
        Args:
            query: Search query (e.g., "literary fiction", "award winning fiction")
            start_year: Start year for publication date filter
            end_year: End year for publication date filter
            max_results: Maximum results per request (max 40)
            start_index: Starting index for pagination
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary containing API response
        """
        params = {
            'q': query,
            'maxResults': min(max_results, 40),  # API limit is 40
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
                    wait_time = (2 ** attempt) * 5  # Exponential backoff: 5, 10, 20 seconds
                    if attempt < max_retries - 1:
                        print(f"Rate limited. Waiting {wait_time} seconds before retry...")
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
        """
        Get the total count of books matching a query without fetching all data
        
        Args:
            query: Search query (e.g., "literary fiction", "award winning fiction")
            
        Returns:
            Total count of books matching the query
        """
        params = {
            'q': query,
            'maxResults': 1,  # Only fetch 1 result to get the count
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
        except requests.exceptions.RequestException as e:
            print(f"Error fetching count: {e}")
            return 0
    
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
            volume_info = item.get('volumeInfo', {})
            
            # Extract publication year
            published_date = volume_info.get('publishedDate', '')
            year = None
            if published_date:
                try:
                    year = int(published_date.split('-')[0])
                except (ValueError, IndexError):
                    year = None
            
            # Only include books from the specified year range
            if year is None or year < start_year or year > end_year:
                return None
            
            book_data = {
                'title': volume_info.get('title', 'N/A'),
                'authors': volume_info.get('authors', []),
                'publisher': volume_info.get('publisher', 'N/A'),
                'published_date': published_date,
                'year': year,
                'categories': volume_info.get('categories', []),
                'page_count': volume_info.get('pageCount', 0),
                'language': volume_info.get('language', 'en'),
                'isbn_10': None,
                'isbn_13': None,
                'google_books_id': item.get('id', 'N/A'),
            }
            
            # Extract ISBNs
            for identifier in volume_info.get('industryIdentifiers', []):
                if identifier.get('type') == 'ISBN_10':
                    book_data['isbn_10'] = identifier.get('identifier')
                elif identifier.get('type') == 'ISBN_13':
                    book_data['isbn_13'] = identifier.get('identifier')
            
            return book_data
            
        except Exception as e:
            print(f"Error extracting book info: {e}")
            return None
    
    def fetch_literary_books(self, 
                            start_year: int = 2020, 
                            end_year: int = 2025,
                            max_books: int = 200,
                            delay: float = 1.0,
                            search_by_year: bool = True) -> List[Dict]:
        """
        Fetch literary fiction books from the specified year range
        
        Args:
            start_year: Start year for search (inclusive)
            end_year: End year for search (inclusive)
            max_books: Maximum number of books to fetch
            delay: Delay between API requests (seconds) to respect rate limits
            search_by_year: If True, search year by year for better filtering
            
        Returns:
            List of book dictionaries
        """
        all_books = []
        seen_ids = set()
        
        print(f"Fetching literary books from {start_year} to {end_year}...")
        print(f"Target: {max_books} books")
        print(f"Search strategy: {'Year-by-year' if search_by_year else 'General search'}\n")
        
        if search_by_year:
            # Search year by year for better targeting
            for year in range(start_year, end_year + 1):
                if len(all_books) >= max_books:
                    break
                
                print(f"\nSearching books from {year}...")
                
                # Different search queries for each year
                year_queries = [
                    f'subject:fiction {year}',
                    f'subject:literary fiction {year}',
                ]
                
                for query in year_queries:
                    if len(all_books) >= max_books:
                        break
                    
                    start_index = 0
                    max_per_query = 40  # Limit per query to avoid too many from one year
                    
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
                                book_info['year'] == year):  # Ensure it's from the target year
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
                max_api_results = 1000  # Google API limit per query
                
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
        """
        Save books data to JSON file with backup of existing file
        
        Args:
            books: List of book dictionaries
            filename: Output filename (default: google_books.json)
        """
        if filename is None:
            filename = 'google_books.json'
        
        # Ensure data directory exists
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        filepath = os.path.join(data_dir, filename)
        
        # Backup existing file if it exists
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
        
        print(f"\nData saved to: {filepath}")
        print(f"   Total books: {len(books)}")
    
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
        
        return filepath


def main():
    """Main execution function"""
    
    # Get API key from environment variable
    api_key = os.getenv('GOOGLE_BOOKS_API_KEY')
    if not api_key:
        print("ERROR: GOOGLE_BOOKS_API_KEY environment variable not set.")
        print("Please set it using: export GOOGLE_BOOKS_API_KEY='your_key_here'")
        print("See API_KEYS_REFERENCE.md for the key value.")
        return
    
    print("Using Google Books API key from environment variable")
    
    fetcher = GoogleBooksAPIFetcher(api_key=api_key)
    
    # Fetch books
    books = fetcher.fetch_literary_books(
        start_year=2020,
        end_year=2025,
        max_books=5000,
        delay=1.0,
        search_by_year=False
    )
    
    # Save to JSON
    if books:
        fetcher.save_to_json(books, filename='google_books.json')
        
        # Print some statistics
        print("\nStatistics:")
        year_counts = {}
        for book in books:
            year = book.get('year')
            year_counts[year] = year_counts.get(year, 0) + 1
        
        for year in sorted(year_counts.keys()):
            print(f"   {year}: {year_counts[year]} books")
    else:
        print("\nNo books were fetched.")


if __name__ == '__main__':
    main()

