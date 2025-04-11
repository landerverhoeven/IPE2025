import pandas as pd
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
    
    return charge_schedule, merged_data