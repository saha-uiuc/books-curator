#!/usr/bin/env python3
"""
Main orchestrator script to run all award scrapers and collect data.
Runs each scraper independently and collects the results.
"""

import logging
import sys
from pathlib import Path

# Import scrapers from the scrapers package
from scrapers import scrape_pulitzer_prize, scrape_national_book_award, scrape_booker_prize

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run all award scrapers."""
    logger.info("="*60)
    logger.info("Starting literary awards data collection...")
    logger.info("="*60)
    
    # Define output directory
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    results = {}
    
    # Run Pulitzer Prize scraper
    try:
        logger.info("\n" + "="*60)
        logger.info("Scraping Pulitzer Prize for Fiction")
        logger.info("="*60)
        pulitzer_file = data_dir / "pulitzer_prize.json"
        pulitzer_data = scrape_pulitzer_prize(str(pulitzer_file))
        
        if pulitzer_data:
            winners = sum(1 for x in pulitzer_data if x['Status'] == 'Winner')
            finalists = len(pulitzer_data) - winners
            logger.info(f"Pulitzer Prize: {len(pulitzer_data)} total ({winners} winners, {finalists} finalists)")
            results['Pulitzer'] = {'total': len(pulitzer_data), 'winners': winners, 'finalists': finalists}
        else:
            logger.warning("✗ No Pulitzer Prize data collected")
            results['Pulitzer'] = {'total': 0, 'winners': 0, 'finalists': 0}
    except Exception as e:
        logger.error(f"✗ Error scraping Pulitzer Prize: {e}", exc_info=True)
        results['Pulitzer'] = {'total': 0, 'winners': 0, 'finalists': 0, 'error': str(e)}
    
    # Run National Book Award scraper
    try:
        logger.info("\n" + "="*60)
        logger.info("Scraping National Book Award for Fiction")
        logger.info("="*60)
        nba_file = data_dir / "national_book_award.json"
        nba_data = scrape_national_book_award(str(nba_file))
        
        if nba_data:
            winners = sum(1 for x in nba_data if x['Status'] == 'Winner')
            finalists = len(nba_data) - winners
            logger.info(f"National Book Award: {len(nba_data)} total ({winners} winners, {finalists} finalists)")
            results['NBA'] = {'total': len(nba_data), 'winners': winners, 'finalists': finalists}
        else:
            logger.warning("✗ No National Book Award data collected")
            results['NBA'] = {'total': 0, 'winners': 0, 'finalists': 0}
    except Exception as e:
        logger.error(f"✗ Error scraping National Book Award: {e}", exc_info=True)
        results['NBA'] = {'total': 0, 'winners': 0, 'finalists': 0, 'error': str(e)}
    
    # Run Booker Prize scraper
    try:
        logger.info("\n" + "="*60)
        logger.info("Scraping Booker Prize")
        logger.info("="*60)
        booker_file = data_dir / "booker_prize.json"
        booker_data = scrape_booker_prize(str(booker_file))
        
        if booker_data:
            winners = sum(1 for x in booker_data if x['Status'] == 'Winner')
            shortlist = sum(1 for x in booker_data if x['Status'] == 'Shortlist')
            longlist = sum(1 for x in booker_data if x['Status'] == 'Longlist')
            logger.info(f"Booker Prize: {len(booker_data)} total ({winners} winners, {shortlist} shortlist, {longlist} longlist)")
            results['Booker'] = {'total': len(booker_data), 'winners': winners, 'shortlist': shortlist, 'longlist': longlist}
        else:
            logger.warning("✗ No Booker Prize data collected")
            results['Booker'] = {'total': 0, 'winners': 0, 'shortlist': 0, 'longlist': 0}
    except Exception as e:
        logger.error(f"✗ Error scraping Booker Prize: {e}", exc_info=True)
        results['Booker'] = {'total': 0, 'winners': 0, 'shortlist': 0, 'longlist': 0, 'error': str(e)}
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("DATA COLLECTION COMPLETE")
    logger.info("="*60)
    
    total_entries = sum(r.get('total', 0) for r in results.values())
    logger.info(f"Total entries collected: {total_entries}")
    
    logger.info("\nBreakdown by award:")
    for award, stats in results.items():
        if 'error' in stats:
            logger.error(f"  {award}: ERROR - {stats['error']}")
        else:
            logger.info(f"  {award}: {stats}")
    
    logger.info("\n" + "="*60)
    logger.info(f"JSON files saved in: {data_dir}")
    logger.info("="*60)
    
    # Return success if any data was collected
    return total_entries > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

