import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from calculations_power import power_output, load_power
from average_power import average_power
from day_night_electricity_cost import day_night_electricity_cost
from day_night_electricity_cost import is_daytime

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

#average_power(N, beta, A, eta, phi_panel)
power_output_data = power_output(N, beta, A, eta, phi_panel)

# Cost in case of day/night tariff
# Prices for day and night source: engie (vtest)
price_day = 0.1489  # Example price for day
price_night = 0.1180  # Example price for night
injection_price = 0.0465  # Example price for injection

# Read data from Excel files
load_profile = pd.read_excel('data\\Load_profile_8.xlsx')  # File with date-time and consumption values

# Convert the first column to date_time format
load_profile['Datum_Startuur'] = pd.to_datetime(load_profile.iloc[:, 0])

# Calculate day and night electricity cost
# VERY IMPORTANT: 
# Change the load_profile and power_output_data to the actual amount that is subtracted from and injected in the grid
# this is an example for the simple situation where there is no battery:
difference = load_profile['Volume_Afname_kWh'] - power_output_data['Power_Output_kWh']
load_profile['Volume_Afname_kWh'] = np.where(difference < 0, 0, difference)
power_output_data['Power_Output_kWh'] = np.where(difference < 0, -difference, 0)

load_profile, totalelectricity, totalnetwork, totaltaxes, totalcost = day_night_electricity_cost(price_day, price_night, injection_price, load_profile, power_output_data)

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
power_output_day = power_output_data[power_output_data['DateTime'].apply(is_daytime)]
power_output_night = power_output_data[~power_output_data['DateTime'].apply(is_daytime)]
print('Day power output:', power_output_day['Power_Output_kWh'].sum(), 'kWh')
print('Night power output:', power_output_night['Power_Output_kWh'].sum(), 'kWh')


'''
# Plot the total cost per 15min
plt.plot(load_profile['Datum_Startuur'], load_profile['total_cost_per_15min'])
plt.xlabel('Date Time')
plt.ylabel('Total Cost per 15min')
plt.title('Total Cost per 15min Over Time')
plt.xlim(pd.Timestamp('2022-01-01'), pd.Timestamp('2022-01-02'))
plt.show()
'''
