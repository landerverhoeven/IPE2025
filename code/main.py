import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import tabulate
from plot import average_power, power_per_year, belpex_visualisation
from dynamic_electricity_cost import calculate_total_dynamic_cost
from day_night_electricity_cost import day_night_electricity_cost
from correct_data_files import all_correct_data_files
from battery1 import calculate_power_difference, calculate_average_daily_power_difference
from Charge_battery import charge_battery
from Discharge_battery import discharge_battery
from financial_evaluation import financial_evaluation
from Conventional_charge_discharge import conventional_battery

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
investment_cost = scissor_lift_cost + installation_cost + uniet_solar_panel_cost * N_module
financing_rate = 0.02  # Example financing rate (5%)
financing_period = 20  # Example financing period (20 years)

# importing corrected files (first run data_configuration to correct the files)
start_time = time.time()
power_output = pd.read_pickle('data/Corrected_power_output.pkl')
load_profile = pd.read_pickle('data/Corrected_load_profile.pkl')
belpex_data = pd.read_pickle('data/Corrected_belpex_data.pkl')
data = pd.read_pickle('data/Corrected_data.pkl')
'''
# The excel files
power_output_old  = pd.read_csv('data/Irradiance_data.csv', parse_dates=['DateTime'])
load_profile_old = pd.read_csv('data/Load_profile_8.csv', parse_dates=['Datum_Startuur'])
belpex_data_old = pd.read_csv('data/Belpex_2024.csv', delimiter=';', parse_dates=['Date'], encoding='ISO-8859-1', dayfirst=True)
data, power_output, load_profile, belpex_data = all_correct_data_files(power_output_old, load_profile_old, belpex_data_old, WP_panel, N_module, tilt_module, azimuth_module)
'''
end_time = time.time()
print(f"Data correction took {end_time - start_time:.2f} seconds")

# Visualize the data
#power_per_year(power_output, load_profile)
#average_power(power_output, load_profile)
#belpex_visualisation(belpex_data)



# Calculate power difference for all timestamps
power_difference = calculate_power_difference(data)

#CONVENTIONAL CHARGE/DISCHARGE
conventional_charge_schedule, conventional_discharge_schedule, conventional_discharge_schedule = conventional_battery(battery_capacity, data)
# Call charge_battery with the correct power_output and load_profile
charge_schedule, data2, end_of_day_charge_level, battery = charge_battery(battery_capacity, data)
#print("Charge schedule:")
#print(charge_schedule)
#discharge_schedule = discharge_battery(data, end_of_day_charge_level)

# print what the data type of charge_schedule is
print("Data type of charge_schedule:", type(charge_schedule))


# FINANCIAL EVALUATION
# Cost in case of day/night tariff and dynamic tariff
variable_data, totalcost_variable = day_night_electricity_cost(data, [battery])
totalcost_dynamic = calculate_total_dynamic_cost(data, [0])
capex, opex, npv_variable, npv_dynamic, payback_period_variable, payback_period_dynamic = financial_evaluation(data, totalcost_variable, totalcost_dynamic, investment_cost, financing_rate, financing_period)
# !!!!!! investment_cost needs to be checked !!!!! (Staat in het begin van main)

















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