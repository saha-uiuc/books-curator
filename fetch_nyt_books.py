#!/usr/bin/env python3
"""
New York Times Books API Data Fetcher
Fetches bestseller and commercial success data for fiction books from 2020-2025
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import shutil


class NYTimesAPIFetcher:
    """Fetches book data from New York Times Books API"""
    
    BASE_URL = "https://api.nytimes.com/svc/books/v3"
    
    def __init__(self, api_key: str):
        """
        Initialize the NYT Books API fetcher
        
        Args:
            api_key: New York Times API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        
    def get_bestseller_lists(self) -> List[Dict]:
        """
        Get predefined fiction bestseller list names
        
        Returns:
            List of bestseller list dictionaries
        """
        # Predefined fiction lists (since /lists/names endpoint is not available)
        fiction_lists = [
            {'encoded_name': 'combined-print-and-e-book-fiction', 'display_name': 'Combined Print & E-Book Fiction'},
            {'encoded_name': 'hardcover-fiction', 'display_name': 'Hardcover Fiction'},
            {'encoded_name': 'trade-fiction-paperback', 'display_name': 'Trade Fiction Paperback'},
            {'encoded_name': 'paperback-trade-fiction', 'display_name': 'Paperback Trade Fiction'},
        ]
        
        return fiction_lists
    
    def get_bestsellers_by_date(self, list_name: str, date: str) -> Dict:
        """
        Get bestsellers for a specific list and date
        
        Args:
            list_name: Encoded list name (e.g., 'combined-print-and-e-book-fiction')
            date: Date in YYYY-MM-DD format
            
        Returns:
            Dictionary containing API response
        """
        url = f"{self.BASE_URL}/lists/{date}/{list_name}.json"
        params = {'api-key': self.api_key}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # No data for this date
                return {}
            print(f"HTTP Error for {date}: {e}")
            return {}
        except requests.exceptions.RequestException as e:
            print(f"Error fetching bestsellers for {date}: {e}")
            return {}
    
    def get_book_reviews(self, title: str = None, author: str = None, isbn: str = None) -> Dict:
        """
        Get book reviews from NYT
        
        Args:
            title: Book title
            author: Author name
            isbn: ISBN number
            
        Returns:
            Dictionary with review data
        """
        url = f"{self.BASE_URL}/reviews.json"
        params = {'api-key': self.api_key}
        
        if isbn:
            params['isbn'] = isbn
        elif title:
            params['title'] = title
        if author:
            params['author'] = author
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {}
    
    def extract_book_info(self, item: Dict, list_name: str, date: str) -> Dict:
        """
        Extract relevant information from a bestseller item
        
        Args:
            item: Book item from API response
            list_name: Name of the bestseller list
            date: Date of the list
            
        Returns:
            Dictionary with extracted book information
        """
        try:
            # Data is directly in the item, not nested in book_details
            book_data = {
                'title': item.get('title', 'N/A'),
                'author': item.get('author', 'N/A'),
                'publisher': item.get('publisher', 'N/A'),
                'description': item.get('description', 'N/A'),
                'primary_isbn13': item.get('primary_isbn13', 'N/A'),
                'primary_isbn10': item.get('primary_isbn10', 'N/A'),
                
                # Bestseller metrics (commercial success indicators)
                'rank': item.get('rank', 0),
                'rank_last_week': item.get('rank_last_week', 0),
                'weeks_on_list': item.get('weeks_on_list', 0),
                'bestseller_date': date,
                'list_name': list_name,
                
                # Additional metadata
                'asterisk': item.get('asterisk', 0),  # Indicates new to list
                'dagger': item.get('dagger', 0),  # Indicates notable sales increase
                
                # Additional useful fields
                'book_image': item.get('book_image', 'N/A'),
                'amazon_product_url': item.get('amazon_product_url', 'N/A'),
            }
            
            return book_data
            
        except Exception as e:
            print(f"Error extracting book info: {e}")
            return None
    
    def fetch_bestsellers_date_range(self,
                                     list_name: str,
                                     start_date: str,
                                     end_date: str,
                                     delay: float = 6.0) -> List[Dict]:
        """
        Fetch bestsellers for a date range
        
        Args:
            list_name: Encoded list name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            delay: Delay between requests (NYT has rate limits: 10 calls/min = 6 sec delay)
            
        Returns:
            List of book dictionaries
        """
        books = []
        seen_isbns = set()
        
        # Convert dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Sample dates: first of each month to reduce API calls
        current = start
        dates_to_check = []
        
        while current <= end:
            dates_to_check.append(current.strftime('%Y-%m-%d'))
            # Move to first of next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        print(f"  Checking {len(dates_to_check)} dates...")
        
        for date in dates_to_check:
            response = self.get_bestsellers_by_date(list_name, date)
            
            results = response.get('results', {})
            if not results:
                continue
            
            books_data = results.get('books', [])
            
            new_books = 0
            for book_item in books_data:
                book_info = self.extract_book_info(book_item, list_name, date)
                if book_info:
                    isbn = book_info.get('primary_isbn13', 'N/A')
                    if isbn not in seen_isbns:
                        books.append(book_info)
                        seen_isbns.add(isbn)
                        new_books += 1
            
            if new_books > 0:
                print(f"    {date}: Found {new_books} new books (Total: {len(books)})")
            
            time.sleep(delay)  # Respect rate limits (10 calls/min)
        
        return books
    
    def fetch_fiction_bestsellers_historical(self, 
                                             start_year: int = 2020,
                                             end_year: int = 2025,
                                             max_requests: int = 100,
                                             delay: float = 12.0) -> List[Dict]:
        """
        Fetch historical fiction bestsellers with rate limiting
        
        Args:
            start_year: Start year
            end_year: End year
            max_requests: Maximum number of API requests to make
            delay: Delay between requests in seconds (12s = 5 requests/min)
            
        Returns:
            List of book dictionaries
        """
        print(f"Fetching NYT fiction bestsellers ({start_year}-{end_year})")
        print(f"Max requests: {max_requests}, Delay: {delay}s between requests")
        print("=" * 70)
        
        all_books = []
        seen_isbns = set()
        requests_made = 0
        
        # Use only the main combined fiction list to maximize coverage
        list_name = 'combined-print-and-e-book-fiction'
        
        # Sample dates: every 3 months from each year
        dates_to_check = []
        for year in range(start_year, end_year + 1):
            for month in [1, 4, 7, 10]:  # Jan, Apr, Jul, Oct
                dates_to_check.append(f"{year}-{month:02d}-01")
        
        print(f"Will check {len(dates_to_check)} dates (every 3 months)")
        print(f"List: Combined Print & E-Book Fiction\n")
        
        for date in dates_to_check:
            if requests_made >= max_requests:
                print(f"\n Reached maximum of {max_requests} requests")
                break
            
            print(f"{date}...", end=' ')
            
            response = self.get_bestsellers_by_date(list_name, date)
            requests_made += 1
            
            results = response.get('results', {})
            if not results:
                print("No data")
                time.sleep(delay)
                continue
            
            books_data = results.get('books', [])
            
            new_books = 0
            for book_item in books_data:
                book_info = self.extract_book_info(book_item, list_name, date)
                if book_info:
                    isbn = book_info.get('primary_isbn13', 'N/A')
                    if isbn not in seen_isbns:
                        all_books.append(book_info)
                        seen_isbns.add(isbn)
                        new_books += 1
            
            print(f"Found {new_books} new books (Total: {len(all_books)})")
            
            # Respect rate limits
            time.sleep(delay)
        
        print(f"\nMade {requests_made} API requests")
        print(f"Collected {len(all_books)} unique books")
        return all_books
    
    def save_to_json(self, books: List[Dict], filename: str = None):
        """
        Save books data to JSON file with backup of existing file
        
        Args:
            books: List of book dictionaries
            filename: Output filename (default: nyt_bestsellers.json)
        """
        if filename is None:
            filename = 'nyt_bestsellers.json'
        
        # Ensure data directory exists
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        filepath = os.path.join(data_dir, filename)
        
        # Backup existing file if it exists
        self._backup_file_if_exists(filepath)
        
        output_data = {
            'metadata': {
                'source': 'New York Times Books API',
                'fetch_date': datetime.now().isoformat(),
                'total_books': len(books),
                'year_range': '2020-2025',
                'note': 'Includes commercial success metrics: bestseller rank, weeks on list, etc.'
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
    
    # Get API key from environment variable
    api_key = os.getenv('NYT_BOOKS_API_KEY')
    
    if not api_key:
        print("=" * 70)
        print("ERROR: NYT_BOOKS_API_KEY environment variable not set.")
        print("=" * 70)
        print("\nPlease set it using:")
        print("  export NYT_BOOKS_API_KEY='your_key_here'")
        print("\nSee API_KEYS_REFERENCE.md for the key value.")
        print("=" * 70)
        return
    
    print("Using New York Times Books API key from environment variable")
    print("=" * 70)
    
    fetcher = NYTimesAPIFetcher(api_key=api_key)
    
    # Fetch historical bestsellers (2020-2025)
    # Samples every 3 months = 24 dates total
    # With 12 second delay = ~5 minutes total
    books = fetcher.fetch_fiction_bestsellers_historical(
        start_year=2020,
        end_year=2025,
        max_requests=30,  # Limit to 30 requests to be safe
        delay=12.0  # 12 seconds = 5 requests per minute
    )
    
    # Save to JSON
    if books:
        fetcher.save_to_json(books, filename='nyt_bestsellers.json')
        
        # Print some statistics
        print("\nStatistics:")
        
        # Books by year (based on bestseller date)
        year_counts = {}
        total_weeks = 0
        max_weeks = 0
        
        for book in books:
            date = book.get('bestseller_date', '')
            if date:
                year = date.split('-')[0]
                year_counts[year] = year_counts.get(year, 0) + 1
            
            weeks = book.get('weeks_on_list', 0)
            total_weeks += weeks
            if weeks > max_weeks:
                max_weeks = weeks
        
        print("\n  Books by year (first appearance):")
        for year in sorted(year_counts.keys()):
            print(f"    {year}: {year_counts[year]} books")
        
        print(f"\n  Commercial success metrics:")
        print(f"    Total weeks on bestseller lists: {total_weeks:,}")
        print(f"    Average weeks per book: {total_weeks/len(books):.1f}")
        print(f"    Maximum weeks on list: {max_weeks}")
    else:
        print("\nNo books were fetched.")


if __name__ == '__main__':
    main()

