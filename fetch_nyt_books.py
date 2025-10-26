#!/usr/bin/env python3
"""Fetch bestseller and commercial success data from NY Times Books API (2020-2025)"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import shutil


class NYTimesAPIFetcher:
    BASE_URL = "https://api.nytimes.com/svc/books/v3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        
    def get_bestseller_lists(self) -> List[Dict]:
        fiction_lists = [
            {'encoded_name': 'combined-print-and-e-book-fiction', 'display_name': 'Combined Print & E-Book Fiction'},
            {'encoded_name': 'hardcover-fiction', 'display_name': 'Hardcover Fiction'},
            {'encoded_name': 'trade-fiction-paperback', 'display_name': 'Trade Fiction Paperback'},
            {'encoded_name': 'paperback-trade-fiction', 'display_name': 'Paperback Trade Fiction'},
        ]
        
        return fiction_lists
    
    def get_bestsellers_by_date(self, list_name: str, date: str) -> Dict:
        url = f"{self.BASE_URL}/lists/{date}/{list_name}.json"
        params = {'api-key': self.api_key}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {}
            print(f"HTTP Error for {date}: {e}")
            return {}
        except:
            return {}
    
    def get_book_reviews(self, title: str = None, author: str = None, isbn: str = None) -> Dict:
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
        except:
            return {}
    
    def extract_book_info(self, item: Dict, list_name: str, date: str) -> Dict:
        # TODO: maybe add more metadata fields?
        book_data = {
            'title': item.get('title', 'N/A'),
            'author': item.get('author', 'N/A'),
            'publisher': item.get('publisher', 'N/A'),
            'description': item.get('description', 'N/A'),
            'primary_isbn13': item.get('primary_isbn13', 'N/A'),
            'primary_isbn10': item.get('primary_isbn10', 'N/A'),
            
            # Bestseller metrics
            'rank': item.get('rank', 0),
            'rank_last_week': item.get('rank_last_week', 0),
            'weeks_on_list': item.get('weeks_on_list', 0),
            'bestseller_date': date,
            'list_name': list_name,
            
            'asterisk': item.get('asterisk', 0),
            'dagger': item.get('dagger', 0),
            
            'book_image': item.get('book_image', 'N/A'),
            'amazon_product_url': item.get('amazon_product_url', 'N/A'),
        }
        
        return book_data
    
    def fetch_bestsellers_date_range(self,
                                     list_name: str,
                                     start_date: str,
                                     end_date: str,
                                     delay: float = 6.0) -> List[Dict]:
        books = []
        seen_isbns = set()
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Sample dates: first of each month
        current = start
        dates_to_check = []
        
        while current <= end:
            dates_to_check.append(current.strftime('%Y-%m-%d'))
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
            
            time.sleep(delay)
        
        return books
    
    def fetch_fiction_bestsellers_historical(self, 
                                             start_year: int = 2020,
                                             end_year: int = 2025,
                                             max_requests: int = 100,
                                             delay: float = 12.0) -> List[Dict]:
        print(f"Fetching NYT fiction bestsellers ({start_year}-{end_year})")
        print(f"Max requests: {max_requests}, Delay: {delay}s between requests")
        print("=" * 70)
        
        all_books = []
        seen_isbns = set()
        requests_made = 0
        
        list_name = 'combined-print-and-e-book-fiction'
        
        # Sample dates: every 3 months from each year
        dates_to_check = []
        for year in range(start_year, end_year + 1):
            for month in [1, 4, 7, 10]:
                dates_to_check.append(f"{year}-{month:02d}-01")
        
        print(f"Will check {len(dates_to_check)} dates (every 3 months)")
        print(f"List: Combined Print & E-Book Fiction\n")
        
        for date in dates_to_check:
            if requests_made >= max_requests:
                print(f"\nWARNING: Reached maximum of {max_requests} requests")
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
            
            time.sleep(delay)
        
        print(f"\nSUCCESS: Made {requests_made} API requests")
        print(f"SUCCESS: Collected {len(all_books)} unique books")
        return all_books
    
    def save_to_json(self, books: List[Dict], filename: str = None):
        if filename is None:
            filename = 'nyt_bestsellers.json'
        
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        filepath = os.path.join(data_dir, filename)
        
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
    api_key = "qn9W553JGmpOq4bFYWxSWQuOBrkXpfJA"
    
    if not api_key:
        print("=" * 70)
        print("WARNING: NYT API KEY REQUIRED")

        print("=" * 70)
        return
    
    print("Using New York Times Books API")
    print("=" * 70)
    
    fetcher = NYTimesAPIFetcher(api_key=api_key)
    
    books = fetcher.fetch_fiction_bestsellers_historical(
        start_year=2020,
        end_year=2025,
        max_requests=30,
        delay=12.0
    )
    
    if books:
        fetcher.save_to_json(books, filename='nyt_bestsellers.json')
        
        print("\nStatistics:")
        
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
        print("\nERROR: No books were fetched.")


if __name__ == '__main__':
    main()
