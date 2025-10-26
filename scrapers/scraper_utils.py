#!/usr/bin/env python3
"""
Common utility functions for all award scrapers.
"""

import requests
from bs4 import BeautifulSoup
import time
import re
import logging
from typing import Optional
from datetime import datetime
import os
import shutil

logger = logging.getLogger(__name__)


def fetch_page(url: str, retries: int = 3) -> Optional[BeautifulSoup]:
    """Fetch a webpage with retry logic"""
    for attempt in range(retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Educational Research Project)'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Failed to fetch {url} after {retries} attempts")
                return None


def clean_text(text: str) -> str:
    if not text:
        return ""
    # Remove citation brackets [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    text = ' '.join(text.split())
    return text.strip()


def extract_year_from_text(text: str) -> Optional[int]:
    match = re.search(r'\b(19|20)\d{2}\b', text)
    if match:
        return int(match.group(0))
    return None


def backup_file_if_exists(filepath: str) -> None:
    """Create a backup of the file if it exists"""
    if not os.path.exists(filepath):
        # logger.info(f"No existing file to backup: {filepath}")
        return
    
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        return
    
    # Get the directory and filename
    file_dir = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    base_name, ext = os.path.splitext(filename)
    
    # Create backup directory relative to the data directory
    # If filepath is in data/, backup to data_backup/
    parent_dir = os.path.dirname(file_dir)
    backup_dir = os.path.join(parent_dir, 'data_backup')
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create backup with full timestamp (YYYYMMDDHHmmSS)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_filename = f"{base_name}_{timestamp}{ext}"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        shutil.copy2(filepath, backup_path)
        logger.info(f"Backed up existing file: {backup_path}")
    except Exception as e:
        logger.error(f"Failed to backup file {filepath}: {e}")


def save_to_json(data: list, filepath: str, backup: bool = True) -> bool:
    """Save data to JSON file with optional backup"""
    import json
    
    try:
        if backup:
            backup_file_if_exists(filepath)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # TODO: add compression for large files?
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(data)} entries to {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save data to {filepath}: {e}")
        return False


def validate_data(data: list, year_range: tuple = (2000, 2025)) -> list:
    """Validate and clean the collected data"""
    validated = []
    
    for entry in data:
        # Check required fields
        if not all(key in entry for key in ["Year", "Award", "Status", "Title", "Author"]):
            logger.warning(f"Skipping entry with missing fields: {entry}")
            continue
        
        # Validate year range
        year = entry.get("Year")
        if year is None or not isinstance(year, int) or not (year_range[0] <= year <= year_range[1]):
            logger.warning(f"Skipping entry with invalid year: {entry.get('Year')} in {entry.get('Title', 'Unknown')}")
            continue
        
        # print(f"DEBUG: validating {entry.get('Title')}")  # TODO: remove
        if not entry.get('Title') or not entry.get('Author'):
            logger.warning(f"Skipping entry with empty title/author: {entry}")
            continue
        
        validated.append(entry)
    
    return validated

