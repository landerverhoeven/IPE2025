import pandas as pd

def correct_belpex(belpex_data):
    # Ensure the 'Date' column is in string format
    belpex_data['Date'] = belpex_data['Date'].astype(str)

    # Append '00:00' to rows where only the date is present (no time)
    belpex_data['Date'] = belpex_data['Date'].apply(lambda x: x if ':' in x else f"{x} 00:00")

    # Convert the 'Date' column to datetime format
    belpex_data['datetime'] = pd.to_datetime(belpex_data['Date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # Drop rows with invalid datetime values (NaT)
    belpex_data = belpex_data.dropna(subset=['datetime']).copy()

    # Convert the 'Euro' column to numeric and drop invalid rows
    belpex_data['Euro'] = pd.to_numeric(belpex_data['Euro'], errors='coerce')
    belpex_data = belpex_data.dropna(subset=['Euro']).copy()

    # Drop duplicate datetime values by aggregating numeric columns
    numeric_columns = belpex_data.select_dtypes(include='number').columns
    belpex_data = belpex_data.groupby('datetime', as_index=False)[numeric_columns].mean()

    # Resample to 15-minute intervals
    belpex_data = belpex_data.set_index('datetime').resample('15min').ffill().reset_index()

    # Change the year of belpex_data to 2000
    belpex_data['datetime'] = belpex_data['datetime'].apply(lambda x: x.replace(year=2000))

    # Debugging: Print belpex_data after resampling and year adjustment
    print("belpex_data after resampling and year adjustment:")
    print(belpex_data.head())
    print(belpex_data.tail())

    return belpex_data


def correct_load_profile(load_profile):
    # Ensure the 'Datum_Startuur' column is in datetime format
    load_profile['Datum_Startuur'] = pd.to_datetime(load_profile['Datum_Startuur'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # Drop rows with invalid datetime values (NaT)
    load_profile = load_profile.dropna(subset=['Datum_Startuur']).copy()

    # Convert the 'Volume_Afname_kWh' column to numeric and drop invalid rows
    load_profile['Volume_Afname_kWh'] = pd.to_numeric(load_profile['Volume_Afname_kWh'], errors='coerce')
    load_profile = load_profile.dropna(subset=['Volume_Afname_kWh']).copy()

    # Resample to 15-minute intervals
    load_profile = load_profile.set_index('Datum_Startuur').resample('15min').ffill().reset_index()

    # Debugging: Print load_profile after resampling
    print("load_profile after resampling:")
    print(load_profile.head())
    print(load_profile.tail())

    return load_profile

if __name__ == "__main__":
    # Read data into memory
    belpex_data = pd.read_excel('data/Belpex_data.xlsx')  # File with date-time and index values
    belpex_data = correct_belpex_profile(belpex_data)
    print(belpex_data)