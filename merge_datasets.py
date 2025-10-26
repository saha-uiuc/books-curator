#!/usr/bin/env python3
"""Merge literary award data with book metadata and reception metrics"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from difflib import SequenceMatcher


class DatasetMerger:
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(__file__)
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.output_dir = os.path.join(self.base_dir, 'merged_data')
        
        self.stats = {
            'awards': {'total': 0, 'matched': 0, 'unmatched': 0},
            'google_books': {'total': 0, 'matched': 0, 'unmatched': 0},
            'openlibrary': {'total': 0, 'matched': 0, 'unmatched': 0},
            'nyt_bestsellers': {'total': 0, 'matched': 0, 'unmatched': 0},
            'merged': {'total': 0}
        }
        
        self.merged_books = {}
        self.unmatched_data = {
            'awards': [],
            'google_books': [],
            'openlibrary': [],
            'nyt_bestsellers': []
        }
        
    def load_json(self, filename: str) -> any:
        filepath = os.path.join(self.data_dir, filename)
        print(f"Loading {filename}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def normalize_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower().strip()
        # Remove common articles
        for article in ["the ", "a ", "an "]:
            if text.startswith(article):
                text = text[len(article):]
        text = ''.join(c if c.isalnum() or c.isspace() else '' for c in text)
        return ' '.join(text.split())
    
    def normalize_author(self, author: any) -> str:
        if isinstance(author, list):
            return ', '.join(author).lower().strip()
        elif isinstance(author, str):
            return author.lower().strip()
        return ""
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1, str2).ratio()
    
    def fuzzy_match(self, title1: str, author1: str, title2: str, author2: str, 
                   threshold: float = 0.85) -> bool:
        norm_title1 = self.normalize_text(title1)
        norm_title2 = self.normalize_text(title2)
        norm_author1 = self.normalize_text(author1)
        norm_author2 = self.normalize_text(author2)
        
        # TODO: maybe try phonetic matching for author names?
        title_similarity = self.calculate_similarity(norm_title1, norm_title2)
        author_similarity = self.calculate_similarity(norm_author1, norm_author2)
        
        # print(f"DEBUG: matching '{title1}' vs '{title2}': {title_similarity}")
        return title_similarity >= threshold and author_similarity >= threshold
    
    def generate_book_id(self, title: str, author: str) -> str:
        norm_title = self.normalize_text(title)
        norm_author = self.normalize_text(author)
        return f"{norm_title}_{norm_author}".replace(' ', '_')[:100]
    
    def find_book_by_isbn(self, isbn: str) -> Optional[str]:
        if not isbn or isbn == 'N/A':
            return None
        
        for book_id, book_data in self.merged_books.items():
            isbns = book_data.get('isbn_all', [])
            if isbn in isbns:
                return book_id
        return None
    
    def find_book_by_fuzzy_match(self, title: str, author: str) -> Optional[str]:
        for book_id, book_data in self.merged_books.items():
            if self.fuzzy_match(
                title, author,
                book_data.get('title', ''),
                book_data.get('author', '')
            ):
                return book_id
        return None
    
    def create_base_book_entry(self, title: str, author: str, year: int = None) -> Dict:
        return {
            'title': title,
            'author': author,
            'year': year,
            'isbn_all': [],
            'isbn_13': None,
            'isbn_10': None,
            'identifiers': {},
            
            'awards': [],
            'award_count': 0,
            'won_award': False,
            'shortlisted': False,
            
            'ratings_average': None,
            'ratings_count': 0,
            'want_to_read_count': 0,
            'currently_reading_count': 0,
            'already_read_count': 0,
            
            'bestseller_appearances': 0,
            'total_weeks_on_bestseller': 0,
            'highest_rank': None,
            'bestseller_dates': [],
            
            'publisher': None,
            'page_count': None,
            'categories': [],
            'description': None,
            'language': None,
            
            'sources': []
        }
    
    def add_isbn_to_book(self, book_data: Dict, isbn: str):
        if isbn and isbn != 'N/A' and isbn not in book_data['isbn_all']:
            book_data['isbn_all'].append(isbn)
            
            if len(isbn) == 13 and not book_data['isbn_13']:
                book_data['isbn_13'] = isbn
            elif len(isbn) == 10 and not book_data['isbn_10']:
                book_data['isbn_10'] = isbn
    
    def merge_awards_data(self):
        print("\n" + "="*70)
        print("MERGING AWARDS DATA")
        print("="*70)
        
        award_files = [
            'booker_prize.json',
            'national_book_award.json',
            'pulitzer_prize.json'
        ]
        
        all_awards = []
        for filename in award_files:
            awards = self.load_json(filename)
            all_awards.extend(awards)
        
        self.stats['awards']['total'] = len(all_awards)
        print(f"Total award entries: {len(all_awards)}")
        
        awards_2020_2025 = [a for a in all_awards if 2020 <= a.get('Year', 0) <= 2025]
        print(f"Award entries (2020-2025): {len(awards_2020_2025)}")
        
        for award_entry in awards_2020_2025:
            title = award_entry.get('Title', '')
            author = award_entry.get('Author', '')
            year = award_entry.get('Year')
            
            if not title or not author:
                continue
            
            book_id = self.find_book_by_fuzzy_match(title, author)
            
            if not book_id:
                book_id = self.generate_book_id(title, author)
                self.merged_books[book_id] = self.create_base_book_entry(title, author, year)
            
            book = self.merged_books[book_id]
            book['awards'].append({
                'award': award_entry.get('Award', ''),
                'year': year,
                'status': award_entry.get('Status', ''),
                'publisher': award_entry.get('Publisher')
            })
            book['award_count'] += 1
            
            if award_entry.get('Status') == 'Winner':
                book['won_award'] = True
            if award_entry.get('Status') in ['Shortlist', 'Finalist']:
                book['shortlisted'] = True
            
            if 'awards' not in book['sources']:
                book['sources'].append('awards')
            
            self.stats['awards']['matched'] += 1
        
        print(f"SUCCESS: Merged {self.stats['awards']['matched']} award entries")
    
    def merge_google_books_data(self):
        print("\n" + "="*70)
        print("MERGING GOOGLE BOOKS DATA")
        print("="*70)
        
        google_data = self.load_json('google_books.json')
        books = google_data.get('books', [])
        self.stats['google_books']['total'] = len(books)
        print(f"Total Google Books entries: {len(books)}")
        
        for book_entry in books:
            title = book_entry.get('title', '')
            authors = book_entry.get('authors', [])
            author = ', '.join(authors) if authors else ''
            
            if not title:
                self.unmatched_data['google_books'].append(book_entry)
                continue
            
            isbn_13 = book_entry.get('isbn_13')
            isbn_10 = book_entry.get('isbn_10')
            
            book_id = None
            if isbn_13:
                book_id = self.find_book_by_isbn(isbn_13)
            if not book_id and isbn_10:
                book_id = self.find_book_by_isbn(isbn_10)
            
            if not book_id and author:
                book_id = self.find_book_by_fuzzy_match(title, author)
            
            if book_id:
                book = self.merged_books[book_id]
                self.stats['google_books']['matched'] += 1
            else:
                book_id = self.generate_book_id(title, author)
                year = book_entry.get('year')
                book = self.create_base_book_entry(title, author, year)
                self.merged_books[book_id] = book
                self.unmatched_data['google_books'].append(book_entry)
                self.stats['google_books']['unmatched'] += 1
            
            self.add_isbn_to_book(book, isbn_13)
            self.add_isbn_to_book(book, isbn_10)
            
            if not book['publisher']:
                book['publisher'] = book_entry.get('publisher')
            if not book['page_count']:
                book['page_count'] = book_entry.get('page_count')
            if not book['language']:
                book['language'] = book_entry.get('language')
            
            categories = book_entry.get('categories', [])
            for cat in categories:
                if cat not in book['categories']:
                    book['categories'].append(cat)
            
            book['identifiers']['google_books_id'] = book_entry.get('google_books_id')
            
            if 'google_books' not in book['sources']:
                book['sources'].append('google_books')
        
        print(f"SUCCESS: Matched: {self.stats['google_books']['matched']}")
        print(f"WARNING: Unmatched: {self.stats['google_books']['unmatched']}")
    
    def merge_openlibrary_data(self):
        print("\n" + "="*70)
        print("MERGING OPEN LIBRARY DATA")
        print("="*70)
        
        ol_data = self.load_json('openlibrary_books.json')
        books = ol_data.get('books', [])
        self.stats['openlibrary']['total'] = len(books)
        print(f"Total Open Library entries: {len(books)}")
        
        for book_entry in books:
            title = book_entry.get('title', '')
            authors = book_entry.get('authors', [])
            author = ', '.join(authors) if authors else ''
            
            if not title:
                self.unmatched_data['openlibrary'].append(book_entry)
                continue
            
            isbns = book_entry.get('isbn', [])
            book_id = None
            
            for isbn in isbns:
                book_id = self.find_book_by_isbn(isbn)
                if book_id:
                    break
            
            if not book_id and author:
                book_id = self.find_book_by_fuzzy_match(title, author)
            
            if book_id:
                book = self.merged_books[book_id]
                self.stats['openlibrary']['matched'] += 1
            else:
                book_id = self.generate_book_id(title, author)
                year = book_entry.get('year')
                book = self.create_base_book_entry(title, author, year)
                self.merged_books[book_id] = book
                self.unmatched_data['openlibrary'].append(book_entry)
                self.stats['openlibrary']['unmatched'] += 1
            
            for isbn in isbns:
                self.add_isbn_to_book(book, isbn)
            
            # Add reception data - this is the valuable part
            book['ratings_average'] = book_entry.get('ratings_average')
            book['ratings_count'] = book_entry.get('ratings_count', 0)
            book['want_to_read_count'] = book_entry.get('want_to_read_count', 0)
            book['currently_reading_count'] = book_entry.get('currently_reading_count', 0)
            book['already_read_count'] = book_entry.get('already_read_count', 0)
            
            book['identifiers']['openlibrary_key'] = book_entry.get('openlibrary_key')
            
            if 'openlibrary' not in book['sources']:
                book['sources'].append('openlibrary')
        
        print(f"SUCCESS: Matched: {self.stats['openlibrary']['matched']}")
        print(f"WARNING: Unmatched: {self.stats['openlibrary']['unmatched']}")
    
    def merge_nyt_bestsellers_data(self):
        print("\n" + "="*70)
        print("MERGING NYT BESTSELLERS DATA")
        print("="*70)
        
        nyt_data = self.load_json('nyt_bestsellers.json')
        books = nyt_data.get('books', [])
        self.stats['nyt_bestsellers']['total'] = len(books)
        print(f"Total NYT Bestseller entries: {len(books)}")
        
        for book_entry in books:
            title = book_entry.get('title', '')
            author = book_entry.get('author', '')
            
            if not title:
                self.unmatched_data['nyt_bestsellers'].append(book_entry)
                continue
            
            isbn_13 = book_entry.get('primary_isbn13')
            isbn_10 = book_entry.get('primary_isbn10')
            
            book_id = None
            if isbn_13 and isbn_13 != 'N/A':
                book_id = self.find_book_by_isbn(isbn_13)
            if not book_id and isbn_10 and isbn_10 != 'N/A':
                book_id = self.find_book_by_isbn(isbn_10)
            
            if not book_id and author:
                book_id = self.find_book_by_fuzzy_match(title, author)
            
            if book_id:
                book = self.merged_books[book_id]
                self.stats['nyt_bestsellers']['matched'] += 1
            else:
                book_id = self.generate_book_id(title, author)
                book = self.create_base_book_entry(title, author, None)
                self.merged_books[book_id] = book
                self.unmatched_data['nyt_bestsellers'].append(book_entry)
                self.stats['nyt_bestsellers']['unmatched'] += 1
            
            self.add_isbn_to_book(book, isbn_13)
            self.add_isbn_to_book(book, isbn_10)
            
            # Add commercial success metrics
            book['bestseller_appearances'] += 1
            weeks = book_entry.get('weeks_on_list', 0)
            book['total_weeks_on_bestseller'] += weeks
            
            rank = book_entry.get('rank')
            if rank:
                if book['highest_rank'] is None or rank < book['highest_rank']:
                    book['highest_rank'] = rank
            
            bestseller_date = book_entry.get('bestseller_date')
            if bestseller_date and bestseller_date not in book['bestseller_dates']:
                book['bestseller_dates'].append(bestseller_date)
            
            if 'nyt_bestsellers' not in book['sources']:
                book['sources'].append('nyt_bestsellers')
        
        print(f"SUCCESS: Matched: {self.stats['nyt_bestsellers']['matched']}")
        print(f"WARNING: Unmatched: {self.stats['nyt_bestsellers']['unmatched']}")
    
    def save_merged_data(self):
        print("\n" + "="*70)
        print("SAVING MERGED DATASETS")
        print("="*70)
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        merged_list = list(self.merged_books.values())
        self.stats['merged']['total'] = len(merged_list)
        
        merged_output = {
            'metadata': {
                'created_date': datetime.now().isoformat(),
                'total_books': len(merged_list),
                'sources': ['awards', 'google_books', 'openlibrary', 'nyt_bestsellers'],
                'description': 'Merged dataset combining award data with book metadata and reception metrics'
            },
            'books': merged_list
        }
        
        merged_file = os.path.join(self.output_dir, 'merged_literary_books.json')
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(merged_output, f, indent=2, ensure_ascii=False)
        print(f"SUCCESS: Saved merged dataset: merged_literary_books.json ({len(merged_list)} books)")
        
        # Save unmatched data
        for source, data in self.unmatched_data.items():
            if data:
                unmatched_file = os.path.join(self.output_dir, f'unmatched_{source}.json')
                unmatched_output = {
                    'metadata': {
                        'source': source,
                        'created_date': datetime.now().isoformat(),
                        'total_unmatched': len(data),
                        'description': f'Unmatched entries from {source} that could not be merged'
                    },
                    'entries': data
                }
                with open(unmatched_file, 'w', encoding='utf-8') as f:
                    json.dump(unmatched_output, f, indent=2, ensure_ascii=False)
                print(f"WARNING: Saved unmatched data: unmatched_{source}.json ({len(data)} entries)")
    
    def generate_report(self):
        print("\n" + "="*70)
        print("GENERATING MERGE REPORT")
        print("="*70)
        
        report = {
            'merge_summary': {
                'created_date': datetime.now().isoformat(),
                'description': 'Statistical report of dataset merge operation'
            },
            'source_datasets': {},
            'merged_dataset': {
                'total_unique_books': self.stats['merged']['total'],
                'books_with_awards': sum(1 for b in self.merged_books.values() if b['award_count'] > 0),
                'books_with_reception_data': sum(1 for b in self.merged_books.values() if b['ratings_count'] > 0),
                'books_on_bestseller_list': sum(1 for b in self.merged_books.values() if b['bestseller_appearances'] > 0),
                'books_with_multiple_sources': sum(1 for b in self.merged_books.values() if len(b['sources']) > 1)
            },
            'data_quality': {
                'books_with_isbn': sum(1 for b in self.merged_books.values() if b['isbn_13'] or b['isbn_10']),
                'books_with_ratings': sum(1 for b in self.merged_books.values() if b['ratings_average'] is not None),
                'award_winning_books': sum(1 for b in self.merged_books.values() if b['won_award']),
                'bestsellers': sum(1 for b in self.merged_books.values() if b['bestseller_appearances'] > 0)
            }
        }
        
        # Add source dataset stats
        for source in ['awards', 'google_books', 'openlibrary', 'nyt_bestsellers']:
            stats = self.stats[source]
            total = stats['total']
            matched = stats['matched']
            unmatched = stats['unmatched']
            report['source_datasets'][source] = {
                'total_entries': total,
                'matched': matched,
                'unmatched': unmatched,
                'match_rate': f"{(matched / total * 100):.1f}%" if total > 0 else "0%"
            }
        
        report_file = os.path.join(self.output_dir, 'merge_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nMERGE STATISTICS:")
        print(f"{'='*70}")
        print(f"{'Source':<20} {'Total':<10} {'Matched':<10} {'Unmatched':<10} {'Match Rate':<10}")
        print(f"{'-'*70}")
        
        for source in ['awards', 'google_books', 'openlibrary', 'nyt_bestsellers']:
            stats = self.stats[source]
            total = stats['total']
            matched = stats['matched']
            unmatched = stats['unmatched']
            rate = f"{(matched / total * 100):.1f}%" if total > 0 else "0%"
            print(f"{source:<20} {total:<10} {matched:<10} {unmatched:<10} {rate:<10}")
        
        print(f"{'='*70}")
        print(f"\nMERGED DATASET:")
        print(f"   Total unique books: {self.stats['merged']['total']}")
        print(f"   Books with awards: {report['merged_dataset']['books_with_awards']}")
        print(f"   Books with reception data: {report['merged_dataset']['books_with_reception_data']}")
        print(f"   Books on bestseller list: {report['merged_dataset']['books_on_bestseller_list']}")
        print(f"   Books from multiple sources: {report['merged_dataset']['books_with_multiple_sources']}")
        
        print(f"\nSUCCESS: Saved merge report: merge_report.json")
    
    def run(self):
        print("\n" + "="*70)
        print("LITERARY BOOKS DATASET MERGER")
        print("="*70)
        print("This script merges award data with book metadata and reception metrics")
        print("="*70)
        
        self.merge_awards_data()
        self.merge_google_books_data()
        self.merge_openlibrary_data()
        self.merge_nyt_bestsellers_data()
        
        self.save_merged_data()
        self.generate_report()
        
        print("\n" + "="*70)
        print("SUCCESS: MERGE COMPLETE!")
        print("="*70)
        print(f"\nOutput files saved to: {self.output_dir}/")
        print("  - merged_literary_books.json (main merged dataset)")
        print("  - unmatched_*.json (unmatched entries from each source)")
        print("  - merge_report.json (detailed statistics)")
        print("="*70)


def main():
    merger = DatasetMerger()
    merger.run()


if __name__ == '__main__':
    main()
