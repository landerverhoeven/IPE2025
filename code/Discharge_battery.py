import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def discharge_battery(data, end_of_day_charge_levels, charge_schedule):
    data= data.copy()  # Create a copy of the input DataFrame to avoid modifying the original
    """
    Discharge the battery based on the power difference and the end-of-day charge level,
    ensuring the battery is not discharged during hours when it is being charged.

    Parameters:
        data (DataFrame): DataFrame containing power difference data.
        end_of_day_charge_levels (list): List of dictionaries containing the end-of-day charge levels for each day.
        charge_schedule (DataFrame): DataFrame containing the charging schedule.

    Returns:
        DataFrame: DataFrame containing the discharge schedule.
    """

    # Initialize variables
    discharge_schedule = {}

    # Convert end_of_day_charge_levels to a dictionary for quick lookup
    end_of_day_charge_dict = {item['Day']: item['End of Day Charge Level (kWh)'] for item in end_of_day_charge_levels}

    # Get the first and last days of the year
    all_days = sorted(data['day'].unique())

    first_day = pd.Timestamp('2024-01-01').date()  # Explicitly set January 1st
    last_day = all_days[-1]

    # Ensure January 1st is included in all_days
    if first_day not in all_days:
        all_days.insert(0, first_day)

    # Use the last day's charge level as the starting charge for the first day
    previous_day_charge = end_of_day_charge_dict.get(last_day, 0)

    grouped = data.groupby('day')

    charge_schedule_grouped = charge_schedule.groupby(charge_schedule['datetime'].dt.date)

    # Iterate through each day in the data
    for day in all_days:

        # Use the previous day's charge level as the starting charge
        current_charge = previous_day_charge

        # Check if the day exists in the grouped data
        if day in grouped.groups:
            group = grouped.get_group(day)
            sorted_group = group.sort_values(by='Euro', ascending=False)
        else:
            # If no data exists for the day, create an empty DataFrame
            sorted_group = pd.DataFrame(columns=['datetime', 'Volume_Afname_kWh', 'Euro'])

        discharge_hours = []
        discharge_power = []

        # Get the charging schedule for the current day
        if day in charge_schedule_grouped.groups:
            charging_hours = charge_schedule_grouped.get_group(day)['datetime'].dt.hour.tolist()
        else:
            charging_hours = []

        # Iterate through the sorted hours
        for _, row in sorted_group.iterrows():
            hour = row['datetime'].hour
            power_difference1 = row['Volume_Afname_kWh']
            power_difference2 = row['power_difference_kwh']

            # Skip discharging if the battery is being charged during this hour
            #if hour in charging_hours:
                #continue

            # Skip discharging if the power difference is positive
            #if power_difference2 != 0:
                #continue

            if current_charge > 0:
                current_charge -= power_difference1  # Discharge the battery
                if current_charge < 0:
                    # Adjust the last discharged power to avoid going below zero
                    power_difference1 -= abs(current_charge)
                    current_charge = 0

                discharge_hours.append(hour)
                discharge_power.append(power_difference1)  # Track the power discharged during this hour

                # Stop discharging if the battery is empty
            if current_charge <= 0:
                break
        if current_charge > 0:
            print(f"Warning: Current charge for {day} is positive with {current_charge} after discharging.")
            

        # Ensure the hours and power are sorted in chronological order
        sorted_indices = sorted(range(len(discharge_hours)), key=lambda i: discharge_hours[i])
        discharge_hours = [discharge_hours[i] for i in sorted_indices]
        discharge_power = [discharge_power[i] for i in sorted_indices]

        # Calculate the charge levels as a cumulative sum of discharge_power
        charge_levels = []
        current_charge = previous_day_charge  # Reset to the starting charge for the day
        for power in discharge_power:
            current_charge -= power
            if current_charge < 0:
                current_charge = 0
            charge_levels.append(current_charge)

        # Store the sorted and calculated data in the discharge_schedule
        discharge_schedule[day] = {
            'hours': discharge_hours,
            'power': discharge_power,
            'current_charge': charge_levels
        }
    
        # Update the previous day's charge level for the next iteration
        previous_day_charge = end_of_day_charge_dict.get(day, 0)


    # Create a DataFrame for the discharge schedule, including discharge power and charge level
    discharge_schedule_df = pd.DataFrame([
        {
            'datetime': 0,
            'Day': day,
            'Hour': hour,
            'Minute': 0,
            'Discharge Power (kWh)': discharge_schedule[day]['power'][i],
            'Charge Level (kWh)': discharge_schedule[day]['current_charge'][i]
        }
        for day in discharge_schedule
        for i, hour in enumerate(discharge_schedule[day]['hours'])
    ])
    
    # Adjust the format of the discharge_schedule_df to match the original data
    discharge_schedule_df['Minute'] = discharge_schedule_df.groupby(['Day', 'Hour']).cumcount() * 15

    # Handle potential issues with daylight saving time and invalid minute values
    discharge_schedule_df['Minute'] = discharge_schedule_df['Minute'].apply(lambda x: {
        60: 1,
        75: 16,
        90: 31,
        105: 46
    }.get(x, x))  # Replace invalid values with the correct ones or keep the original value

    # Warn if unexpected minute values are found
    if (discharge_schedule_df['Minute'] > 46).any():
        print("Warning: Minute value is not in the expected range.")

    # Create the 'datetime' column
    discharge_schedule_df['datetime'] = pd.to_datetime(
        discharge_schedule_df['Day'].astype(str) + ' ' +
        discharge_schedule_df['Hour'].astype(str) + ':' +
        discharge_schedule_df['Minute'].astype(str).str.zfill(2) + ':00'
    )

    # Drop unnecessary columns
    discharge_schedule_df.drop(columns=['Day', 'Hour', 'Minute'], inplace=True)

    # Save the discharge schedule to an Excel file
    discharge_schedule_df.to_excel('results/discharge_schedule.xlsx', index=False)

    # Ensure 'datetime' is in the same timezone as the original data
    discharge_schedule_df['datetime'] = discharge_schedule_df['datetime'].dt.tz_localize("Europe/Brussels", ambiguous="NaT", nonexistent="NaT")

    # Merge the discharge schedule with the original data
    merged_data = pd.merge(data, discharge_schedule_df, on='datetime', how='left', suffixes=('', '_charge'))

    # Fill missing values for discharge power and charge level
    merged_data['Discharge Power (kWh)'] = merged_data['Discharge Power (kWh)'].fillna(0)
    merged_data['Charge Level (kWh)'] = merged_data['Charge Level (kWh)'].fillna(0)

    # Drop unnecessary columns
    merged_data.drop(columns=['day', 'power_difference_kwh'], inplace=True)

    # Create the battery_discharge DataFrame
    battery_discharge = merged_data[['datetime', 'Discharge Power (kWh)', 'Charge Level (kWh)']].rename(
        columns={'Discharge Power (kWh)': 'discharge_power', 'Charge Level (kWh)': 'charge_level'}
    )

    return battery_discharge