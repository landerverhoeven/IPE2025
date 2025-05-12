import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns
import matplotlib.colors as mcolors
import tabulate
from plot import average_power, power_per_year, belpex_visualisation
from dynamic_electricity_cost import calculate_total_dynamic_cost
from day_night_electricity_cost import day_night_electricity_cost
from correct_data_files import all_correct_data_files
from battery1 import calculate_power_difference, calculate_average_daily_power_difference
from Charge_battery import charge_battery, smart_battery_merge
from Discharge_battery import discharge_battery
from financial_evaluation import financial_evaluation
from Conventional_charge_discharge import conventional_battery
from EV_charge import charge_ev_weekly

def main(tilt_module, azimuth_module_1, azimuth_module_2, battery_type):
    # Constants for PV system
    WP_panel = 445  # Panel power (W)
    N_module = 24  # Number of panels

    battery_capacity = 6.5  # Battery capacity (kWh)
    battery_capacity_ev = 65  # EV battery capacity (kWh)
    battery_capacity_ev_min = 0.2 * battery_capacity_ev  # Minimum charge level (20% of capacity)
    battery_capacity_ev_max = 1 * battery_capacity_ev  # Maximum charge level (80% of capacity)

    # Costs
    if battery_type == 0 or battery_type == 3:
        battery_cost = 3289.04
    else:
        battery_cost = 0
    subtotal1 = 7213.78 - battery_cost # flat mounting system
    subtotal2 = 7476.26 - battery_cost # tilted mounting system
    if tilt_module == np.radians(5):
        investment_cost = subtotal1
    elif tilt_module == np.radians(35):
        investment_cost = subtotal2
    else:
        raise ValueError("Invalid tilt angle. Use 5° for flat roof or 35° for tilted roof.")
    financing_rate = 0.02  # Example financing rate (5%)
    financing_period = 20  # Example financing period (20 years)
    
    

    # importing corrected files (first run data_configuration to correct the files)

    #power_output = pd.read_pickle('data/Corrected_power_output.pkl')
    load_profile_old = pd.read_pickle('data/Corrected_load_profile.pkl')
    belpex_data_old = pd.read_pickle('data/Corrected_belpex_data.pkl')
    #data = pd.read_pickle('data/Corrected_data.pkl')
    

    # The csv files
    power_output_old  = pd.read_csv('data/Irradiance_data.csv', parse_dates=['DateTime'])
    #load_profile_old = pd.read_csv('data/Load_profile_8.csv', parse_dates=['Datum_Startuur'])
    #belpex_data_old = pd.read_csv('data/Belpex_2024.csv', delimiter=';', parse_dates=['Date'], encoding='ISO-8859-1', dayfirst=True)
    data, power_output, load_profile, belpex_data = all_correct_data_files(power_output_old, load_profile_old, belpex_data_old, WP_panel, N_module, tilt_module, azimuth_module_1, azimuth_module_2)

    # Visualize the data
    #power_per_year(power_output, load_profile)
    #average_power(power_output, load_profile)
    #belpex_visualisation(belpex_data)

    # Calculate power difference for all timestamps
    #power_difference = calculate_power_difference(data)
    data[['datetime', 'power_difference_kwh', 'power_difference_kwh_for_conventional']] = calculate_power_difference(data)
    # Battery
    if battery_type == 0:
        evaluated_battery = [0]
    elif battery_type == 1:
        conventional_charge_schedule, conventional_discharge_schedule, conventional_charge_discharge_schedule = conventional_battery(battery_capacity, data)
        evaluated_battery = conventional_charge_discharge_schedule
    elif battery_type == 2:
        charge_schedule, data2, end_of_day_charge_level, battery_charge = charge_battery(battery_capacity, data)
        discharge_schedule = discharge_battery(data2, end_of_day_charge_level, charge_schedule)
        smart_battery = smart_battery_merge(battery_charge, discharge_schedule)
        evaluated_battery = smart_battery
    elif battery_type == 3:
        charge_schedule, data2, end_of_day_charge_level, battery_charge = charge_battery(battery_capacity, data)
        ev_charge_schedule = charge_ev_weekly(data, battery_capacity_ev, charge_schedule)
        evaluated_battery = ev_charge_schedule
    else:
        raise ValueError("Invalid battery type.")

    '''
    print("conventional_charge_discharge_schedule:")
    print(conventional_charge_discharge_schedule.head(50))

    print("smart_charge_schedule:")
    print(battery.head(50))
    '''

    # FINANCIAL EVALUATION
    # Cost in case of day/night tariff and dynamic tariff
    variable_data, totalcost_variable = day_night_electricity_cost(data, evaluated_battery)
    totalcost_dynamic = calculate_total_dynamic_cost(data, evaluated_battery)
    capex, opex, npv_variable, npv_dynamic, payback_period_variable, payback_period_dynamic = financial_evaluation(data, totalcost_variable, totalcost_dynamic, investment_cost, financing_rate, financing_period)




    







    '''
    #POST-PROCESSING


    data['datetime'] = pd.to_datetime(data['datetime']).dt.tz_localize(None)

    # Filter the data for July 1st
    july_1st = data[
        (data['datetime'] >= pd.Timestamp('2000-07-27')) &
        (data['datetime'] < pd.Timestamp('2000-07-28'))
    ]
    july_1st_smart_schedule = smart_battery[
        (smart_battery['datetime'] >= pd.Timestamp('2000-07-27')) &
        (smart_battery['datetime'] < pd.Timestamp('2000-07-28'))
    ]
    # Plot the power output, load profile, and electricity price
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot power output and load profile on the primary y-axis
    ax1.plot(july_1st['datetime'], july_1st['Power_Output_kWh'], label='Power Output (kWh)', color='blue')
    ax1.plot(july_1st['datetime'], july_1st['Volume_Afname_kWh'], label='Load Profile (kWh)', color='red')
    ax1.plot(july_1st_smart_schedule['datetime'], july_1st_smart_schedule['charge_power'], label='Charge Schedule (kWh)', color='orange')

    # Set axis labels with larger font size
    ax1.set_xlabel('Datetime', fontsize=14)
    ax1.set_ylabel('Energy (kWh)', color='black', fontsize=14)
    ax1.tick_params(axis='y', labelcolor='black', labelsize=12)
    ax1.tick_params(axis='x', labelsize=12)
    ax1.grid(True)

    # Create a secondary y-axis for electricity price
    ax2 = ax1.twinx()
    ax2.plot(july_1st['datetime'], july_1st['Euro'], label='Electricity Price (€/MWh)', color='green')
    ax2.set_ylabel('Electricity Price (€/MWh)', color='green', fontsize=14)
    ax2.tick_params(axis='y', labelcolor='green', labelsize=12)

    # Add title and legend with larger font size
    fig.suptitle('Power Output, Load Profile, Charge Schedule, and Electricity Price on July 27, 2024', fontsize=16)
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9), fontsize=12)

    # Adjust layout and save the plot
    fig.tight_layout()
    plt.savefig('results/power_output_load_profile_price_charge_discharge_july_1st.png')
    #plt.show()

    data['datetime'] = pd.to_datetime(data['datetime']).dt.tz_localize(None)
    data.to_excel('results/data.xlsx', index=False)



    df = data.copy()

    # Extract relevant time info
    df['date'] = df['datetime'].dt.date  # Extract the date for the y-axis
    df['time'] = df['datetime'].dt.time  # Extract the time for the x-axis
    # Create heatmap matrix (date vs. time)
    heatmap_data = df.pivot_table(
        index='date',  # Rows represent dates
        columns='time',  # Columns represent times
        values='Euro',
        aggfunc='mean'
    ).fillna(0)
    # Plot heatmap
    norm = mcolors.TwoSlopeNorm(vmin=-20, vcenter=130, vmax=500)

    plt.figure(figsize=(18, 8))
    ax = sns.heatmap(
        heatmap_data,
        cmap="RdBu_r",  # Diverging colormap: green for positive, blue for negative
        norm=norm,  # Use the custom normalization
        center=0,  # Center the colormap at 0
        cbar_kws={'label': 'Electricity Price (€/MWh)'},  # Larger font for colorbar label
        xticklabels=8,  # Show every 8th time label
        yticklabels=30  # Show every 30th date label
    )

    # Set title and axis labels with larger font sizes
    plt.title("Electricity Price (Year Overview)", fontsize=18)
    plt.xlabel("Time of Day", fontsize=16)
    plt.ylabel("Date", fontsize=16)
    plt.xticks(fontsize=14, rotation=45)  # Rotate x-axis labels for better readability
    plt.yticks(fontsize=14)
    # Adjust colorbar font size
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(labelsize=14)  # Set font size for colorbar ticks
    plt.tight_layout()
    plt.savefig('results/electricty_price_heatmap.png')
    #plt.show()





    
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
    plt.close('all')
 # Constants for PV system

# ------------------------ Variables ------------------------

start_time = time.time()
for battery_type in range(4):
    # Mapping battery types to their names
    battery_type_names = {0: "No", 1: "Conventional", 2: "Smart", 3: "EV"}
    print("************* Battery type: {} Battery *************".format(battery_type_names.get(battery_type, "Unknown")))
    
    # Flat roof - Southern orientation
    tilt_module = np.radians(5)  # Panel tilt angle (radians). 5°: Flat roof, 30°-40°: Tilted roof.
    azimuth_module_1 = np.radians(180) # Panel azimuth angle (radians). 90°: Facing east., 180°: Facing south., 270°: Facing west, 0°: Facing north.
    azimuth_module_2 = np.radians(180)  # Panel azimuth angle (radians). 90°: Facing east., 180°: Facing south., 270°: Facing west, 0°: Facing north.
    print("------------- Flat roof - Southern orientation -------------")
    main(tilt_module, azimuth_module_1, azimuth_module_2, battery_type)

    # Flat roof - East-West orientation
    tilt_module = np.radians(5)  # Panel tilt angle (radians). 5°: Flat roof, 30°-40°: Tilted roof.
    azimuth_module_1 = np.radians(90) # Panel azimuth angle (radians). 90°: Facing east., 180°: Facing south., 270°: Facing west, 0°: Facing north.
    azimuth_module_2 = np.radians(270)  # Panel azimuth angle (radians). 90°: Facing east., 180°: Facing south., 270°: Facing west, 0°: Facing north.
    print("------------- Flat roof - East-West orientation -------------")
    main(tilt_module, azimuth_module_1, azimuth_module_2, battery_type)

    # Gable roof - Southern orientation
    tilt_module = np.radians(35)  # Panel tilt angle (radians). 5°: Flat roof, 30°-40°: Tilted roof.
    azimuth_module_1 = np.radians(180) # Panel azimuth angle (radians). 90°: Facing east., 180°: Facing south., 270°: Facing west, 0°: Facing north.
    azimuth_module_2 = np.radians(180)  # Panel azimuth angle (radians). 90°: Facing east., 180°: Facing south., 270°: Facing west, 0°: Facing north.
    print("------------- Gable roof - Southern orientation -------------")
    main(tilt_module, azimuth_module_1, azimuth_module_2, battery_type)

    # Gable roof - East-West orientation
    tilt_module = np.radians(35)  # Panel tilt angle (radians). 5°: Flat roof, 30°-40°: Tilted roof.
    azimuth_module_1 = np.radians(90) # Panel azimuth angle (radians). 90°: Facing east., 180°: Facing south., 270°: Facing west, 0°: Facing north.
    azimuth_module_2 = np.radians(270)  # Panel azimuth angle (radians). 90°: Facing east., 180°: Facing south., 270°: Facing west, 0°: Facing north.
    print("------------- Gable roof - East-West orientation -------------")
    main(tilt_module, azimuth_module_1, azimuth_module_2, battery_type)

end_time = time.time()
print("Execution time: {:.2f} seconds".format(end_time - start_time))
