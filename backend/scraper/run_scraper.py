# backend/scraper/run_scraper.py

import os
import django
import sys

# Set up Django env
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'track_chief.settings')
django.setup()

from scraper import NJTransitScraper

if __name__ == "__main__":
    URL = "https://www.njtransit.com/dv-to/New%20York%20Penn%20Station"
    scraper = None
    
    try:
        scraper = NJTransitScraper(url=URL)
        print("Starting scraper...")
        scraper.scrape(interval_minutes=9)
    except KeyboardInterrupt:
        print("\nScraping stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        if scraper:
            scraper.close()