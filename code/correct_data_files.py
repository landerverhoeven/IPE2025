import pandas as pd

def correct_belpex_profile(belpex_data):

    # Ensure the 'Date' column is in string format
    belpex_data['Date'] = belpex_data['Date'].astype(str)

    # Convert the 'Date' column to datetime format
    belpex_data['datetime'] = pd.to_datetime(belpex_data['Date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # Drop rows with invalid datetime values (NaT)
    belpex_data = belpex_data.dropna(subset=['datetime']).copy()

    # Add 29 February to belpex_data
    # Filter data for 5 days before and 5 days after 28 February
    february_range = belpex_data[
        (belpex_data['datetime'] >= "2019-02-23") & (belpex_data['datetime'] <= "2019-03-04")
    ].copy()

    # Find the day with the lowest consumption
    february_range['day'] = february_range['datetime'].dt.date
    daily_consumption = february_range.groupby('day')['Euro'].sum()
    lowest_consumption_day = daily_consumption.idxmin()

    # Copy the 15-minute interval values of the lowest consumption day to 29 February
    lowest_day_data = belpex_data[
        belpex_data['datetime'].dt.date == lowest_consumption_day
    ].copy()

    # Adjust only timestamps from 28 February to 29 February
    lowest_day_data['datetime'] = lowest_day_data['datetime'].apply(
        lambda x: x.replace(day=29, month=2) if x.month == 2 and x.day == 28 else x
    )

    # Insert 29 February data into belpex_data
    belpex_data = pd.concat([belpex_data, lowest_day_data]).sort_values(by='datetime').reset_index(drop=True)

    # Debugging: Print confirmation of 29 February addition
    print("29 February added to belpex_data:")
    print(belpex_data[belpex_data['datetime'].dt.date == pd.Timestamp("2019-02-29").date()])
    return belpex_data

if __name__ == "__main__":
    # Read data into memory
    belpex_data = pd.read_excel('data/Belpex_data.xlsx')  # File with date-time and index values
    belpex_data = correct_belpex_profile(belpex_data)
    print(belpex_data)
