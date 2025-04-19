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
N_module = 20  # Number of panels

battery_capacity = 3  # Battery capacity (kWh)

# Costs
scissor_lift_cost = 170  # incl. vat
installation_cost = 1200  # incl.vat
uniet_solar_panel_cost = 110  # incl. vat

# Calculate power_output, load_profile, and belpex_data
power_output_data = pd.read_excel('data/Irradiance_data.xlsx')
load_profile_data = pd.read_excel('data/Load_profile_8.xlsx')
belpex_data_data = pd.read_excel('data/Belpex_2024.xlsx')
data, power_output, load_profile, belpex_data = all_correct_data_files(power_output_data, load_profile_data, belpex_data_data, WP_panel, N_module, tilt_module, azimuth_module)

# Cost in case of day/night tariff
# Prices for day and night source: engie (vtest)
price_day = 0.1489  # Example price for day
price_night = 0.1180  # Example price for night
injection_price = 0.0465  # Example price for injection

power_per_year(power_output, load_profile)
average_power(power_output, load_profile)

# Calculate day and night electricity cost
# VERY IMPORTANT: 
# Change the load_profile and power_output to the actual amount that is subtracted from and injected in the grid
# this is an example for the simple situation where there is no battery:
difference = load_profile['Volume_Afname_kWh'] - power_output['Power_Output_kWh']
load_profile['Volume_Afname_kWh'] = np.where(difference < 0, 0, difference)
power_output['Power_Output_kWh'] = np.where(difference < 0, -difference, 0)

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

# Calculate power difference for all timestamps
power_difference = calculate_power_difference(power_output, load_profile)
power_difference['power_difference_kwh'] = power_difference['power_difference_kwh'].clip(lower=0)


## Plot power_output, power_difference, and load_profile on the same graph
#plt.figure(figsize=(12, 6))
#plt.plot(power_output['datetime'], power_output['power_output_kwh'], label='Power Output (kWh)', color='blue')
#plt.plot(power_difference['datetime'], power_difference['power_difference_kwh'], label='Power Difference (kWh)', color='orange')
#plt.plot(load_profile['datum_startuur'], load_profile['volume_afname_kwh'], label='Load Profile (kWh)', color='red')
#plt.xlabel('Datetime')
#plt.ylabel('Energy (kWh)')
#plt.title('Power Output, Power Difference, and Load Profile')
#plt.grid(True)
#plt.legend()
#plt.tight_layout()
#
## Save the plot as an image
#plt.savefig('results/power_output_difference_load_profile.png')
#plt.show()
# Debug: Print the power_difference DataFrame to verify its structure
#print("Power Difference DataFrame:")
#print(power_difference.head())
#print(power_difference.columns)

# Save the power difference to an Excel file
power_difference.to_excel('results/power_difference.xlsx', index=False)

# Calculate the total surplus
print('Total surplus:', power_difference["power_difference_kwh"].sum(), 'kWh')



# Debug: Print the load_profile DataFrame to verify its structure
#print("Load Profile Columns (before reset):", load_profile.columns)
#print(load_profile.head())

# Ensure load_profile has 'Datum_Startuur' as a column
if 'Datum_Startuur' not in load_profile.columns:
    load_profile = load_profile.reset_index()  # Reset index to make 'Datum_Startuur' a column


# Debug: Print the load_profile DataFrame to verify its structure after reset
#print("Load Profile Columns (after reset):", load_profile.columns)
#print(load_profile.head())

# Call charge_battery with the correct power_output and load_profile
charge_schedule, merged_data = charge_battery(battery_capacity, power_output, belpex_data, load_profile)
#print('Charge schedule:', charge_schedule)

# Convert charge_schedule dictionary to a DataFrame
charge_schedule_df = pd.DataFrame([
    {'Day': day, 'Hour': hour} for day, hours in charge_schedule.items() for hour in hours
])

# Save the charge_schedule DataFrame to an Excel file
charge_schedule_df.to_excel('results/charge_schedule.xlsx', index=False)
merged_data.to_excel('results/merge_data.xlsx', index=False)
#power_output.to_excel('results/power_output6.xlsx', index=False)
#load_profile.to_excel('results/load_profile6.xlsx', index=False)
#power_difference.to_excel('results/power_difference6.xlsx', index=False)

# Prepare data for the heatmap
days = sorted(charge_schedule.keys())  # Sorted list of days
hours = range(24)  # Hours of the day (0-23)
heatmap_data = np.zeros((len(days), len(hours)))  # Initialize a 2D array

# Populate the heatmap data
for i, day in enumerate(days):
    for hour in charge_schedule[day]:
        heatmap_data[i, hour] = 1  # Mark charging hours

# Create the heatmap
plt.figure(figsize=(12, 8))
plt.imshow(heatmap_data, aspect='auto', cmap='Greens', origin='lower')
plt.colorbar(label='Charging (1 = Yes, 0 = No)')
plt.xticks(ticks=np.arange(len(hours)), labels=hours)
plt.yticks(ticks=np.arange(len(days))[::30], labels=[str(day) for day in days[::30]])  # Show every 30th day
plt.xlabel('Hour of the Day')
plt.ylabel('Day of the Year')
plt.title('Battery Charging Hours Over the Year')
plt.tight_layout()

# Save the plot as an image
plt.savefig('results/charging_hours_heatmap.png')
plt.show()

# Prepare data for the plot
charging_data = []

# Loop through the charge_schedule to filter power_output data
for day, hours in charge_schedule.items():
    for hour in hours:
        # Filter the power_output for the specific day and hour
        charging_datetime = pd.Timestamp(day) + pd.Timedelta(hours=hour)
        matching_row = power_output[power_output['datetime'] == charging_datetime]
        if not matching_row.empty:
            charging_data.append(matching_row)

# Combine all the filtered rows into a single DataFrame
charging_data = pd.concat(charging_data)

# Plot the charging power output
plt.figure(figsize=(12, 6))
plt.plot(charging_data['datetime'], charging_data['power_output_kwh'], label='Charging Power Output', color='blue')
plt.xlabel('Datetime')
plt.ylabel('Power Output (kWh)')
plt.title('Battery Charging Power Output Over the Year')
plt.grid(True)
plt.legend()
plt.tight_layout()

# Save the plot as an image
plt.savefig('results/charging_power_output_plot.png')
plt.show()

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