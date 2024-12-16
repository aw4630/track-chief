from selenium import webdriver
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

''' 

    THIS IS DEPARTURE VISION SCRAPER SCRIPT for NY PENN STATION VERSION 2
    - Collects the track number of departing trains in real-time
    - Goes thru class headers/names containing scheduled train data from the Javascript-rendered NJ Transit website
    - Runs every 10 minutes 
    - Unique data entries are uploaded in a .csv format to test script functionality/accuracy

    VERSION 3: Containerize scraping script w/ Docker and deploy to Kubernetes cluster for automated scraping

'''

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

    def scrape(self, output_file, interval_minutes=5):
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
