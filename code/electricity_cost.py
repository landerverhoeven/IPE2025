import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# SOURCE: ENGIE Electrabel - Dynamic electricity prices

def dynamic_electricity_cost(index, kW_peak, load_consumption):
    vat_tarrif = 1.06  # VAT tariff

    # Cost energy produced
    fixed_fee = 100.70  # Fixed fee per year
    dynamic_price = (0.1 * index + 1.316) * vat_tarrif / 100

    cost_energy_produced = dynamic_price * load_consumption

    # Income energy injected
    income_energy_injected = (0.1 * index - 1.3050) * vat_tarrif / 100

    # Network costs
    capacity_tarrif = 51.9852 * kW_peak  # Annual capacity tariff
    take_off_fee = 5.60719 / 100  # Per kWh
    data_management_fee = 18.56  # Annual fee

    network_costs = capacity_tarrif + take_off_fee * load_consumption + data_management_fee

    # Taxes
    energy_contribution = 0.20417 / 100  # Per kWh
    federal_energy_tax = 5.03288 / 100  # Per kWh

    taxes = (energy_contribution + federal_energy_tax) * load_consumption

    # Total electricity cost formula
    formula_for_electricity = cost_energy_produced + network_costs + taxes - income_energy_injected * 0

    return formula_for_electricity + fixed_fee

# Read and preprocess index data
index_data = pd.read_excel('data/Belpex_data.xlsx')  # File with date-time and index values
index_data.rename(columns={'Date': 'DateTime', 'Euro': 'Index'}, inplace=True)
index_data['Index'] = index_data['Index'].replace({'€': '', ',': '.'}, regex=True).astype(float)  # Clean and convert to float
index_data['DateTime'] = pd.to_datetime(index_data['DateTime'])  # Ensure DateTime is in datetime format

# Resample index data to 15-minute intervals (forward fill to match load profile)
index_data = index_data.set_index('DateTime').resample('15min').ffill().reset_index()

# Read and preprocess load profile data
load_profile = pd.read_excel('data/Load_profile_8.xlsx')  # File with date-time and consumption values
load_profile.rename(columns={'date_time': 'Datum_Startuur', 'load_consumption': 'Volume_Afname_kWh'}, inplace=True)
load_profile['Volume_Afname_kWh'] = load_profile['Volume_Afname_kWh'].astype(str).str.replace(',', '.').astype(float)  # Convert to float
load_profile['Datum_Startuur'] = pd.to_datetime(load_profile['Datum_Startuur'])  # Ensure Datum_Startuur is in datetime format

# Resample load profile to 15-minute intervals
load_profile = load_profile.set_index('Datum_Startuur').resample('15min').sum().reset_index()

# Calculate kW_peak (maximum load in kW) for the year
load_profile['load_consumption_kw'] = load_profile['Volume_Afname_kWh'] / 0.25  # Convert kWh to kW (15 minutes = 0.25 hours)
kW_peak = load_profile['load_consumption_kw'].max()

# Merge index data with load profile into a single matrix
data = pd.merge(index_data, load_profile, left_on='DateTime', right_on='Datum_Startuur', how='inner')

# Check if the merge resulted in an empty DataFrame
if data.empty:
    raise ValueError("The merged DataFrame is empty. Check the alignment of timestamps in 'index_data' and 'load_profile'.")

# Perform all calculations in the matrix
data['electricity_cost'] = data.apply(
    lambda row: dynamic_electricity_cost(row['Index'], kW_peak, row['Volume_Afname_kWh']), axis=1
)

# Aggregate results to calculate yearly totals
total_electricity_cost = data['electricity_cost'].sum()
total_load_consumption = data['Volume_Afname_kWh'].sum()

# Save the results to a new file
data.to_excel('results/electricity_cost_results_yearly.xlsx', index=False)

# Print yearly summary
print(f"Total Electricity Cost (Yearly): €{total_electricity_cost:.2f}")
print(f"Total Load Consumption (Yearly): {total_load_consumption:.2f} kWh")

