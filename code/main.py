import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from average_power import average_power
from day_night_electricity_cost import day_night_electricity_cost
from day_night_electricity_cost import is_daytime
from correct_data_files import correct_belpex_data, correct_load_profile, correct_irradiance_data
from power_per_year import power_per_year

# Constants for PV system
beta = np.radians(20)  # Panel tilt angle (radians)
A = 2  # Panel area (m^2)
eta = 0.18  # Panel efficiency (18%)
N = 2  # Number of panels
phi_panel = np.radians(180)  # Panel azimuth angle (radians)

# Costs
scissor_lift_cost = 170  # incl. vat
installation_cost = 1200  # incl.vat
uniet_solar_panel_cost = 110  # incl. vat

# Read and correct all the data files
power_output = correct_irradiance_data(N, beta, A, eta, phi_panel, pd.read_excel('data\\Irradiance_data.xlsx'))  # File with date-time and irradiance values
load_profile = correct_load_profile(pd.read_excel('data\\Load_profile_8.xlsx'))  # File with date-time and consumption values
belpex_data = correct_belpex_data(pd.read_excel('data\\Belpex_data.xlsx'))  # File with date-time and index values

power_per_year(power_output, load_profile)
average_power(power_output, load_profile)
total_power_output = power_output['Power_Output_kWh'].sum()
print('Total power output:', total_power_output, 'kWh')

# Cost in case of day/night tariff
# Prices for day and night source: engie (vtest)
price_day = 0.1489  # Example price for day
price_night = 0.1180  # Example price for night
injection_price = 0.05  # Example price for injection

# Calculate day and night electricity cost
load_profile, totalelectricity, totalnetwork, totaltaxes, totalcost = day_night_electricity_cost(price_day, price_night, injection_price, load_profile, power_output)

# Print somle useful information
print('total electricity costs:', totalelectricity, 'eur')
print('network costs:', totalnetwork, 'eur')
print('taxes:', totaltaxes, 'eur')
print('total costs:', totalcost, 'eur')

# Load day and night
load_day = load_profile[load_profile['Datum_Startuur'].apply(is_daytime)]
load_night = load_profile[~load_profile['Datum_Startuur'].apply(is_daytime)]
print('day load:', load_day['Volume_Afname_kWh'].sum(), 'kWh')
print('night load:', load_night['Volume_Afname_kWh'].sum(), 'kWh')


'''
# Plot the total cost per 15min
plt.plot(load_profile['Datum_Startuur'], load_profile['total_cost_per_15min'])
plt.xlabel('Date Time')
plt.ylabel('Total Cost per 15min')
plt.title('Total Cost per 15min Over Time')
plt.xlim(pd.Timestamp('2022-01-01'), pd.Timestamp('2022-01-02'))
plt.show()
'''
