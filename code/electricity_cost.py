import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# SOURCE: ENGIE

# General 
vat_tarrif = 1.06

def dynamic_electricity_cost(index, kW_peak, load_consumption, vat_tarrif):
    # Cost energy produced
    fixed_fee = 100.70
    dynamic_price = (0.1 * index + 1.316) * vat_tarrif / 100

    cost_energy_produced = fixed_fee + dynamic_price * load_consumption

    # Income energy injected
    income_energy_injected = (0.1 * index - 1.3050) * vat_tarrif / 100

    # Network costs
    capacity_tarrif = 51.9852 * kW_peak
    take_off_fee = 5.60719 / 100
    data_management_fee = 18.56

    network_costs = capacity_tarrif + take_off_fee * load_consumption + data_management_fee

    # Taxes
    energy_contribution = 0.20417 / 100
    federal_energy_tax = 5.03288 / 100

    taxes = (energy_contribution + federal_energy_tax) * load_consumption

    formula_for_electricity = cost_energy_produced + network_costs + taxes - income_energy_injected * 0

    return formula_for_electricity



# Read data from files
index_data = pd.read_excel('data\Belpex_data.xlsx')  # File with date-time and index values
load_consumption_data = pd.read_excel('data\Load_profile_8.xlsx')  # File with date-time and consumption values

# Read load profile to calculate kW_peak
load_profile = pd.read_excel('data\Load_profile_8.xlsx')  # File with date-time and consumption values
load_profile['date_time'] = pd.to_datetime(load_profile['date_time'])
load_profile['month'] = load_profile['date_time'].dt.to_period('M')

# Convert kWh to kW for kW_peak calculation (assuming hourly data)
load_profile['load_consumption_kw'] = load_profile['load_consumption_kwh'] / 1  # 1 hour assumed

# Calculate kW_peak for each month
monthly_kW_peak = load_profile.groupby('month')['load_consumption_kw'].max().reset_index()
monthly_kW_peak.rename(columns={'load_consumption_kw': 'kW_peak'}, inplace=True)

# Ensure the data is aligned by date-time
data = pd.merge(index_data, load_consumption_data, on='date_time', suffixes=('_index', '_load'))
data['date_time'] = pd.to_datetime(data['date_time'])
data['month'] = data['date_time'].dt.to_period('M')

# Merge kW_peak into the main data
data = pd.merge(data, monthly_kW_peak, on='month', how='left')

# Calculate dynamic electricity cost for each row
data['electricity_cost'] = data.apply(
    lambda row: dynamic_electricity_cost(row['index'], row['kW_peak'], row['load_consumption'], vat_tarrif), axis=1
)

# Save the results to a new file
data.to_csv('electricity_cost_results.csv', index=False)

