import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from battery1 import calculate_power_difference
import seaborn as sns


def charge_battery(battery_capacity, data):
    data = data.copy()  # Create a copy of the input DataFrame to avoid modifying the original
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
    #belpex_data.columns = belpex_data.columns.str.strip().str.lower()
    #load_profile.columns = load_profile.columns.str.strip().str.lower()

    # Ensure 'datetime' and 'datum_startuur' are in the same timezone
    #belpex_data['datetime'] = pd.to_datetime(belpex_data['datetime']).dt.tz_localize(None)
    #load_profile['datum_startuur'] = pd.to_datetime(load_profile['datum_startuur'])

    # Calculate the power difference
    #power_difference_data = calculate_power_difference(data)
    #power_difference_data['power_difference_kwh'] = power_difference_data['power_difference_kwh'].clip(lower=0)
    ## Resample power_difference_data to hourly intervals
    #power_difference_data['datetime'] = pd.to_datetime(power_difference_data['datetime'])
    #power_difference_data.set_index('datetime', inplace=True)
    #hourly_power_difference = power_difference_data.resample('H').sum().reset_index()

    # Debug: Print the dtypes of datetime columns
    #print("Debug: Belpex Data DateTime dtype:", belpex_data['datetime'].dtype)
    #print("Debug: Hourly Power Difference DateTime dtype:", hourly_power_difference['datetime'].dtype)

    # Merge the hourly power difference data with the Belpex data
    


    # Group data by day
    data['day'] = data['datetime'].dt.date
    data['residual_load'] = data['Volume_Afname_kWh'] - data['Power_Output_kWh']
    data['residual_load'] = data['residual_load'].clip(lower=0)

    grouped = data.groupby('day')

    charge_schedule = {}
    end_of_day_charge_levels = []  # List to store the charge level at the end of each day

    # Process each day
    days = list(grouped.groups.keys())  # Get the list of all days
    for i, day in enumerate(days):
        group = grouped.get_group(day)

        # Calculate the charging capacity for the day based on the residual load of the next day
        if i + 1 < len(days):  # Check if there is a next day
            next_day = days[i + 1]
            next_day_group = grouped.get_group(next_day)
            temp_capacity = next_day_group['residual_load'].sum()
        else:
            temp_capacity = 0  # No next day, so set capacity to 0

        # Reset the battery charge at the start of each day
        current_charge = 0  # Reset the current charge of the battery

        # Sort by price (cheapest to most expensive)
        sorted_group = group.sort_values(by='Euro')

        charge_hours = []
        charge_power = []  # List to store the power charged during each hour

        # Iterate through the sorted hours
        for _, row in sorted_group.iterrows():
            hour = row['datetime'].hour
            power_difference1 = row['power_difference_kwh']

            # Only add the hour if power_difference is not 0
            if power_difference1 != 0:
                # Add power difference to the total and update current charge
                current_charge += power_difference1
                if current_charge > temp_capacity:
                    # Adjust the last charged power to avoid exceeding capacity
                    power_difference1 -= (current_charge - temp_capacity)
                    current_charge = temp_capacity

                charge_hours.append(hour)
                charge_power.append(power_difference1)  # Track the power charged during this hour

                # Stop charging if the battery is full
                if current_charge >= temp_capacity:
                    break

        # Ensure the hours and power are sorted in chronological order
        sorted_indices = sorted(range(len(charge_hours)), key=lambda i: charge_hours[i])
        charge_hours = [charge_hours[i] for i in sorted_indices]
        charge_power = [charge_power[i] for i in sorted_indices]

        # Calculate the charge levels as a cumulative sum of charge_power
        charge_levels = []
        current_charge = 0
        for power in charge_power:
            current_charge += power
            if current_charge > temp_capacity:
                current_charge = temp_capacity
            charge_levels.append(current_charge)

        # Store the sorted and calculated data in the charge_schedule
        charge_schedule[day] = {
            'hours': charge_hours,
            'power': charge_power,
            'current_charge': charge_levels
        }

        # Append the charge level at the end of the day
        end_of_day_charge_levels.append({'Day': day, 'End of Day Charge Level (kWh)': current_charge})

    # Create a DataFrame for the charge schedule, including charge power and charge level
    charge_schedule_df = pd.DataFrame([
        {
            'datetime': 0,
            'Day': day,
            'Hour': hour,
            'Minute': 0,
            'Charge Power (kWh)': charge_schedule[day]['power'][i],
            'Charge Level (kWh)': charge_schedule[day]['current_charge'][i]
        }
        for day in charge_schedule
        for i, hour in enumerate(charge_schedule[day]['hours'])
    ])

    # Change charge_schedule_df to match the format of the original data
    charge_schedule_df['Minute'] = charge_schedule_df.groupby(['Day', 'Hour']).cumcount() * 15
    charge_schedule_df['datetime'] = pd.to_datetime(
        charge_schedule_df['Day'].astype(str) + ' ' +
        charge_schedule_df['Hour'].astype(str) + ':' +
        charge_schedule_df['Minute'].astype(str).str.zfill(2) + ':00'
    )
    #charge_schedule_df.set_index('datetime', inplace=True)
    charge_schedule_df.drop(columns=['Day', 'Hour', 'Minute'], inplace=True)

    # Save the charge_schedule DataFrame to an Excel file
    charge_schedule_df.to_excel('results/charge_schedule.xlsx', index=False)

    # Make sure datetime is in the same timezone as the original data
    charge_schedule_df['datetime'] = charge_schedule_df['datetime'].dt.tz_localize("Europe/Brussels", ambiguous="NaT", nonexistent="NaT")

    # Merge data with charge_schedule_df to include the original data columns
    merged_data = pd.merge(data, charge_schedule_df, on='datetime', how='left', suffixes=('', '_charge'))
    merged_data['Charge Power (kWh)'] = merged_data['Charge Power (kWh)'].fillna(0)
    merged_data['Charge Level (kWh)'] = merged_data['Charge Level (kWh)'].fillna(0)
    merged_data.drop(columns=['day', 'power_difference_kwh'], inplace=True)

    battery_charge = pd.DataFrame()
    battery_charge['datetime'] = merged_data['datetime']
    battery_charge['charge_power'] = merged_data['Charge Power (kWh)']
    battery_charge['charge_level'] = merged_data['Charge Level (kWh)']

    # Create a DataFrame for the end-of-day charge levels
    end_of_day_charge_df = pd.DataFrame(end_of_day_charge_levels)

    # Save the end-of-day charge levels to an Excel file
    end_of_day_charge_df.to_excel('results/end_of_day_charge_levels.xlsx', index=False)

    # Print the list of end-of-day charge levels
    #print(end_of_day_charge_levels)
    '''''
    # Prepare data for the heatmap
    days = sorted(charge_schedule.keys())  # Sorted list of days
    hours = range(24)  # Hours of the day (0-23)
    heatmap_data = np.zeros((len(days), len(hours)))  # Initialize a 2D array

    # Populate the heatmap data
    for i, day in enumerate(days):
        for hour in charge_schedule[day]['hours']:
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
    '''
    # Save the plot as an image
    #plt.savefig('results/charging_hours_heatmap.png')
    #plt.show()

    ## Prepare data for the plot
    #charging_data = []
#
    ## Loop through the charge_schedule to filter power_output data
    #for day, hours in charge_schedule.items():
    #    for hour in hours:
    #        # Calculate the charging datetime
    #        charging_datetime = pd.Timestamp(day) + pd.Timedelta(hours=hour)
    #        matching_row = data[data['datetime'] == charging_datetime]
    #        
    #        # Debug: Print the datetime and whether a match was found
    #        print(f"Checking datetime: {charging_datetime}")
    #        print(f"Matching rows: {len(matching_row)}")
    #        
    #        if not matching_row.empty:
    #            charging_data.append(matching_row)
#
    ## Combine all the filtered rows into a single DataFrame
    #charging_data = pd.concat(charging_data)
#
    ## Plot the charging power output
    #plt.figure(figsize=(12, 6))
    #plt.plot(charging_data['datetime'], charging_data['power_output_kwh'], label='Charging Power Output', color='blue')
    #plt.xlabel('Datetime')
    #plt.ylabel('Power Output (kWh)')
    #plt.title('Battery Charging Power Output Over the Year')
    #plt.grid(True)
    #plt.legend()
    #plt.tight_layout()
#
    ## Save the plot as an image
    #plt.savefig('results/charging_power_output_plot.png')
    #plt.show()
    data = pd.DataFrame(data)
    return charge_schedule_df, data, end_of_day_charge_levels, battery_charge



def smart_battery_merge(battery_charge, discharge_schedule):
    # Update 'charge_power' in smart_battery based on discharge_schedule
    smart_battery = pd.DataFrame
    if not discharge_schedule.empty:
        smart_battery = pd.merge(
            battery_charge[['datetime', 'charge_power']],
            discharge_schedule[['datetime', 'discharge_power']],
            on='datetime',
            how='left'
        )
        # If discharge_power is not NaN, set charge_power to -1 * discharge_power
        smart_battery['charge_power'] = smart_battery.apply(
            lambda row: -1 * row['discharge_power'] if row['discharge_power'] != 0 else row['charge_power'],
            axis=1
        )
        # Drop the 'discharge_power' column as it's no longer needed
        smart_battery.drop(columns=['discharge_power'], inplace=True)

    # Debug: Print the updated DataFrame
    # print(smart_battery.head())

    smart_battery['datetime'] = pd.to_datetime(smart_battery['datetime']).dt.tz_localize(None)
    smart_battery.to_excel('results/smart_battery_schedule.xlsx', index=False)

    # Load Excel data
    df = smart_battery.copy()

    # Extract relevant time info
    df['date'] = df['datetime'].dt.date  # Extract the date for the y-axis
    df['time'] = df['datetime'].dt.time  # Extract the time for the x-axis

    # Create heatmap matrix (date vs. time)
    heatmap_data = df.pivot_table(
        index='date',  # Rows represent dates
        columns='time',  # Columns represent times
        values='charge_power',
        aggfunc='mean'
    ).fillna(0)

    # Plot heatmap
    plt.figure(figsize=(18, 8))
    ax = sns.heatmap(
        heatmap_data,
        cmap="BrBG",  # Diverging colormap: green for positive, blue for negative
        center=0,  # Center the colormap at 0
        cbar_kws={'label': 'Charge Power (kW)'},
        xticklabels=8,  # Show every 8th time label
        yticklabels=30  # Show every 30th date label
    )
    
    # Set title and axis labels with larger font sizes
    plt.title("Smart Battery Charging/Discharging Heatmap (Year Overview)", fontsize=18)
    plt.xlabel("Time of Day", fontsize=16)
    plt.ylabel("Date", fontsize=16)
    plt.xticks(fontsize=14, rotation=45)
    plt.yticks(fontsize=14)

    # Adjust colorbar font size
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(labelsize=14)  # Set font size for colorbar ticks

    plt.tight_layout()
    plt.savefig('results/smart_battery_heatmap.png')
    plt.show()

    # Zoomed-in week view (e.g., May 30 to June 5, 2000)
    week_data = df[(df['datetime'] >= pd.Timestamp('2000-05-30')) & (df['datetime'] < pd.Timestamp('2000-06-06'))]

    plt.figure(figsize=(16, 6))
    plt.plot(week_data['datetime'], week_data['charge_power'], color='teal', linewidth=1)
    plt.axhline(0, color='black', linestyle='--', linewidth=0.8)
    plt.title("Smart Battery Charging/Discharging – Week View (May 30 to June 5)")
    plt.ylabel("Charge Power (kW)")
    plt.xlabel("Datetime")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('results/smart_battery_week_view.png')
    plt.show()

        # Extract month
    df['month'] = df['datetime'].dt.month

    # Separate charge and discharge values
    df['charged'] = df['charge_power'].clip(lower=0)  # Only positive values (charging)
    df['discharged'] = -df['charge_power'].clip(upper=0)  # Negative values flipped positive (discharging)

    # Monthly summary
    monthly_summary = df.groupby('month')[['charged', 'discharged']].sum()

    # Plot
    plt.figure(figsize=(10, 6))
    monthly_summary.plot(kind='bar', stacked=False, color=['green', 'blue'])
    plt.title("Monthly Energy Charged and Discharged by Smart Battery")
    plt.xlabel("Month")
    plt.ylabel("Energy (kWh)")
    plt.xticks(
        ticks=range(0, 12),
        labels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        rotation=45
    )
    plt.legend(["Charged", "Discharged"])
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('results/smart_battery_monthly_summary.png')
    plt.show()

    return smart_battery