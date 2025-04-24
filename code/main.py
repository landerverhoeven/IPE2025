import time
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
from Discharge_battery import discharge_battery

# Constants for PV system
tilt_module = np.radians(30)  # Panel tilt angle (radians)
azimuth_module = np.radians(90)  # Panel azimuth angle (radians)
WP_panel = 350  # Panel power (W)
N_module = 15  # Number of panels

battery_capacity = 5  # Battery capacity (kWh)

# Costs
scissor_lift_cost = 170  # incl. vat
installation_cost = 1200  # incl.vat
uniet_solar_panel_cost = 110  # incl. vat

# importing corrected files (first run data_configuration to correct the files)
power_output = pd.read_pickle('data/Corrected_power_output.pkl')
load_profile = pd.read_pickle('data/Corrected_load_profile.pkl')
belpex_data = pd.read_pickle('data/Corrected_belpex_data.pkl')
data = pd.read_pickle('data/Corrected_data.pkl')


# Visualize the data
power_per_year(power_output, load_profile)
average_power(power_output, load_profile)



# Cost in case of day/night tariff
variable_data, totalcost_variable = day_night_electricity_cost(data, [0])
print(f'total variabel cost: {totalcost_variable:.2f} eur')

# Cost in case of dynamic tariff
totalcost_dynamic = calculate_total_dynamic_cost(data, [0])
print(f'total dynamic cost: {totalcost_dynamic:.2f} eur')


'''
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
charge_schedule, data, end_of_day_charge_level = charge_battery(battery_capacity, data)
#print('Charge schedule:', charge_schedule)
# Convert charge_schedule dictionary to a DataFrame

discharge_schedule = discharge_battery(data, end_of_day_charge_level)
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