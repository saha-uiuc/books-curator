# API Keys Reference

**NOTE: The code reads API keys from environment variables, not from this file. API keys are shared separately with course staff. **

## Required API Keys

### Google Books API
- **Environment Variable:** `GOOGLE_BOOKS_API_KEY`
- **Key:** `***`
- **Documentation:** https://developers.google.com/books/docs/v1/using

### New York Times Books API
- **Environment Variable:** `NYT_BOOKS_API_KEY`
- **Key:** `***`
- **Documentation:** https://developer.nytimes.com/docs/books-product/1/overview

### Open Library API
- **Environment Variable:** Not required (no API key needed)
- **Documentation:** https://openlibrary.org/developers/api

## Usage

Set environment variables before running scripts:

```bash
export GOOGLE_BOOKS_API_KEY="AIzaSyA1DjQVSOBDlvlligfxGsLsVgubBRrBzvI"
export NYT_BOOKS_API_KEY="qn9W553JGmpOq4bFYWxSWQuOBrkXpfJA"

# Then run the pipeline
./run_pipeline.sh
```

Or create a `.env` file (add to `.gitignore`):

```
GOOGLE_BOOKS_API_KEY=AIzaSyA1DjQVSOBDlvlligfxGsLsVgubBRrBzvI
NYT_BOOKS_API_KEY=qn9W553JGmpOq4bFYWxSWQuOBrkXpfJA
```

