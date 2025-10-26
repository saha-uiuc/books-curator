#!/usr/bin/env python3
"""Get book counts from Google Books API - quick check without fetching full data"""

from fetch_google_books import GoogleBooksAPIFetcher


def main():
    api_key = "AIzaSyA1DjQVSOBDlvlligfxGsLsVgubBRrBzvI"
    
    fetcher = GoogleBooksAPIFetcher(api_key=api_key)
    
    print("=" * 70)
    print("GOOGLE BOOKS API - BOOK COUNTS (2020-2025)")
    print("=" * 70)
    print("\nFetching counts for each year...\n")
    
    years = range(2020, 2026)
    year_counts = {}
    
    for year in years:
        query = f'subject:fiction'
        count = fetcher.get_book_count(query)
        year_counts[year] = count
        print(f"Fiction books ({year}).................. {count:>10,} books")
    
    print("\n" + "=" * 70)
    print("CATEGORY COUNTS (2020-2025)")
    print("=" * 70 + "\n")
    
    categories = {
        'Award-winning Fiction': 'subject:fiction award winning',
        'Literary Fiction': 'subject:literary fiction',
        'Fiction Bestsellers': 'subject:fiction bestseller',
        'Contemporary Fiction': 'subject:contemporary fiction',
        'Prize-winning Fiction': 'subject:fiction prize',
    }
    
    for category, query in categories.items():
        count = fetcher.get_book_count(query)
        print(f"{category:.<40} {count:>10,} books")
    
    print("\n" + "=" * 70)
    print("Note: Google Books API caps totalItems at 1,000,000")
    print("Actual counts may be higher. Year filtering is limited in the API.")
    print("=" * 70)


if __name__ == '__main__':
    main()
