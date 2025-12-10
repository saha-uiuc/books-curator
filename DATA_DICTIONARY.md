# Data Dictionary

## CS598 FDC Final Project: Literary Awards and Book Reception Dataset

**Dataset Name:** Critical Acclaim vs. Reader Popularity: Integrated Literary Dataset  
**Version:** 1.0  
**Last Updated:** December 10, 2025  
**Author:** Somnath Saha (somnath4@illinois.edu)  
**License:** CC BY 4.0 (Data), MIT (Code)

---

## Table of Contents

1. [Dataset Overview](#dataset-overview)
2. [File Structure](#file-structure)
3. [Field Definitions](#field-definitions)
4. [Data Types and Constraints](#data-types-and-constraints)
5. [Enumerated Values](#enumerated-values)
6. [Source Provenance](#source-provenance)
7. [Data Quality Notes](#data-quality-notes)
8. [Schema.org Metadata](#schemaorg-metadata)
9. [Example Records](#example-records)

---

## 1. Dataset Overview

### Primary File
**`merged_data/merged_literary_books.json`**

### Description
A curated, integrated dataset of 1,538 unique English-language fiction books combining data from:
- 3 major literary awards (Pulitzer Prize, National Book Award, Booker Prize)
- 3 bibliographic/reception APIs (Google Books, Open Library, New York Times)

### Temporal Coverage
- **Awards data:** 2000-2025 (25 years)
- **API data:** 2020-2025 (5 years)

### Geographic/Linguistic Scope
- English-language fiction
- Primarily U.S. and U.K. publications
- International authors eligible for major awards

### Record Count
1,538 unique books

### Format
JSON (JavaScript Object Notation)
- Encoding: UTF-8
- Specification: RFC 8259 / ECMA-404

---

## 2. File Structure

### JSON Structure

```json
{
  "metadata": {
    "title": "Merged Literary Awards and Book Reception Dataset",
    "description": "Integrated dataset...",
    "version": "1.0",
    "created_date": "YYYY-MM-DDTHH:MM:SSZ",
    "total_books": 1538,
    "sources": ["awards", "google_books", "openlibrary", "nyt_bestsellers"],
    "integration_method": "ISBN matching + fuzzy title-author matching",
    "match_threshold": 0.85
  },
  "books": [
    {
      "book_id": 1,
      "title": "...",
      ...
    },
    ...
  ]
}
```

---

## 3. Field Definitions

### 3.1 Core Identifiers

#### `book_id`
- **Description:** System-generated unique identifier for internal referencing
- **Data Type:** Integer
- **Nullable:** No
- **Constraints:** Sequential integers starting from 1; unique within dataset
- **Example:** `1`, `42`, `1538`
- **Usage:** Join key for linking to external analysis tables

#### `isbn_13`
- **Description:** 13-digit International Standard Book Number (ISBN-13)
- **Data Type:** String
- **Nullable:** Yes (28% of books lack ISBN-13)
- **Format:** 13 digits, no hyphens (e.g., "9780385537070")
- **Standard:** ISO 2108
- **Source:** Google Books, Open Library, NYT Bestsellers
- **Usage:** Primary identifier for cross-dataset matching

#### `isbn_10`
- **Description:** 10-digit International Standard Book Number (ISBN-10)
- **Data Type:** String
- **Nullable:** Yes (31% of books lack ISBN-10)
- **Format:** 10 characters (9 digits + check digit, which may be 'X'), no hyphens
- **Standard:** ISO 2108 (deprecated but still widely used)
- **Source:** Google Books, Open Library, NYT Bestsellers
- **Usage:** Secondary identifier for cross-dataset matching

#### `isbn_all`
- **Description:** Array of all known ISBNs for this book (both ISBN-10 and ISBN-13, multiple editions)
- **Data Type:** Array of Strings
- **Nullable:** Yes (empty array if no ISBNs available)
- **Format:** Each element is a string (10 or 13 characters, no hyphens)
- **Source:** Aggregated from all data sources
- **Example:** `["9780385537070", "0385537077", "9780307946171"]`
- **Usage:** Maximizes linkage opportunities across editions

#### `identifiers`
- **Description:** Object containing external identifiers for linking to original data sources
- **Data Type:** Object (key-value pairs)
- **Nullable:** Yes (fields within object are individually nullable)
- **Sub-fields:**
  - `google_books_id`: String, Google Books unique identifier (e.g., "xGZmDwAAQBAJ")
  - `openlibrary_key`: String, Open Library work key (e.g., "/works/OL20028467W")
- **Source:** Google Books API, Open Library API
- **Usage:** Enable programmatic retrieval of full records from original APIs

---

### 3.2 Bibliographic Metadata

#### `title`
- **Description:** Book title (normalized, primary edition)
- **Data Type:** String
- **Nullable:** No (required field)
- **Constraints:** Non-empty; cleaned of footnote markers and extra whitespace
- **Normalization:** Leading/trailing whitespace removed; citation markers ([1], [2], etc.) removed
- **Source:** All sources (priority: Awards > Google Books > Open Library > NYT)
- **Example:** `"The Nickel Boys"`, `"There There"`
- **Usage:** Display name; fuzzy matching (when normalized further)

#### `author`
- **Description:** Primary author name
- **Data Type:** String
- **Nullable:** No (required field)
- **Format:** Typically "Firstname Lastname" or "Firstname Middlename Lastname"
- **Normalization:** Birth/death years removed (e.g., "(1962–)" → ""); extra whitespace removed
- **Source:** All sources (priority: Awards > Google Books > Open Library > NYT)
- **Example:** `"Colson Whitehead"`, `"Tommy Orange"`
- **Note:** For multi-author books, only the first/primary author is recorded
- **Usage:** Display; author-based filtering and grouping

#### `year`
- **Description:** Publication year (first edition, or award year if publication year unavailable)
- **Data Type:** Integer
- **Nullable:** No (required field, though may be award year as proxy)
- **Constraints:** 1900 ≤ year ≤ 2025 (validation range)
- **Source:** All sources (priority: Google Books > Awards > Open Library)
- **Example:** `2019`, `2023`
- **Usage:** Temporal filtering and analysis; cohort grouping

#### `publisher`
- **Description:** Publishing house / publisher name
- **Data Type:** String
- **Nullable:** Yes (22% of books missing publisher)
- **Format:** Official publisher name (may include imprint)
- **Source:** Google Books (primary), Awards (for winners), Open Library
- **Example:** `"Doubleday"`, `"Alfred A. Knopf"`, `"Penguin Random House"`
- **Usage:** Publisher analysis; quality indicator

#### `page_count`
- **Description:** Number of pages in the book
- **Data Type:** Integer
- **Nullable:** Yes (76% of books missing page count - only available from Google Books)
- **Constraints:** > 0 (if present)
- **Source:** Google Books API only
- **Example:** `224`, `437`
- **Usage:** Book length analysis; reading time estimation

#### `language`
- **Description:** Primary language of the book
- **Data Type:** String
- **Nullable:** Yes (59% of books missing language code)
- **Format:** ISO 639-1 two-letter language code
- **Standard:** ISO 639-1
- **Source:** Google Books API
- **Example:** `"en"` (English), `"es"` (Spanish)
- **Usage:** Language filtering (though dataset focuses on English-language fiction)

#### `categories`
- **Description:** Array of genre/subject classifications
- **Data Type:** Array of Strings
- **Nullable:** Yes (58% of books missing categories)
- **Source:** Google Books (primary), Open Library (supplementary)
- **Example:** `["Fiction", "Literary", "Historical Fiction"]`
- **Usage:** Genre analysis; subject-based filtering

#### `description`
- **Description:** Book description / synopsis
- **Data Type:** String (long text)
- **Nullable:** Yes (not included by default to reduce file size; available from original APIs)
- **Source:** Google Books API, Open Library API
- **Note:** Omitted from main dataset due to length; can be fetched using `identifiers`
- **Usage:** Full-text search; content analysis (if needed)

---

### 3.3 Awards Data

#### `awards`
- **Description:** Array of award objects detailing all award appearances for this book
- **Data Type:** Array of Objects
- **Nullable:** Yes (empty array if no awards)
- **Source:** Awards data (Pulitzer, NBA, Booker)
- **Sub-schema:**
  ```json
  {
    "award_name": "String",  // e.g., "Pulitzer Prize for Fiction"
    "year": Integer,          // Year awarded
    "status": "String",       // "Winner", "Finalist", "Shortlist"
    "publisher": "String|null" // Publisher at time of award (if recorded)
  }
  ```
- **Example:**
  ```json
  [
    {
      "award_name": "Pulitzer Prize for Fiction",
      "year": 2020,
      "status": "Winner",
      "publisher": "Doubleday"
    },
    {
      "award_name": "National Book Award for Fiction",
      "year": 2019,
      "status": "Finalist",
      "publisher": null
    }
  ]
  ```
- **Usage:** Award-based filtering; multi-award analysis

#### `award_count`
- **Description:** Total number of award appearances (sum of all awards entries)
- **Data Type:** Integer
- **Nullable:** No (0 if no awards)
- **Constraints:** ≥ 0
- **Source:** Derived (calculated from `awards` array length)
- **Example:** `0`, `1`, `3`
- **Usage:** Quick filtering for awarded books; prestige indicator

#### `won_award`
- **Description:** Boolean flag indicating whether this book won any award (status="Winner")
- **Data Type:** Boolean
- **Nullable:** No
- **Derivation:** `true` if any award in `awards` array has `status="Winner"`
- **Source:** Derived from `awards` array
- **Example:** `true`, `false`
- **Usage:** Binary classification (winner vs. non-winner)

#### `shortlisted`
- **Description:** Boolean flag indicating whether this book was shortlisted/finalist for any award without winning
- **Data Type:** Boolean
- **Nullable:** No
- **Derivation:** `true` if any award has `status="Finalist"` or `"Shortlist"` but none have `status="Winner"`
- **Source:** Derived from `awards` array
- **Example:** `true`, `false`
- **Usage:** Distinguish finalists from winners and non-nominated books

---

### 3.4 Public Reception Metrics

All fields in this section are sourced from **Open Library API**.

#### `ratings_average`
- **Description:** Average reader rating on a 1.0 to 5.0 scale
- **Data Type:** Float
- **Nullable:** Yes (51% of books missing ratings)
- **Constraints:** 1.0 ≤ value ≤ 5.0 (if present)
- **Precision:** Typically 2 decimal places
- **Source:** Open Library API (aggregated user ratings)
- **Example:** `3.89`, `4.12`, `3.5`
- **Usage:** Quality indicator; correlation with awards

#### `ratings_count`
- **Description:** Total number of user ratings
- **Data Type:** Integer
- **Nullable:** Yes (51% of books missing ratings)
- **Constraints:** ≥ 0 (if present)
- **Source:** Open Library API
- **Example:** `47235`, `1203`, `156`
- **Usage:** Sample size for statistical significance; popularity indicator

#### `want_to_read_count`
- **Description:** Number of users who marked this book as "want to read"
- **Data Type:** Integer
- **Nullable:** Yes (51% of books missing)
- **Constraints:** ≥ 0 (if present)
- **Source:** Open Library API
- **Example:** `12453`, `789`
- **Usage:** Interest indicator; popularity forecast

#### `currently_reading_count`
- **Description:** Number of users currently reading this book
- **Data Type:** Integer
- **Nullable:** Yes (51% of books missing)
- **Constraints:** ≥ 0 (if present)
- **Source:** Open Library API
- **Example:** `2341`, `56`
- **Usage:** Current engagement indicator; trending analysis

#### `already_read_count`
- **Description:** Number of users who have marked this book as read
- **Data Type:** Integer
- **Nullable:** Yes (51% of books missing)
- **Constraints:** ≥ 0 (if present)
- **Source:** Open Library API
- **Example:** `45678`, `3210`
- **Usage:** Historical readership; completed reads indicator

---

### 3.5 Commercial Success Metrics

All fields in this section are sourced from **New York Times Books API**.

#### `bestseller_appearances`
- **Description:** Number of times this book appeared on any NYT bestseller list
- **Data Type:** Integer
- **Nullable:** Yes (0 or null if never on bestseller list; 82% of books)
- **Constraints:** ≥ 0
- **Source:** NYT Books API (aggregated from bestseller list appearances)
- **Example:** `3`, `15`, `0`
- **Usage:** Commercial success indicator; popularity metric

#### `total_weeks_on_bestseller`
- **Description:** Cumulative number of weeks this book appeared on bestseller lists
- **Data Type:** Integer
- **Nullable:** Yes (0 or null if never on list)
- **Constraints:** ≥ 0; ≥ `bestseller_appearances` (since each appearance is ≥1 week)
- **Source:** NYT Books API (summed from all list appearances)
- **Example:** `8`, `52`, `0`
- **Usage:** Longevity of commercial success; sales proxy

#### `highest_rank`
- **Description:** Best (lowest number) ranking achieved on any NYT bestseller list
- **Data Type:** Integer
- **Nullable:** Yes (null if never on list)
- **Constraints:** 1 ≤ value ≤ 15 (NYT lists typically show top 15)
- **Source:** NYT Books API (minimum rank across all appearances)
- **Example:** `1`, `7`, `12`
- **Usage:** Peak commercial success indicator; #1 bestseller flag

#### `bestseller_dates`
- **Description:** Array of dates (YYYY-MM-DD) when this book appeared on bestseller lists
- **Data Type:** Array of Strings (ISO 8601 dates)
- **Nullable:** Yes (empty array if never on list)
- **Format:** Each element is "YYYY-MM-DD"
- **Source:** NYT Books API (list publication dates)
- **Example:** `["2019-08-04", "2019-08-11", "2019-08-18"]`
- **Usage:** Temporal analysis; correlation with award announcements

---

### 3.6 Provenance and Metadata

#### `sources`
- **Description:** Array of data source identifiers indicating which sources contributed to this book record
- **Data Type:** Array of Strings
- **Nullable:** No (always has at least one source)
- **Allowed Values:** 
  - `"awards"` - Data from literary awards (Pulitzer, NBA, Booker)
  - `"google_books"` - Data from Google Books API
  - `"openlibrary"` - Data from Open Library API
  - `"nyt_bestsellers"` - Data from NYT Bestsellers API
- **Example:** `["awards", "google_books", "openlibrary"]`
- **Usage:** Data provenance tracking; filtering by source completeness

---

## 4. Data Types and Constraints

### Summary Table

| Field Name | Type | Nullable | Validation | Example |
|------------|------|----------|------------|---------|
| `book_id` | Integer | No | > 0, unique | `42` |
| `isbn_13` | String | Yes | 13 digits, no hyphens | `"9780385537070"` |
| `isbn_10` | String | Yes | 10 chars, no hyphens | `"0385537077"` |
| `isbn_all` | Array[String] | Yes | Each: 10 or 13 chars | `["978...", "038..."]` |
| `identifiers` | Object | Yes | Valid object or null | `{"google_books_id": "..."}` |
| `title` | String | No | Non-empty | `"The Nickel Boys"` |
| `author` | String | No | Non-empty | `"Colson Whitehead"` |
| `year` | Integer | No | 1900-2025 | `2019` |
| `publisher` | String | Yes | N/A | `"Doubleday"` |
| `page_count` | Integer | Yes | > 0 | `224` |
| `language` | String | Yes | ISO 639-1 (2 chars) | `"en"` |
| `categories` | Array[String] | Yes | N/A | `["Fiction", "Literary"]` |
| `awards` | Array[Object] | Yes | Valid award objects | See sub-schema |
| `award_count` | Integer | No | ≥ 0 | `1` |
| `won_award` | Boolean | No | true or false | `true` |
| `shortlisted` | Boolean | No | true or false | `false` |
| `ratings_average` | Float | Yes | 1.0-5.0 | `3.89` |
| `ratings_count` | Integer | Yes | ≥ 0 | `47235` |
| `want_to_read_count` | Integer | Yes | ≥ 0 | `12453` |
| `currently_reading_count` | Integer | Yes | ≥ 0 | `2341` |
| `already_read_count` | Integer | Yes | ≥ 0 | `45678` |
| `bestseller_appearances` | Integer | Yes | ≥ 0 | `3` |
| `total_weeks_on_bestseller` | Integer | Yes | ≥ 0 | `8` |
| `highest_rank` | Integer | Yes | 1-15 | `2` |
| `bestseller_dates` | Array[String] | Yes | ISO 8601 dates | `["2019-08-04"]` |
| `sources` | Array[String] | No | Valid source IDs | `["awards", "google_books"]` |

---

## 5. Enumerated Values

### `awards[].status`
- **Winner** - Book won the award
- **Finalist** - Book was a finalist for the award (used by Pulitzer, National Book Award)
- **Shortlist** - Book was on the shortlist (used by Booker Prize)

### `sources[]` (Possible Values)
- **awards** - Pulitzer Prize, National Book Award, or Booker Prize
- **google_books** - Google Books API
- **openlibrary** - Open Library API
- **nyt_bestsellers** - New York Times Books API

### `awards[].award_name` (Possible Values)
- **Pulitzer Prize for Fiction**
- **National Book Award for Fiction**
- **Booker Prize**

---

## 6. Source Provenance

### Field-to-Source Mapping

| Field | Primary Source | Secondary/Supplementary Sources | Notes |
|-------|----------------|----------------------------------|-------|
| `book_id` | System-generated | N/A | Unique per book |
| `isbn_13`, `isbn_10`, `isbn_all` | Google Books | Open Library, NYT | Aggregated from all |
| `identifiers` | Google Books, Open Library | N/A | External IDs |
| `title` | Awards | Google Books, Open Library, NYT | Priority: Awards > Google > OL > NYT |
| `author` | Awards | Google Books, Open Library, NYT | Priority: Awards > Google > OL > NYT |
| `year` | Google Books | Awards, Open Library | Publication year preferred |
| `publisher` | Google Books | Awards (winners only) | Awards include publisher for winners |
| `page_count` | Google Books | N/A | Only source |
| `language` | Google Books | N/A | Only source |
| `categories` | Google Books | Open Library | Merged when both available |
| `awards`, `award_count`, `won_award`, `shortlisted` | Awards | N/A | Only source |
| `ratings_average`, `ratings_count`, `want_to_read_count`, `currently_reading_count`, `already_read_count` | Open Library | N/A | Only source |
| `bestseller_appearances`, `total_weeks_on_bestseller`, `highest_rank`, `bestseller_dates` | NYT Books | N/A | Only source |
| `sources` | System-derived | N/A | Tracks contributing sources |

---

## 7. Data Quality Notes

### Completeness by Field Category

| Category | Completeness | Notes |
|----------|--------------|-------|
| Core Identifiers (book_id, title, author, year) | **100%** | Required fields |
| ISBNs | **83.7%** | Awards data often lacks ISBNs (older/non-U.S. editions) |
| Publisher | **78.2%** | Variable across sources |
| Page Count | **24.3%** | Only from Google Books (318/1538) |
| Language | **41.2%** | Only from Google Books |
| Categories | **41.5%** | From Google Books, sometimes Open Library |
| Reader Ratings | **49.4%** | Limited to Open Library matches |
| Bestseller Metrics | **17.6%** | Limited to NYT matches |
| Awards Information | **12.8%** | By design (award winners/finalists only) |

### Missing Data Patterns

1. **Awards Books Without API Data:** 78.3% of award entries (455/581) lack matches to Google Books, Open Library, or NYT
   - Reason: Publication dates outside 2020-2025 API data collection window, or international editions without ISBNs

2. **API Books Without Awards:** 95% of Google Books and 93% of Open Library books are not award-related
   - Expected: Awards represent a small subset of published fiction

3. **ISBN Gaps:** 17% of books lack ISBNs
   - Reason: Older books (pre-ISBN standardization), non-U.S. editions, galley copies

### Data Quality Improvements Applied

- ✅ Text normalization (whitespace, punctuation, citation markers)
- ✅ Date standardization (ISO 8601 format)
- ✅ Null handling (explicit `null` vs. empty string vs. omission)
- ✅ ISBN normalization (remove hyphens, validate check digits)
- ✅ Duplicate removal (within each source before merge)
- ✅ Outlier detection (year validation 1900-2025)

### Known Limitations

1. **Temporal Misalignment:** Award data (2000-2025) broader than API data (2020-2025)
2. **NYT Sampling:** Every 3 months (not exhaustive weekly coverage) due to rate limits
3. **Fuzzy Matching Trade-offs:** 0.85 threshold balances precision vs. recall; some legitimate matches may be missed
4. **Language Bias:** Dataset focuses on English-language fiction published in U.S./U.K.

---

## 8. Schema.org Metadata

### Dataset-Level Metadata (JSON-LD)

```json
{
  "@context": "https://schema.org/",
  "@type": "Dataset",
  "name": "Critical Acclaim vs. Reader Popularity: Integrated Literary Dataset",
  "description": "A curated, integrated dataset of 1,538 unique English-language fiction books (2000-2025) combining data from major literary awards (Pulitzer Prize, National Book Award, Booker Prize) and bibliographic/reception APIs (Google Books, Open Library, New York Times Bestsellers). Created to investigate the relationship between critical acclaim, public reception, and commercial success in contemporary literature.",
  "url": "https://github.com/[username]/cs598-fdc-literary-awards",
  "identifier": "https://doi.org/10.XXXXX/XXXXX",
  "keywords": [
    "literary awards",
    "book reception",
    "bibliographic data",
    "data curation",
    "entity resolution",
    "Pulitzer Prize",
    "National Book Award",
    "Booker Prize",
    "bestsellers",
    "reader ratings",
    "data integration"
  ],
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "creator": {
    "@type": "Person",
    "name": "Somnath Saha",
    "email": "somnath4@illinois.edu",
    "affiliation": {
      "@type": "Organization",
      "name": "University of Illinois at Urbana-Champaign",
      "url": "https://illinois.edu"
    }
  },
  "dateCreated": "2025-10-01",
  "dateModified": "2025-12-10",
  "datePublished": "2025-12-10",
  "version": "1.0",
  "temporalCoverage": "2000-01-01/2025-12-31",
  "spatialCoverage": {
    "@type": "Place",
    "name": "United States and United Kingdom"
  },
  "distribution": [
    {
      "@type": "DataDownload",
      "encodingFormat": "application/json",
      "contentUrl": "https://github.com/[username]/cs598-fdc-literary-awards/raw/main/merged_data/merged_literary_books.json",
      "name": "Merged Literary Books Dataset (JSON)"
    }
  ],
  "isBasedOn": [
    {
      "@type": "CreativeWork",
      "name": "Pulitzer Prize for Fiction (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/Pulitzer_Prize_for_Fiction",
      "license": "https://creativecommons.org/licenses/by-sa/3.0/"
    },
    {
      "@type": "CreativeWork",
      "name": "National Book Award for Fiction (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/National_Book_Award_for_Fiction",
      "license": "https://creativecommons.org/licenses/by-sa/3.0/"
    },
    {
      "@type": "CreativeWork",
      "name": "Booker Prize (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/List_of_winners_and_nominated_authors_of_the_Booker_Prize",
      "license": "https://creativecommons.org/licenses/by-sa/3.0/"
    },
    {
      "@type": "WebAPI",
      "name": "Google Books API",
      "url": "https://developers.google.com/books",
      "provider": {
        "@type": "Organization",
        "name": "Google"
      }
    },
    {
      "@type": "WebAPI",
      "name": "Open Library API",
      "url": "https://openlibrary.org/developers/api",
      "provider": {
        "@type": "Organization",
        "name": "Internet Archive"
      },
      "license": "https://creativecommons.org/publicdomain/zero/1.0/"
    },
    {
      "@type": "WebAPI",
      "name": "New York Times Books API",
      "url": "https://developer.nytimes.com/docs/books-product/1/overview.html",
      "provider": {
        "@type": "Organization",
        "name": "The New York Times"
      }
    }
  ],
  "variableMeasured": [
    {
      "@type": "PropertyValue",
      "name": "title",
      "description": "Book title (normalized)"
    },
    {
      "@type": "PropertyValue",
      "name": "author",
      "description": "Primary author name"
    },
    {
      "@type": "PropertyValue",
      "name": "year",
      "description": "Publication year (first edition)",
      "unitText": "year"
    },
    {
      "@type": "PropertyValue",
      "name": "isbn_13",
      "description": "13-digit International Standard Book Number"
    },
    {
      "@type": "PropertyValue",
      "name": "ratings_average",
      "description": "Average reader rating (1.0-5.0 scale)",
      "minValue": 1.0,
      "maxValue": 5.0
    },
    {
      "@type": "PropertyValue",
      "name": "ratings_count",
      "description": "Total number of reader ratings",
      "unitText": "count"
    },
    {
      "@type": "PropertyValue",
      "name": "bestseller_appearances",
      "description": "Number of times on NYT bestseller list",
      "unitText": "count"
    },
    {
      "@type": "PropertyValue",
      "name": "total_weeks_on_bestseller",
      "description": "Cumulative weeks on bestseller lists",
      "unitText": "week"
    },
    {
      "@type": "PropertyValue",
      "name": "award_count",
      "description": "Total number of award appearances",
      "unitText": "count"
    },
    {
      "@type": "PropertyValue",
      "name": "won_award",
      "description": "Boolean flag: won any award",
      "valueReference": {
        "@type": "PropertyValue",
        "value": ["true", "false"]
      }
    }
  ],
  "measurementTechnique": "Data integration using ISBN matching (primary) and fuzzy title-author matching (fallback, threshold 0.85). Web scraping for literary awards data; REST API calls for bibliographic, reception, and commercial data. Entity resolution applied to merge 1,760 source entries into 1,538 unique books.",
  "citation": "Saha, S. (2025). Critical Acclaim vs. Reader Popularity: Curating an Integrated Dataset of Literary Awards and Book Reception. CS598 Foundations of Data Curation Final Project, University of Illinois at Urbana-Champaign."
}
```

---

## 9. Example Records

### Example 1: Award Winner with Full Data

```json
{
  "book_id": 1,
  "title": "The Nickel Boys",
  "author": "Colson Whitehead",
  "year": 2019,
  "isbn_13": "9780385537070",
  "isbn_10": "0385537077",
  "isbn_all": ["9780385537070", "0385537077"],
  "publisher": "Doubleday",
  "page_count": 224,
  "language": "en",
  "categories": ["Fiction", "Literary", "Historical Fiction"],
  "awards": [
    {
      "award_name": "Pulitzer Prize for Fiction",
      "year": 2020,
      "status": "Winner",
      "publisher": "Doubleday"
    }
  ],
  "award_count": 1,
  "won_award": true,
  "shortlisted": false,
  "ratings_average": 3.89,
  "ratings_count": 47235,
  "want_to_read_count": 12453,
  "currently_reading_count": 2341,
  "already_read_count": 45678,
  "bestseller_appearances": 3,
  "total_weeks_on_bestseller": 8,
  "highest_rank": 2,
  "bestseller_dates": ["2019-08-04", "2019-08-11", "2019-08-18"],
  "identifiers": {
    "google_books_id": "xGZmDwAAQBAJ",
    "openlibrary_key": "/works/OL20028467W"
  },
  "sources": ["awards", "google_books", "openlibrary", "nyt_bestsellers"]
}
```

### Example 2: Award Finalist (Partial Data)

```json
{
  "book_id": 42,
  "title": "Trust",
  "author": "Hernan Diaz",
  "year": 2022,
  "isbn_13": "9780593421055",
  "isbn_10": null,
  "isbn_all": ["9780593421055"],
  "publisher": "Riverhead Books",
  "page_count": 416,
  "language": "en",
  "categories": ["Fiction", "Literary"],
  "awards": [
    {
      "award_name": "National Book Award for Fiction",
      "year": 2022,
      "status": "Finalist",
      "publisher": null
    }
  ],
  "award_count": 1,
  "won_award": false,
  "shortlisted": true,
  "ratings_average": null,
  "ratings_count": null,
  "want_to_read_count": null,
  "currently_reading_count": null,
  "already_read_count": null,
  "bestseller_appearances": 0,
  "total_weeks_on_bestseller": 0,
  "highest_rank": null,
  "bestseller_dates": [],
  "identifiers": {
    "google_books_id": "aB3cDeFgHiJ",
    "openlibrary_key": null
  },
  "sources": ["awards", "google_books"]
}
```

### Example 3: Non-Award Book (API Data Only)

```json
{
  "book_id": 789,
  "title": "The Midnight Library",
  "author": "Matt Haig",
  "year": 2020,
  "isbn_13": "9780525559474",
  "isbn_10": "0525559477",
  "isbn_all": ["9780525559474", "0525559477"],
  "publisher": "Viking",
  "page_count": 304,
  "language": "en",
  "categories": ["Fiction", "Fantasy"],
  "awards": [],
  "award_count": 0,
  "won_award": false,
  "shortlisted": false,
  "ratings_average": 4.05,
  "ratings_count": 123456,
  "want_to_read_count": 34567,
  "currently_reading_count": 5678,
  "already_read_count": 98765,
  "bestseller_appearances": 52,
  "total_weeks_on_bestseller": 104,
  "highest_rank": 1,
  "bestseller_dates": ["2020-09-13", "2020-09-20", "..."],
  "identifiers": {
    "google_books_id": "klM1NoPqRsT",
    "openlibrary_key": "/works/OL23456789W"
  },
  "sources": ["google_books", "openlibrary", "nyt_bestsellers"]
}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-10 | Somnath Saha | Initial release with complete field definitions and schema.org metadata |

---

**For questions or corrections, contact:** somnath4@illinois.edu  
**Project Repository:** https://github.com/[username]/cs598-fdc-literary-awards  
**License:** CC BY 4.0 (Data), MIT (Code)

