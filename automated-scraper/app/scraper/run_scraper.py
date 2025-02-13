# backend/scraper/run_scraper.py

import os
import django
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the app directory to Python path
current_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(current_dir))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'track_chief.settings')
django.setup()

# Import the scraper class
from scraper.scraper import NJTransitScraper

def main():
    url = os.getenv('NJ_TRANSIT_URL', 'https://www.njtransit.com/dv-to/New%20York%20Penn%20Station')
    interval = int(os.getenv('SCRAPER_INTERVAL_MINUTES', '9'))
    
    scraper = None
    try:
        logger.info("Initializing NJ Transit scraper...")
        scraper = NJTransitScraper(url=url)
        
        logger.info(f"Starting scraper with {interval} minute interval...")
        scraper.scrape(interval_minutes=interval)
    except KeyboardInterrupt:
        logger.info("\nScraping stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()