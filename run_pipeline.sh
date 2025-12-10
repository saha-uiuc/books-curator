#!/bin/bash

# ============================================================================
# Complete Literary Awards and Book Reception Data Collection Pipeline
# ============================================================================
# This script orchestrates the entire data curation workflow:
#   1. Web scraping for award data (optional, controlled by flag)
#   2. API calls to fetch book metadata and reception metrics
#   3. Data merging and integration with entity resolution
#
# Usage:
#   ./run_pipeline.sh                    # Run full pipeline
#   ./run_pipeline.sh --skip-scraping    # Skip Wikipedia scraping (use pre-fetched awards data)
#   ./run_pipeline.sh --merge-only       # Only run merge step (assumes all data fetched)
# ============================================================================

set -e  # Exit on error

# ============================================================================
# CONFIGURATION FLAGS (defaults)
# ============================================================================

# Set to "true" to run web scraping for awards data
# Set to "false" to use existing JSON files in data/ folder
RUN_WEB_SCRAPING="true"

# Set to "true" to fetch data from Google Books API
RUN_GOOGLE_BOOKS="true"

# Set to "true" to fetch data from Open Library API
RUN_OPEN_LIBRARY="true"

# Set to "true" to fetch data from NYT Bestsellers API
RUN_NYT_BESTSELLERS="true"

# Set to "true" to run the dataset merge
RUN_MERGE="true"

# ============================================================================
# PARSE COMMAND LINE ARGUMENTS
# ============================================================================

for arg in "$@"; do
    case $arg in
        --skip-scraping)
            RUN_WEB_SCRAPING="false"
            echo "Note: Skipping Wikipedia scraping (using pre-fetched awards data)"
            shift
            ;;
        --merge-only)
            RUN_WEB_SCRAPING="false"
            RUN_GOOGLE_BOOKS="false"
            RUN_OPEN_LIBRARY="false"
            RUN_NYT_BESTSELLERS="false"
            echo "Note: Running merge step only"
            shift
            ;;
        --help|-h)
            echo "Usage: ./run_pipeline.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-scraping    Skip Wikipedia scraping, use pre-fetched awards data"
            echo "  --merge-only       Only run merge step (assumes all data already fetched)"
            echo "  --help, -h         Show this help message"
            exit 0
            ;;
        *)
            # Unknown option
            ;;
    esac
done

# ============================================================================
# END CONFIGURATION
# ============================================================================

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "================================================================"
echo "                                                                "
echo "    LITERARY AWARDS & BOOK RECEPTION DATA CURATION PIPELINE    "
echo "                                                                "
echo "================================================================"
echo ""
echo "Configuration:"
echo "  Web Scraping (Awards):    ${RUN_WEB_SCRAPING}"
echo "  Google Books API:         ${RUN_GOOGLE_BOOKS}"
echo "  Open Library API:         ${RUN_OPEN_LIBRARY}"
echo "  NYT Bestsellers API:      ${RUN_NYT_BESTSELLERS}"
echo "  Dataset Merge:            ${RUN_MERGE}"
echo ""

# ============================================================================
# SETUP: Virtual Environment and Dependencies
# ============================================================================

echo "================================================================"
echo "SETUP: Environment and Dependencies"
echo "================================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "[OK] Virtual environment created"
else
    echo "[OK] Virtual environment found"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
echo "Checking dependencies..."
if ! python -c "import requests, bs4, pandas" 2>/dev/null; then
    echo "Installing required packages..."
    pip install -q -r requirements.txt
    echo "[OK] Dependencies installed"
else
    echo "[OK] Dependencies already installed"
fi

echo ""

# ============================================================================
# STAGE 1: Web Scraping for Awards Data (Optional)
# ============================================================================

if [ "$RUN_WEB_SCRAPING" = "true" ]; then
    echo "================================================================"
    echo "STAGE 1: Web Scraping - Literary Awards Data"
    echo "================================================================"
    echo ""
    echo "Scraping award data from Wikipedia..."
    echo "Sources: Pulitzer Prize, National Book Award, Booker Prize"
    echo ""
    
    python run_scrapers.py
    SCRAPER_EXIT_CODE=$?
    
    if [ $SCRAPER_EXIT_CODE -ne 0 ]; then
        echo ""
        echo "[ERROR] Web scraping failed with exit code $SCRAPER_EXIT_CODE"
        exit 1
    fi
    
    echo ""
    echo "[OK] Stage 1 Complete: Awards data scraped successfully"
    echo ""
else
    echo "================================================================"
    echo "STAGE 1: Web Scraping - SKIPPED"
    echo "================================================================"
    echo ""
    echo "Web scraping skipped (RUN_WEB_SCRAPING=false)"
    echo "Using existing JSON files in data/ folder"
    echo ""
    
    # Verify that award JSON files exist
    if [ ! -f "data/pulitzer_prize.json" ] || [ ! -f "data/national_book_award.json" ] || [ ! -f "data/booker_prize.json" ]; then
        echo "[ERROR] Award JSON files not found in data/ folder"
        echo "  Please set RUN_WEB_SCRAPING=true or ensure JSON files exist"
        exit 1
    fi
    echo "[OK] Stage 1 Complete: Using existing awards data"
    echo ""
fi

# ============================================================================
# STAGE 2: API Data Collection - Google Books
# ============================================================================

if [ "$RUN_GOOGLE_BOOKS" = "true" ]; then
    echo "================================================================"
    echo "STAGE 2A: API Data Collection - Google Books"
    echo "================================================================"
    echo ""
    echo "Fetching bibliographic metadata from Google Books API..."
    echo "Target: Fiction books (2020-2025)"
    echo ""
    
    python fetch_google_books.py
    GB_EXIT_CODE=$?
    
    if [ $GB_EXIT_CODE -ne 0 ]; then
        echo ""
        echo "[ERROR] Google Books API fetch failed with exit code $GB_EXIT_CODE"
        exit 1
    fi
    
    echo ""
    echo "[OK] Stage 2A Complete: Google Books data fetched successfully"
    echo ""
else
    echo "================================================================"
    echo "STAGE 2A: Google Books API - SKIPPED"
    echo "================================================================"
    echo ""
    echo "Google Books API skipped (RUN_GOOGLE_BOOKS=false)"
    echo ""
fi

# ============================================================================
# STAGE 3: API Data Collection - Open Library
# ============================================================================

if [ "$RUN_OPEN_LIBRARY" = "true" ]; then
    echo "================================================================"
    echo "STAGE 2B: API Data Collection - Open Library"
    echo "================================================================"
    echo ""
    echo "Fetching public reception metrics from Open Library API..."
    echo "Target: Fiction books with ratings and readership data (2020-2025)"
    echo ""
    
    python fetch_openlibrary_books.py
    OL_EXIT_CODE=$?
    
    if [ $OL_EXIT_CODE -ne 0 ]; then
        echo ""
        echo "[ERROR] Open Library API fetch failed with exit code $OL_EXIT_CODE"
        exit 1
    fi
    
    echo ""
    echo "[OK] Stage 2B Complete: Open Library data fetched successfully"
    echo ""
else
    echo "================================================================"
    echo "STAGE 2B: Open Library API - SKIPPED"
    echo "================================================================"
    echo ""
    echo "Open Library API skipped (RUN_OPEN_LIBRARY=false)"
    echo ""
fi

# ============================================================================
# STAGE 4: API Data Collection - NYT Bestsellers
# ============================================================================

if [ "$RUN_NYT_BESTSELLERS" = "true" ]; then
    echo "================================================================"
    echo "STAGE 2C: API Data Collection - NYT Bestsellers"
    echo "================================================================"
    echo ""
    echo "Fetching commercial success metrics from NYT Books API..."
    echo "Target: Fiction bestsellers (2020-2025)"
    echo "[NOTE] This may take several minutes due to API rate limits"
    echo ""
    
    python fetch_nyt_books.py
    NYT_EXIT_CODE=$?
    
    if [ $NYT_EXIT_CODE -ne 0 ]; then
        echo ""
        echo "[ERROR] NYT Bestsellers API fetch failed with exit code $NYT_EXIT_CODE"
        exit 1
    fi
    
    echo ""
    echo "[OK] Stage 2C Complete: NYT Bestsellers data fetched successfully"
    echo ""
else
    echo "================================================================"
    echo "STAGE 2C: NYT Bestsellers API - SKIPPED"
    echo "================================================================"
    echo ""
    echo "NYT Bestsellers API skipped (RUN_NYT_BESTSELLERS=false)"
    echo ""
fi

# ============================================================================
# STAGE 5: Data Integration and Merging
# ============================================================================

if [ "$RUN_MERGE" = "true" ]; then
    echo "================================================================"
    echo "STAGE 3: Data Integration and Merging"
    echo "================================================================"
    echo ""
    echo "Merging all datasets with entity resolution..."
    echo "Strategy: ISBN matching -> Fuzzy title-author matching"
    echo ""
    
    python merge_datasets.py
    MERGE_EXIT_CODE=$?
    
    if [ $MERGE_EXIT_CODE -ne 0 ]; then
        echo ""
        echo "[ERROR] Dataset merge failed with exit code $MERGE_EXIT_CODE"
        exit 1
    fi
    
    echo ""
    echo "[OK] Stage 3 Complete: Datasets merged successfully"
    echo ""
    
    # Verify merge output
    if [ ! -f "merged_data/merged_literary_books.json" ]; then
        echo "[ERROR] Merged dataset not found"
        exit 1
    fi
else
    echo "================================================================"
    echo "STAGE 3: Data Merging - SKIPPED"
    echo "================================================================"
    echo ""
    echo "Dataset merge skipped (RUN_MERGE=false)"
    echo ""
fi

# ============================================================================
# PIPELINE SUMMARY
# ============================================================================

echo ""
echo "================================================================"
echo "                                                                "
echo "                   PIPELINE COMPLETED                           "
echo "                                                                "
echo "================================================================"
echo ""

echo "Output Files:"
echo ""

echo "Individual Data Sources:"
if [ -f "data/pulitzer_prize.json" ]; then
    echo "  [OK] data/pulitzer_prize.json"
fi
if [ -f "data/national_book_award.json" ]; then
    echo "  [OK] data/national_book_award.json"
fi
if [ -f "data/booker_prize.json" ]; then
    echo "  [OK] data/booker_prize.json"
fi
if [ -f "data/google_books.json" ]; then
    echo "  [OK] data/google_books.json"
fi
if [ -f "data/openlibrary_books.json" ]; then
    echo "  [OK] data/openlibrary_books.json"
fi
if [ -f "data/nyt_bestsellers.json" ]; then
    echo "  [OK] data/nyt_bestsellers.json"
fi
echo ""

echo "Merged Dataset:"
if [ -f "merged_data/merged_literary_books.json" ]; then
    echo "  [OK] merged_data/merged_literary_books.json (Primary output)"
fi
echo ""

echo "Reports and Metadata:"
if [ -f "merged_data/merge_report.json" ]; then
    echo "  [OK] merged_data/merge_report.json"
fi
if [ -f "merged_data/unmatched_google_books.json" ]; then
    echo "  [OK] merged_data/unmatched_google_books.json"
fi
if [ -f "merged_data/unmatched_openlibrary.json" ]; then
    echo "  [OK] merged_data/unmatched_openlibrary.json"
fi
if [ -f "merged_data/unmatched_nyt_bestsellers.json" ]; then
    echo "  [OK] merged_data/unmatched_nyt_bestsellers.json"
fi
echo ""

echo "Backups:"
if [ -d "data_backup" ] && [ "$(ls -A data_backup 2>/dev/null)" ]; then
    echo "  [OK] data_backup/ (Timestamped backups of previous runs)"
fi
echo ""

echo "Next Steps:"
echo "  - View merge statistics: cat merged_data/merge_report.json"
echo "  - Analyze the data: python -m json.tool merged_data/merged_literary_books.json"
echo "  - Re-run with different settings by editing flags at the top of run_pipeline.sh"
echo ""

echo "All done!"
echo ""

