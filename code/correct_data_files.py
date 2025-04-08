import pandas as pd

def correct_belpex_data(belpex_data):
    belpex_data = belpex_data.copy()  # Avoid SettingWithCopyWarning

    # Ensure the 'Date' column is in string format
    belpex_data['Date'] = belpex_data['Date'].astype(str)

    # Append '00:00' to rows where only the date is present (no time)
    belpex_data['Date'] = belpex_data['Date'].apply(lambda x: x if ':' in x else f"{x} 00:00")

    # Convert the 'Date' column to datetime format
    belpex_data['datetime'] = pd.to_datetime(belpex_data['Date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # Drop rows with invalid datetime values (NaT)
    belpex_data = belpex_data.dropna(subset=['datetime']).copy()

    # Drop rows where the date is February 29
    belpex_data = belpex_data[~((belpex_data['datetime'].dt.month == 2) & (belpex_data['datetime'].dt.day == 29))]

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

    # Add missing rows till 23:45:00
    last_row = belpex_data.iloc[-1]
    last_datetime = last_row['datetime']
    additional_rows = []
    for i in range(1, 4):
        new_datetime = last_datetime + pd.Timedelta(minutes=15 * i)
        new_row = last_row.copy()
        new_row['datetime'] = new_datetime
        additional_rows.append(new_row)
    belpex_data = belpex_data.append(additional_rows, ignore_index=True)

    return belpex_data


def correct_load_profile(load_profile):
    load_profile = load_profile.copy()  # Avoid SettingWithCopyWarning

    # Ensure the 'Datum_Startuur' column is in datetime format
    load_profile['Datum_Startuur'] = pd.to_datetime(load_profile['Datum_Startuur'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # Drop rows with invalid datetime values (NaT)
    load_profile = load_profile.dropna(subset=['Datum_Startuur']).copy()

    # Drop rows where the date is February 29
    load_profile = load_profile[~((load_profile['Datum_Startuur'].dt.month == 2) & (load_profile['Datum_Startuur'].dt.day == 29))]

    # Convert the 'Volume_Afname_kWh' column to numeric and drop invalid rows
    load_profile['Volume_Afname_kWh'] = pd.to_numeric(load_profile['Volume_Afname_kWh'], errors='coerce')
    load_profile = load_profile.dropna(subset=['Volume_Afname_kWh']).copy()

    # Resample to 15-minute intervals
    load_profile = load_profile.set_index('Datum_Startuur').resample('15min').ffill().reset_index()

    # Change the year of load_profile to 2000
    load_profile['Datum_Startuur'] = load_profile['Datum_Startuur'].apply(lambda x: x.replace(year=2000))

    return load_profile


def correct_irradiance_data(irradiance_data):
    irradiance_data = irradiance_data.copy()  # Avoid SettingWithCopyWarning

    # Ensure the 'DateTime' column is in datetime format
    irradiance_data['DateTime'] = pd.to_datetime(irradiance_data['DateTime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # Drop rows with invalid datetime values (NaT)
    irradiance_data = irradiance_data.dropna(subset=['DateTime']).copy()

    # Drop rows where the date is February 29
    irradiance_data = irradiance_data[~((irradiance_data['DateTime'].dt.month == 2) & (irradiance_data['DateTime'].dt.day == 29))]

    # Resample to 15-minute intervals
    irradiance_data = irradiance_data.set_index('DateTime').resample('15min').ffill().reset_index()

    # Change the year of load_profile to 2000
    irradiance_data['DateTime'] = irradiance_data['DateTime'].apply(lambda x: x.replace(year=2000))

    return irradiance_data


if __name__ == "__main__":
    # Read data into memory
    belpex_data = pd.read_excel('data/Belpex_data.xlsx')  # File with date-time and index values
    print(f"Length of belpex_data before correction: {len(belpex_data)}")
    belpex_data = correct_belpex_data(belpex_data)
    print(f"Length of belpex_data after correction: {len(belpex_data)}")
    # Debugging: Print load_profile after resampling
    print("belpex_data after resampling:")
    print(belpex_data.head())
    print(belpex_data.tail())

    load_profile = pd.read_excel('data/Load_profile_8.xlsx')  # File with date-time and index values
    print(f"Length of load_profile before correction: {len(load_profile)}")
    load_profile = correct_load_profile(load_profile)
    print(f"Length of load_profile after correction: {len(load_profile)}")
    print("load_profile after resampling:")
    print(load_profile.head())
    print(load_profile.tail())

    irradiance_data = pd.read_excel('data/Irradiance_data.xlsx')  # File with date-time and index values
    print(f"Length of irradiance_data before correction: {len(irradiance_data)}")
    irradiance_data = correct_irradiance_data(irradiance_data)
    print(f"Length of irradiance_data after correction: {len(irradiance_data)}")
    print("irradiance_data after resampling:")
    print(irradiance_data.head())
    print(irradiance_data.tail())