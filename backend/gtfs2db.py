import pandas as pd

''' Clean/preprocess route data for relational PostgreSQL DB
    Specifically dropping unneeded data columns and editing train departure times to range from 0-24 hours
    The csv will be saved to the rail_data folder, which will be then uploaded to PGAdmin4 for testing queries
    Afterwards I will create a SQL dump file and upload it to my Google Cloud SQL bucket and the respective cloud instance
'''

csv_path = '/Users/alanwu/Downloads/rail_data/routes.csv'
df = pd.read_csv(csv_path)

# DROP the 'route_url' column, its not needed
df = df.drop(columns=['route_url'])

cleaned_csv_path = '/Users/alanwu/Downloads/rail_data/cleaned_routes.csv'
df.to_csv(cleaned_csv_path, index=False)

print("Cleaned CSV saved as:", cleaned_csv_path)

from datetime import timedelta

# Clean/preprocess stop_times data
input_csv_path = '/Users/alanwu/Downloads/rail_data/stop_times.csv'
output_csv_path = '/Users/alanwu/Downloads/rail_data/cleaned_stop_times.csv'

def fix_invalid_time(time_str):
    """
    There are times that need to be fixed in the train schedule, ex: 25:03:00 should be 01:03:00
    aka fix times that exceed 24:00:00.
    If the time exceeds 24:00:00, subtract 24 hours and return the corrected time.
    """
    try:
        # Split the time into hours, minutes, seconds
        parts = list(map(int, time_str.split(":")))
        hours, minutes, seconds = parts[0], parts[1], parts[2]
        
        if hours >= 24:
            hours -= 24
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    except Exception as e:
        print(f"Error processing time: {time_str} - {e}")
        return time_str  

df = pd.read_csv(input_csv_path)

if 'arrival_time' in df.columns:
    df['arrival_time'] = df['arrival_time'].apply(fix_invalid_time)

if 'departure_time' in df.columns:
    df['departure_time'] = df['departure_time'].apply(fix_invalid_time)

df.to_csv(output_csv_path, index=False)

print(f"Cleaned CSV saved as {output_csv_path}")


