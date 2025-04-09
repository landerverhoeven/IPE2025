import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from average_power import average_power
from dynamic_electricity_cost import calculate_total_dynamic_cost
from day_night_electricity_cost import day_night_electricity_cost
from day_night_electricity_cost import is_daytime
from correct_data_files import all_correct_data_files
from power_per_year import power_per_year

# Constants for PV system
tilt_module = np.radians(30)  # Panel tilt angle (radians)
WP_panel = 250  # Panel power (W)
N_module = 4  # Number of panels
azimuth_module = np.radians(90)  # Panel azimuth angle (radians)

# Costs
scissor_lift_cost = 170  # incl. vat
installation_cost = 1200  # incl.vat
uniet_solar_panel_cost = 110  # incl. vat

# File paths (using os.path.join for cross-platform compatibility)
data_folder = "data"
belpex_path = os.path.join(data_folder, "Belpex_data.xlsx")
load_profile_path = os.path.join(data_folder, "Load_profile_8.xlsx")
irradiance_path = os.path.join(data_folder, "Irradiance_data.xlsx")

# Read and correct all the data files
data, power_output, load_profile, belpex_data = all_correct_data_files(pd.read_excel(irradiance_path), pd.read_excel(load_profile_path), pd.read_excel(belpex_path), WP_panel, N_module, tilt_module, azimuth_module)

power_per_year(power_output, load_profile)
average_power(power_output, load_profile)

# Calculate total cost using in-memory data
total_cost = calculate_total_dynamic_cost(power_output, load_profile, belpex_data)

# Cost in case of day/night tariff
# Prices for day and night source: engie (vtest)
price_day = 0.1489  # Example price for day
price_night = 0.1180  # Example price for night
injection_price = 0.05  # Example price for injection

# Calculate day and night electricity cost
#load_profile, totalelectricity, totalnetwork, totaltaxes, totalcost = day_night_electricity_cost(price_day, price_night, injection_price, load_profile, power_output)

# Load day and night
#load_day = load_profile[load_profile['Datum_Startuur'].apply(is_daytime)]
#load_night = load_profile[~load_profile['Datum_Startuur'].apply(is_daytime)]
#print('day load:', load_day['Volume_Afname_kWh'].sum(), 'kWh')
#print('night load:', load_night['Volume_Afname_kWh'].sum(), 'kWh')


'''
# Plot the total cost per 15min
plt.plot(load_profile['Datum_Startuur'], load_profile['total_cost_per_15min'])
plt.xlabel('Date Time')
plt.ylabel('Total Cost per 15min')
plt.title('Total Cost per 15min Over Time')
plt.xlim(pd.Timestamp('2022-01-01'), pd.Timestamp('2022-01-02'))
plt.show()
'''
