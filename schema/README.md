# Schema Documentation

This directory contains JSON Schema definitions and JSON-LD metadata for the Literary Awards and Book Reception Dataset.

## Files

### Dataset-Level Metadata

| File | Description |
|------|-------------|
| `dataset-metadata.jsonld` | JSON-LD metadata using schema.org vocabulary for dataset discovery and citation |

### JSON Schemas

| File | Validates | Description |
|------|-----------|-------------|
| `award-entry.schema.json` | `data/*.json` (awards) | Schema for individual award entries (Pulitzer, NBA, Booker) |
| `google-books.schema.json` | `data/google_books.json` | Schema for Google Books API data |
| `openlibrary.schema.json` | `data/openlibrary_books.json` | Schema for Open Library API data with reader metrics |
| `nyt-bestsellers.schema.json` | `data/nyt_bestsellers.json` | Schema for NYT bestseller data |
| `merged-book.schema.json` | `merged_data/merged_literary_books.json` | Schema for the integrated dataset |

## JSON Schema Version

All schemas use JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12/schema

## Validation

To validate a JSON file against its schema using Python:

```python
import json
import jsonschema

# Load schema
with open('schema/merged-book.schema.json') as f:
    schema = json.load(f)

# Load data
with open('merged_data/merged_literary_books.json') as f:
    data = json.load(f)

# Validate
jsonschema.validate(instance=data, schema=schema)
print("Validation passed!")
```

Or using the command line with `ajv`:

```bash
npx ajv validate -s schema/merged-book.schema.json -d merged_data/merged_literary_books.json
```

## JSON-LD Metadata

The `dataset-metadata.jsonld` file provides machine-readable metadata following schema.org conventions. This enables:

- **Dataset discovery** via search engines and data catalogs
- **Proper citation** with creator, date, and license information
- **Provenance tracking** with source dataset references
- **FAIR compliance** (Findable, Accessible, Interoperable, Reusable)

### Key Properties

- `@type`: Dataset
- `creator`: Somnath Saha (somnath4@illinois.edu)
- `license`: CC-BY-4.0
- `temporalCoverage`: 2000/2025
- `isBasedOn`: References to all source data (Wikipedia, Google Books, Open Library, NYT)

## Schema Design Principles

1. **Nullable fields**: Optional fields use `["type", "null"]` syntax
2. **Provenance**: All records include `sources` array for data lineage
3. **Identifiers**: Multiple identifier systems supported (ISBN, Google Books ID, Open Library key)
4. **Extensibility**: `additionalProperties` allowed where appropriate for future fields

