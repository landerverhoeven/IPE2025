import time
start_time = time.time()
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
from battery1 import calculate_power_difference
from battery1 import calculate_average_daily_power_difference
from average_power import average_power
from Charge_battery import charge_battery

# Constants for PV system
tilt_module = np.radians(30)  # Panel tilt angle (radians)
azimuth_module = np.radians(90)  # Panel azimuth angle (radians)
WP_panel = 350  # Panel power (W)
N_module = 15  # Number of panels

battery_capacity = 10  # Battery capacity (kWh)

# Costs
scissor_lift_cost = 170  # incl. vat
installation_cost = 1200  # incl.vat
uniet_solar_panel_cost = 110  # incl. vat

end_time = time.time()
print(f"Runtime for importing packages: {end_time - start_time:.2f} seconds")

# Calculate power_output, load_profile, and belpex_data
start_time = time.time()
power_output_data = pd.read_excel('data/Irradiance_data.xlsx')
end_time = time.time()
print(f"Runtime for reading irradiance_data: {end_time - start_time:.2f} seconds")
start_time = time.time()
load_profile_data = pd.read_excel('data/Load_profile_8.xlsx')
end_time = time.time()
print(f"Runtime for reading load profile 8: {end_time - start_time:.2f} seconds")
start_time = time.time()
belpex_data_data = pd.read_excel('data/Belpex_2024.xlsx')
end_time = time.time()
print(f"Runtime for reading belpex: {end_time - start_time:.2f} seconds")
start_time = time.time()
data, power_output, load_profile, belpex_data = all_correct_data_files(power_output_data, load_profile_data, belpex_data_data, WP_panel, N_module, tilt_module, azimuth_module)
end_time = time.time()
print(f"Runtime for correcting all data files: {end_time - start_time:.2f} seconds")
print("main: ", load_profile.head())
# Cost in case of day/night tariff
load_profile2 = load_profile.copy()
power_output2 = power_output.copy()
# Prices for day and night source: engie (vtest)
price_day = 0.1489 + 0.0117 + 0.0042 # Price for day + green energy + WKK
price_night = 0.1180 + 0.0117 + 0.0042 # Price for night + green energy + WKK
injection_price = 0.0465  # Example price for injection

# Visualize the data
#power_per_year(power_output, load_profile)
#average_power(power_output, load_profile)

# Calculate day and night electricity cost
# VERY IMPORTANT: 
# Change the load_profile and power_output to the actual amount that is subtracted from and injected in the grid
# this is an example for the simple situation where there is no battery:
# difference = load_profile['Volume_Afname_kWh'] - power_output['Power_Output_kWh']
# load_profile['Volume_Afname_kWh'] = np.where(difference < 0, 0, difference)
# power_output['Power_Output_kWh'] = np.where(difference < 0, -difference, 0)

variable_data, totalelectricity, totalnetwork, totaltaxes, totalcost = day_night_electricity_cost(price_day, price_night, injection_price, load_profile, power_output)

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
print(power_output.head())
power_output_day = power_output[power_output['DateTime'].apply(is_daytime)]
power_output_night = power_output[~power_output['DateTime'].apply(is_daytime)]
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

# Calculate power difference for all timestamps
power_difference = calculate_power_difference(data)


# Ensure load_profile has 'Datum_Startuur' as a column
#if 'Datum_Startuur' not in load_profile.columns:
#    load_profile = load_profile.reset_index()  # Reset index to make 'Datum_Startuur' a column


# Call charge_battery with the correct power_output and load_profile
charge_schedule, merged_data = charge_battery(battery_capacity, power_difference, data)
#print('Charge schedule:', charge_schedule)

# Convert charge_schedule dictionary to a DataFrame

'''
# Filter the power_difference data for the first day of January
first_day = power_difference[
    (power_difference['datetime'] >= pd.Timestamp('2024-01-01')) &
    (power_difference['datetime'] < pd.Timestamp('2024-01-02'))
]

# Print the values for January 1st
print("Power Difference Values on January 1st, 2024:")
print(first_day)

# Plot the power difference for the first day of January
plt.figure(figsize=(12, 6))
plt.plot(first_day['datetime'], first_day['power_difference_kwh'], label='Power Difference (kWh)', color='orange')
plt.xlabel('Datetime')
plt.ylabel('Power Difference (kWh)')
plt.title('Power Difference on January 1st, 2024')
plt.grid(True)
plt.legend()
plt.tight_layout()

# Save the plot as an image
plt.savefig('results/power_difference_january_1st.png')
plt.show()

# Filter the power_output and load_profile data for the first day of January
first_day_power_output = power_output[
    (power_output['datetime'] >= pd.Timestamp('2024-01-01')) &
    (power_output['datetime'] < pd.Timestamp('2024-01-02'))
]

first_day_load_profile = load_profile[
    (load_profile['datum_startuur'] >= pd.Timestamp('2024-01-01')) &
    (load_profile['datum_startuur'] < pd.Timestamp('2024-01-02'))
]

# Plot both power output and load profile on the same graph
plt.figure(figsize=(12, 6))
plt.plot(first_day_power_output['datetime'], first_day_power_output['power_output_kwh'], label='Power Output (kWh)', color='blue')
plt.plot(first_day_load_profile['datum_startuur'], first_day_load_profile['volume_afname_kwh'], label='Load Profile (kWh)', color='red')
plt.xlabel('Datetime')
plt.ylabel('Energy (kWh)')
plt.title('Power Output and Load Profile on January 1st, 2024')
plt.grid(True)
plt.legend()
plt.tight_layout()

# Save the plot as an image
plt.savefig('results/power_output_and_load_profile_january_1st.png')
plt.show()
'''