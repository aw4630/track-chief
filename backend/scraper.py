
import requests
from bs4 import BeautifulSoup

#URL of the NJ Transit NY Penn Station departures page
URL = "https://www.njtransit.com/dv-to/NY%20Penn%20Station"

def fetch_departures():
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(URL)
        response.raise_for_status()  

        soup = BeautifulSoup(response.text, 'html.parser')

        #Get all departure cards
        departure_cards = soup.find_all('div', class_='media no-gutters p-3')

        departures = []

        for card in departure_cards:
            # Extract train destination (ex: "Trenton - SEC")
            destination = card.find('p', class_='mb-0').strong.text.strip()

            # Extract train line and number (ex: "NEC Train 3951")
            train_info = card.find('p', class_='mb-0').find_next_sibling('p').text.strip()
            train_line, train_number = train_info.split('Train')

            # Extract departure time (e.g., "5:12 PM")
            departure_time = card.find('strong', class_='d-block ff-secondary--bold flex-grow-1 h2 mb-0').text.strip()

            # Extract track number (if available)
            track_info = card.find('p', class_='align-self-end mt-1 mb-0')
            track_number = track_info.text.strip() if track_info else "Track not listed"

            #ADD TO PRELIM DEPARTURES LIST
            departures.append({
                "Destination": destination,
                "Train Line": train_line.strip(),
                "Train Number": train_number.strip(),
                "Departure Time": departure_time,
                "Track Number": track_number
            })

        return departures

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

# DISPLAY PRELIM TEST LIST
if __name__ == "__main__":
    departures = fetch_departures()
    if departures:
        print("Scheduled Departures:")
        for idx, dep in enumerate(departures, start=1):
            print(f"{idx}. Destination: {dep['Destination']}")
            print(f"   Train Line: {dep['Train Line']}")
            print(f"   Train Number: {dep['Train Number']}")
            print(f"   Departure Time: {dep['Departure Time']}")
            print(f"   Track Number: {dep['Track Number']}\n")
    else:
        print("No departures found or an error occurred.")
