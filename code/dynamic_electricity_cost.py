import pandas as pd

# SOURCE: ENGIE Electrabel - Dynamic electricity prices

def calculate_total_dynamic_cost(belpex_data, load_profile):
    """
    Calculate the total yearly electricity cost, including dynamic and fixed costs.
    Returns the total cost.
    """
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

    # Standardize datetime formats for load_profile
    load_profile = load_profile.copy()  # Avoid SettingWithCopyWarning
    load_profile['Datum_Startuur'] = pd.to_datetime(load_profile['Datum_Startuur'], format='%Y-%m-%dT%H:%M:%S.%fZ', errors='coerce')

    # Drop rows with invalid datetime values (NaT) in load_profile
    load_profile = load_profile.dropna(subset=['Datum_Startuur']).copy()

    # Change the year of load_profile to 2000
    load_profile['Datum_Startuur'] = load_profile['Datum_Startuur'].apply(lambda x: x.replace(year=2000))

    # Ensure both datasets cover the same datetime range
    start_date = max(belpex_data['datetime'].min(), load_profile['Datum_Startuur'].min())
    end_date = min(belpex_data['datetime'].max(), load_profile['Datum_Startuur'].max())

    belpex_data = belpex_data[(belpex_data['datetime'] >= start_date) & (belpex_data['datetime'] <= end_date)].copy()
    load_profile = load_profile[(load_profile['Datum_Startuur'] >= start_date) & (load_profile['Datum_Startuur'] <= end_date)].copy()

    # Validate that both datasets are aligned
    if not belpex_data['datetime'].equals(load_profile['Datum_Startuur']):
        raise ValueError("The datetime columns in belpex_data and load_profile are not aligned.")

    # Calculate electricity cost for each 15-minute interval
    vat_tarrif = 1.06  # VAT tariff
    load_profile['electricity_cost'] = (
        ((0.1 * belpex_data['Euro'].values + 1.316) * vat_tarrif / 100) * load_profile['Volume_Afname_kWh'] +  # Cost energy produced
        (5.60719 / 100) * load_profile['Volume_Afname_kWh'] +  # Network costs
        ((0.20417 / 100) + (5.03288 / 100)) * load_profile['Volume_Afname_kWh']  # Taxes
    )

    # Total dynamic costs
    dynamic_costs = load_profile['electricity_cost'].sum()
    print(f"Dynamic Cost (Yearly): €{dynamic_costs:.2f}")
    
    # Fixed yearly costs
    fixed_fee = 100.70  # Fixed fee per year
    capacity_tarrif = 51.9852  # Annual capacity tariff per kW
    data_management_fee = 18.56  # Annual fee

    # Calculate kW_peak (maximum load in kW) for each month using 15-minute intervals
    load_profile['Month'] = load_profile['Datum_Startuur'].dt.month
    load_profile['load_consumption_kw'] = load_profile['Volume_Afname_kWh'] / 0.25  # Convert kWh to kW (15 minutes = 0.25 hours)
    kW_peak_matrix = load_profile.groupby('Month')['load_consumption_kw'].max().reset_index()
    kW_peak_matrix.rename(columns={'load_consumption_kw': 'kW_peak'}, inplace=True)

    # Calculate the average kW_peak across all months
    average_kW_peak = kW_peak_matrix['kW_peak'].mean()

    # Ensure the average_kW_peak is at least 2.5 kW
    if average_kW_peak < 2.5:
        average_kW_peak = 2.5

    # Calculate the total capacity tariff for the year
    total_capacity_tarrif = average_kW_peak * capacity_tarrif

    # Total yearly cost
    total_cost = dynamic_costs + fixed_fee + data_management_fee + total_capacity_tarrif

    return total_cost

# Main script
if __name__ == "__main__":
    # Read data into memory
    belpex_data = pd.read_excel('data/Belpex_data.xlsx')  # File with date-time and index values
    load_profile = pd.read_excel('data/Load_profile_8.xlsx')  # File with date-time and consumption values

    # Calculate total cost using in-memory data
    total_cost = calculate_total_dynamic_cost(belpex_data, load_profile)

    # Print the total cost
    print(f"Total Electricity Cost (Yearly): €{total_cost:.2f}")
    print(f"belpex_data rows after filtering: {len(belpex_data)}")
    print(f"load_profile rows after filtering: {len(load_profile)}")
    print("belpex_data datetime range:", belpex_data['datetime'].min(), "to", belpex_data['datetime'].max())
    print("load_profile date_time range:", load_profile['Datum_Startuur'].min(), "to", load_profile['Datum_Startuur'].max())