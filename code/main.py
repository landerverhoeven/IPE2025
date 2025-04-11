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

# File paths (using os.path.join for cross-platform compatibility)
data_folder = "data"
belpex_path = os.path.join(data_folder, "Belpex_2024.xlsx")
load_profile_path = os.path.join(data_folder, "Load_profile_8.xlsx")
irradiance_path = os.path.join(data_folder, "Irradiance_data.xlsx")

# Read and correct all the data files
data, power_output, load_profile, belpex_data = all_correct_data_files(pd.read_excel(irradiance_path), pd.read_excel(load_profile_path), pd.read_excel(belpex_path), WP_panel, N_module, tilt_module, azimuth_module)

power_per_year(power_output, load_profile)
average_power(power_output, load_profile)

# Debug: Print the power_output DataFrame to verify its structure
#print("Power Output Columns:", power_output.columns)
#print(power_output.head())

# Ensure power_output has 'DateTime' as a column
if 'DateTime' not in power_output.columns:
    power_output = power_output.reset_index()  # Reset index to make 'DateTime' a column

# Debug: Print the power_output DataFrame to verify its structure after reset
#print("Power Output Columns (after reset):", power_output.columns)
#print(power_output.head())

# Calculate total cost using in-memory data
total_cost = calculate_total_dynamic_cost(data)

# Cost in case of day/night tariff
# Prices for day and night source: engie (vtest)
price_day = 0.1489  # Example price for day
price_night = 0.1180  # Example price for night
injection_price = 0.05  # Example price for injection

# Calculate day and night electricity cost
load_profile, totalelectricity, totalnetwork, totaltaxes, totalcost = day_night_electricity_cost(price_day, price_night, injection_price, load_profile, power_output)

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

# Calculate power difference for all timestamps
power_difference = calculate_power_difference(power_output, load_profile)

# Debug: Print the power_difference DataFrame to verify its structure
#print("Power Difference DataFrame:")
#print(power_difference.head())
#print(power_difference.columns)

# Save the power difference to an Excel file
power_difference.to_excel('results/power_difference.xlsx', index=False)

# Calculate the total surplus
print('Total surplus:', power_difference["power_difference_kwh"].sum(), 'kWh')

# Calculate the average daily power difference
average_daily_difference = calculate_average_daily_power_difference(power_difference)

# Save the results to a new Excel file
average_daily_difference.to_excel('results/average_daily_power_difference.xlsx', index=False)
'''
# Plot the results
plt.figure(figsize=(10, 6))
plt.plot(average_daily_difference["TimeOfDay"], average_daily_difference["Power_Difference_kWh"], label="Average Power Difference (kWh)", color="green")
plt.xlabel("Time of Day")
plt.ylabel("Average Power Difference (kWh)")
plt.title("Average Daily Power Difference Over a Year")
plt.xticks(rotation=45)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('results/average_daily_power_difference_plot.png')  # Save the plot as an image
plt.show()
'''

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
charge_schedule = charge_battery(battery_capacity, power_output, belpex_data, load_profile)
#print('Charge schedule:', charge_schedule)

# Prepare data for the heatmap
days = sorted(charge_schedule.keys())  # Sorted list of days
hours = range(24)  # Hours of the day (0-23)
heatmap_data = np.zeros((len(days), len(hours)))  # Initialize a 2D array

# Populate the heatmap data
for i, day in enumerate(days):
    for hour in charge_schedule[day]:
        heatmap_data[i, hour] = 1  # Mark charging hours
'''
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
'''
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
'''
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
'''
# Filter the power_difference data for the first day of January
first_day = power_difference[
    (power_difference['datetime'] >= pd.Timestamp('2024-01-01')) &
    (power_difference['datetime'] < pd.Timestamp('2024-01-02'))
]

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