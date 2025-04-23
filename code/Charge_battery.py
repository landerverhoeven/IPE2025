import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from battery1 import calculate_power_difference

def charge_battery(battery_capacity, power_output, belpex_data, load_profile):
    """
    Determines the hours during which the battery should be charged based on electricity prices and power difference.

    Parameters:
        battery_capacity (float): The capacity of the battery in kWh.
        power_output (DataFrame): DataFrame containing power output data.
        belpex_data (DataFrame): DataFrame containing electricity prices.
        load_profile (DataFrame): DataFrame containing the load profile.

    Returns:
        dict: A dictionary where keys are days and values are lists of hours to charge the battery.
    """
    # Normalize column names
    belpex_data.columns = belpex_data.columns.str.strip().str.lower()
    load_profile.columns = load_profile.columns.str.strip().str.lower()

    # Ensure 'datetime' and 'datum_startuur' are in the same timezone
    belpex_data['datetime'] = pd.to_datetime(belpex_data['datetime']).dt.tz_localize(None)
    load_profile['datum_startuur'] = pd.to_datetime(load_profile['datum_startuur'])

    # Calculate the power difference
    power_difference_data = calculate_power_difference(power_output, load_profile)
    power_difference_data['power_difference_kwh'] = power_difference_data['power_difference_kwh'].clip(lower=0)
    # Resample power_difference_data to hourly intervals
    power_difference_data['datetime'] = pd.to_datetime(power_difference_data['datetime'])
    power_difference_data.set_index('datetime', inplace=True)
    hourly_power_difference = power_difference_data.resample('H').sum().reset_index()

    # Debug: Print the dtypes of datetime columns
    #print("Debug: Belpex Data DateTime dtype:", belpex_data['datetime'].dtype)
    #print("Debug: Hourly Power Difference DateTime dtype:", hourly_power_difference['datetime'].dtype)

    # Merge the hourly power difference data with the Belpex data
    merged_data = pd.merge(
        belpex_data,
        hourly_power_difference,
        left_on='datetime',
        right_on='datetime',
        how='inner'
    )

    # Group data by day
    merged_data['day'] = merged_data['datetime'].dt.date
    grouped = merged_data.groupby('day')
    
    charge_schedule = {}

    # Process each day
    for day, group in grouped:
        # Sort by price (cheapest to most expensive)
        sorted_group = group.sort_values(by='euro')
        
        total_power = 0
        charge_hours = []
        
        # Iterate through the sorted hours
        for _, row in sorted_group.iterrows():
            hour = row['datetime'].hour
            power_difference = row['power_difference_kwh']
            
            # Only add the hour if power_difference is not 0
            if power_difference != 0:
                # Add power difference to the total
                total_power += power_difference
                charge_hours.append(hour)
            
            # Check if the battery capacity is reached
            if total_power >= battery_capacity:
                break
        
        # Store the charging hours for the day
        charge_schedule[day] = charge_hours
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
    return charge_schedule, merged_data