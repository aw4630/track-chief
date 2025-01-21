'''from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import pandas as pd
from datetime import datetime
import time

class NJTransitScraper:
    def __init__(self, url, driver_path):
        self.url = url
        self.driver_path = driver_path
        self.data = []

        # config the Selenium WebDriver
        options = Options()
        options.add_argument("--headless")  #headless mode, don't show browser popup
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(service=Service(driver_path), options=options)

    def fetch_page(self):
        try:
            self.driver.get(self.url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "media-body"))
            )
        except TimeoutException:
            print("Timeout while loading the page. Retrying...")
            return None

    def parse_data(self):
        try:
            entries = self.driver.find_elements(By.CLASS_NAME, "media-body")
            print(f"Number of entries found: {len(entries)}")   

            for entry in entries:
                try:
                    #DEBUG 
                    print("Entry Text: ", entry.text)

                    # EXTRACT route short name (ex: 'NEC', 'NJCL')
                    try:
                        route_short_name_element = entry.find_element(By.XPATH, ".//p/span")
                        route_short_name = route_short_name_element.text.strip()
                    except NoSuchElementException:
                        print("Route short name not found, skipping entry.")
                        continue

                    # EXTRACT train number (ex: 'Train 7684')
                    try:
                        train_text_element = entry.find_element(By.XPATH, ".//p[contains(text(), 'Train')]")
                        train_text = train_text_element.text.strip()
                        train_number = train_text.split("Train")[1].strip()
                    except NoSuchElementException:
                        print("Train number not found, skipping entry.")
                        continue

                    # EXTRACT departure time (ex: '8:54 PM') and convert to ISO ("%Y-%m-%dT%H:%M:%SZ") format 
                    try:
                        departure_time_element = entry.find_element(By.XPATH, ".//strong[contains(text(), ':')]")
                        departure_time_raw = departure_time_element.text.strip()
                        now = datetime.now()
                        departure_time = datetime.strptime(
                            f"{now.strftime('%Y-%m-%d')} {departure_time_raw}", "%Y-%m-%d %I:%M %p"
                        ).strftime("%Y-%m-%dT%H:%M:%SZ")
                    except NoSuchElementException:
                        print("Departure time not found, skipping entry.")
                        continue

                    # EXTRACT track number (ex: 'Track 2')
                    try:
                        track_element = entry.find_element(By.XPATH, ".//p[contains(text(), 'Track')]")
                        track = track_element.text.strip()
                        if not track.startswith("Track"):  
                            print("Invalid track number, skipping entry.")
                            continue
                    except NoSuchElementException:
                        print("Track number not found, skipping entry.")
                        continue


                    # Check for duplicates, only append new entry if unique
                    new_entry = {
                        "train_number": train_number,
                        "route_short_name": route_short_name,
                        "departure_time": departure_time,
                        "track": track,
                    }
                    if new_entry not in self.data:
                        self.data.append(new_entry)
                    else:
                        print("Duplicate entry found, skipping.")

                except Exception as e:
                    print(f"Error processing entry: {e}, skipping.")
                    continue
        except Exception as e:
            print(f"Error parsing data: {e}")


    def save_to_csv(self, output_file):
        if self.data:
            df = pd.DataFrame(self.data)
            df.to_csv(output_file, index=False)
            print(f"Data saved to {output_file}")
        else:
            print("No data collected.")

    def scrape(self, output_file, interval_minutes=10):
        while True:
            print(f"Starting scrape at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.fetch_page()
            print("Parsing data...")
            self.parse_data()
            print("Data parsed, save to test file: track_usage.csv")
            self.save_to_csv(output_file)
            print(f"Sleeping for {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60) #10 * 60 seconds -> 10 minutes sleep time

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    URL = "https://www.njtransit.com/dv-to/New%20York%20Penn%20Station" # NJTransit's departure vision site for NY Penn Station
    DRIVER_PATH = "/opt/homebrew/bin/chromedriver"  # Update with the path to my chromedriver exe

    scraper = NJTransitScraper(URL, DRIVER_PATH)
    try:
        scraper.scrape(output_file="track_usage.csv", interval_minutes=10) #Scrape every 10 minutes for new track number data
    except KeyboardInterrupt:
        print("Scraping stopped by user.")
    finally:
        scraper.close()
'''

# backend/scraper/scraper.py

'''

    THIS IS DEPARTURE VISION SCRAPER SCRIPT for NY PENN STATION VERSION 3
    - Collects the track number of departing trains in real-time using refined script
    - Goes thru class headers/names containing scheduled train data from the Javascript-rendered NJ Transit website
    - Runs every 10 minutes 
    - Additional error handling statements added
    - Unique data entries are uploaded in relational SQL format to 'track_usage' table in my Google Cloud SQL 'gtfs' database

    VERSION 4: Containerize scraping script w/ Docker and deploy to Kubernetes cluster for automated scraping

'''

# backend/scraper/scraper.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from datetime import datetime
import time
import os
import psutil
import logging
from django.db import connection
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NJTransitScraper:
    def __init__(self, url):
        self.url = url
        self.data = []
        self.driver = None
        self.initialize_driver()

    def cleanup_chrome_processes(self):
        """Kill any existing Chrome processes"""
        try:
            for proc in psutil.process_iter(['name']):
                if 'chrome' in proc.info['name'].lower():
                    try:
                        proc.kill()
                    except:
                        pass
            time.sleep(2)  # Give processes time to clean up
        except Exception as e:
            logger.error(f"Error cleaning up Chrome processes: {e}")

    def initialize_driver(self, retry_count=3):
        """Initialize Chrome driver with retries"""
        for attempt in range(retry_count):
            try:
                # Clean up any existing Chrome processes
                self.cleanup_chrome_processes()
                
                options = Options()
                options.add_argument('--headless=new')  # Updated headless mode
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-software-rasterizer')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-browser-side-navigation')
                options.add_argument('--remote-debugging-port=0')  # Random debug port
                options.add_experimental_option('excludeSwitches', ['enable-logging'])
                
                # Set Chrome binary location for M1 Mac
                options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                
                # Use ChromeDriverManager for automatic driver management
                driver_path = ChromeDriverManager().install()
                service = Service(driver_path)
                
                self.driver = webdriver.Chrome(service=service, options=options)
                logger.info("Chrome driver initialized successfully")
                return
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed to initialize driver: {e}")
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                if attempt < retry_count - 1:
                    time.sleep(5 * (attempt + 1))  # Exponential backoff
                else:
                    raise Exception("Failed to initialize Chrome driver after multiple attempts")

    def parse_data(self):
        if not self.driver:
            logger.error("Driver not initialized")
            return

        try:
            entries = self.driver.find_elements(By.CLASS_NAME, "media-body")
            logger.info(f"Number of entries found: {len(entries)}")   

            for entry in entries:
                try:
                    # Extract route short name
                    route_short_name_element = entry.find_element(By.XPATH, ".//p/span")
                    route_short_name = route_short_name_element.text.strip()

                    # Extract train number
                    train_text_element = entry.find_element(By.XPATH, ".//p[contains(text(), 'Train')]")
                    train_text = train_text_element.text.strip()
                    train_number = train_text.split("Train")[1].strip()

                    # Extract departure time
                    # Modified departure time handling
                    departure_time_element = entry.find_element(By.XPATH, ".//strong[contains(text(), ':')]")
                    departure_time_raw = departure_time_element.text.strip()
                    now = datetime.now()  # Local time
                
                    # Parse the time and explicitly set today's date
                    departure_time = datetime.strptime(
                        f"{now.date()} {departure_time_raw}",
                        "%Y-%m-%d %I:%M %p"
                    )

                    # Adjust for timezone if necessary
                    if departure_time_raw.endswith('PM') and departure_time.hour < 12:
                        departure_time = departure_time.replace(hour=departure_time.hour + 12)
                    elif departure_time_raw.endswith('AM') and departure_time.hour == 12:
                        departure_time = departure_time.replace(hour=0)

                    # Format for database (keep it in local time)
                    departure_time_str = departure_time.strftime("%Y-%m-%d %H:%M:%S")

                    # Extract track number
                    track_element = entry.find_element(By.XPATH, ".//p[contains(text(), 'Track')]")
                    track = track_element.text.strip()
                    
                    if not track.startswith("Track"):
                        logger.warning(f"Invalid track format: {track}")
                        continue

                    new_entry = {
                        "train_number": train_number,
                        "route_short_name": route_short_name,
                        "departure_time": departure_time_str,
                        "track": track,
                    }

                    if new_entry not in self.data:
                        self.data.append(new_entry)
                        logger.debug(f"Added new entry: {new_entry}")
                    else:
                        logger.debug("Duplicate entry found, skipping.")

                except NoSuchElementException as e:
                    logger.warning(f"Missing element in entry: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing entry: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing data: {e}")
            raise

    def upload_to_db(self):
        """Upload data to track_usage table"""
        if not self.data:
            logger.info("No data to upload")
            return

        cursor = None
        try:
            cursor = connection.cursor()
            
            query = """
            INSERT INTO track_usage 
            (train_number, route_short_name, departure_time, track)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (train_number, departure_time) 
            DO UPDATE SET
                track = EXCLUDED.track,
                route_short_name = EXCLUDED.route_short_name;
            """
            
            values = [(
                entry['train_number'],
                entry['route_short_name'],
                entry['departure_time'],
                entry['track']
            ) for entry in self.data]
            
            cursor.executemany(query, values)
            connection.commit()
            logger.info(f"Successfully uploaded {len(values)} records")
            
        except Exception as e:
            logger.error(f"Error uploading to database: {e}")
            connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.data = []  # Clear data after upload attempt

    def fetch_page(self):
        if not self.driver:
            logger.error("Driver not initialized")
            return

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.driver.get(self.url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "media-body"))
                )
                return True
            except TimeoutException:
                logger.warning(f"Timeout while loading the page. Attempt {attempt + 1} of {max_retries}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(5 * (attempt + 1))
            except WebDriverException as e:
                logger.error(f"WebDriver error: {e}")
                raise

    def scrape(self, interval_minutes=10):
        """Main scraping loop"""
        retry_count = 0
        max_retries = 3
        
        while True:
            try:
                logger.info(f"Starting scrape at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                if not self.driver:
                    self.initialize_driver()
                
                self.fetch_page()
                self.parse_data()
                self.upload_to_db()
                
                retry_count = 0  # Reset retry count on successful scrape
                logger.info(f"Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error during scrape cycle: {e}")
                retry_count += 1
                
                try:
                    if self.driver:
                        self.driver.quit()
                except:
                    pass
                
                self.driver = None
                
                if retry_count >= max_retries:
                    logger.error("Max retries reached, waiting longer before next attempt")
                    time.sleep(300)  # 5 minutes
                    retry_count = 0
                else:
                    time.sleep(60 * retry_count)  # Progressive backoff

    def close(self):
        """Cleanup method"""
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            logger.error(f"Error closing driver: {e}")
        finally:
            self.cleanup_chrome_processes()