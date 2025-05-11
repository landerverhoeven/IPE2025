from datetime import datetime, time, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def charge_ev_weekly(data, battery_capacity, charge_battery_schedule, max_charge_percent=100, max_charge_rate=2.3, drive_discharge=8):
    """
    Models an EV battery charging process for all weeks in the dataset.
    The battery discharges during daily driving (8 kWh between 8 AM and 6 PM) and charges
    during the cheapest possible time between 6 PM and 8 AM on weekdays and the entire day on weekends,
    excluding hours when the battery is charging.

    Args:
        data (pd.DataFrame): DataFrame containing 'datetime', 'price', and 'power_surplus' for each time interval.
        battery_capacity (float): Maximum capacity of the battery (kWh).
        charge_battery_schedule (pd.DataFrame): DataFrame containing the battery charge schedule with 'datetime' column.
        max_charge_percent (float): Maximum charge level as a percentage of battery capacity.
        max_charge_rate (float): Maximum charging rate in kW.
        drive_discharge (float): Daily discharge in kWh.

    Returns:
        pd.DataFrame: DataFrame containing the updated charge levels for all weeks.
    """
    max_charge = battery_capacity * (max_charge_percent / 100)
    max_charge_per_interval = max_charge_rate / 4  # Maximum charge rate per 15-minute interval
    results = []

    # Sort data by datetime for the discharging simulation
    data = data.sort_values(by='datetime')  # Ensure data is sorted by datetime

    # Exclude overlapping hours from the EV charging schedule
    charge_battery_hours = charge_battery_schedule['datetime']

    # Initialize the starting charge level
    current_charge = max_charge
    current_day = None  # Track the current day
    current_week = None  # Track the current week
    daily_discharge_remaining = 0  # Initialize daily discharge remaining

    # First iteration: Simulate driving (discharge)
    for _, entry in data.iterrows():
        dt = entry['datetime']

        # Reset weekly charge at the start of a new week
        if current_week != dt.isocalendar()[1]:  # Check if the week number has changed
            current_week = dt.isocalendar()[1]
            current_charge = max_charge  # Reset charge to max at the start of a new week

        # Reset daily discharge at the start of a new day
        if current_day != dt.date():
            current_day = dt.date()
            daily_discharge_remaining = drive_discharge  # Reset daily discharge to 8 kWh at the start of each day

        # Simulate daily driving (8 kWh between 8 AM and 6 PM)
        if time(8, 0) <= dt.time() <= time(18, 0):  # Applies to all days (weekdays and weekends)
            discharge_amount = min(drive_discharge / (10 * 4), daily_discharge_remaining)  # Spread 8 kWh over 10 hours (15-min intervals)
            current_charge -= discharge_amount
            current_charge = max(current_charge, 0)  # Ensure charge does not go below 0
            daily_discharge_remaining -= discharge_amount  # Reduce the daily discharge remaining

        # Append the results for this time interval (discharge only)
        results.append({
            "datetime": dt,
            "price": entry['Euro'],
            "power_surplus": entry['power_difference_kwh'],
            "charge_power": 0,  # No charging during this iteration
            "discharge_charge": current_charge  # Preserve the charge after discharging            
            })

    # Convert the results list to a DataFrame for charging simulation
    results_df = pd.DataFrame(results)

    # Second iteration: Simulate charging (using power surplus)
    results_df = results_df.sort_values(by='price')  # Sort by price for charging
    for _, row in results_df.iterrows():
        dt = row['datetime']
        price = row['price']
        power_surplus = row['power_surplus']
        charge_power = 0
        weekday = dt.weekday()
        is_weekend = weekday >= 5  # Saturday and Sunday are weekends

        # Skip hours where the battery is charging
        if dt in charge_battery_hours.values:
            continue

        # Charging allowed: 6 PM to 8 AM on weekdays or the entire day on weekends
        if (is_weekend or dt.time() >= time(18, 0) or dt.time() <= time(8, 0)):
            charge_needed = max_charge - results_df.loc[row.name, 'discharge_charge']
            if power_surplus > 0:
                # Use power surplus to charge as much as possible, limited by max charge rate per interval
                charge_power = min(charge_needed, power_surplus, max_charge_per_interval)

        # Update the charging power in the results DataFrame
        results_df.loc[row.name, 'charge_power'] = charge_power

    # Recalculate updated_charge in chronological order
    results_df = results_df.sort_values(by='datetime')  # Return to chronological order
    current_week = None  # Reset current week for recalculation
    for i, row in results_df.iterrows():
        dt = row['datetime']

        # Reset cumulative charging power at the start of a new week
        if current_week != dt.isocalendar()[1]:  # Check if the week number has changed
            current_week = dt.isocalendar()[1]
            cumulative_charge_power = 0  # Reset cumulative charging power

        # Calculate updated_charge as discharge_charge + cumulative charging power
        cumulative_charge_power += row['charge_power']
        updated_charge = row['discharge_charge'] + cumulative_charge_power

        # If updated_charge exceeds max_charge, adjust the charge_power in the current row
        if updated_charge > max_charge:
            excess = updated_charge - max_charge
            # Ensure charge_power does not go below 0
            adjusted_charge_power = max(0, row['charge_power'] - excess)
            results_df.loc[i, 'charge_power'] = adjusted_charge_power
            updated_charge = row['discharge_charge'] + cumulative_charge_power - (row['charge_power'] - adjusted_charge_power)

        # Update the updated_charge in the DataFrame
        results_df.loc[i, 'updated_charge'] = updated_charge
    '''
    # Third iteration: Simulate grid charging for each week
    results_df['week'] = results_df['datetime'].dt.isocalendar().week  # Add a column for the week number
    results_df['day'] = results_df['datetime'].dt.date  # Add a column for the day

    for week, week_data in results_df.groupby('week'):
        # Calculate the total discharge for the week (8 kWh per day)
        num_days_in_week = week_data['day'].nunique()  # Count unique days in the week
        total_discharge = 8 * num_days_in_week  # Total discharge for the week

        # Calculate the total charging power for the week
        total_charge_power = week_data['charge_power'].sum() + week_data['grid_charge_power'].sum()

        # Calculate the grid charge needed for the week
        grid_charge_needed = total_discharge - total_charge_power

        # Sort the week data by price for grid charging
        week_data = week_data.sort_values(by='price')

        for i, row in week_data.iterrows():
            dt = row['datetime']
            price = row['price']
            charge_power = row['charge_power']
            grid_charge_power = 0
            weekday = dt.weekday()
            is_weekend = weekday >= 5  # Saturday and Sunday are weekends

            # Charging allowed: 6 PM to 8 AM on weekdays or the entire day on weekends
            if grid_charge_needed > 0 and (is_weekend or dt.time() >= time(18, 0) or dt.time() <= time(8, 0)):
                                    # Determine the maximum grid charging power allowed
                    max_grid_charge_power = max_charge_per_interval - charge_power
                    grid_charge_power = min(grid_charge_needed, max_grid_charge_power)
                    grid_charge_power = max(0, grid_charge_power)  # Ensure it does not go below 0

                    # Update grid_charge_needed and grid_charge_power
                    grid_charge_needed -= grid_charge_power
                    results_df.loc[row.name, 'grid_charge_power'] = grid_charge_power

        # Verify that the total grid charging power matches the weekly difference
        total_grid_charge_power = week_data['grid_charge_power'].sum()
        if not abs(total_grid_charge_power - (total_discharge - total_charge_power)) < 1e-6:
            print(f"Warning: Grid charging power mismatch in week {week}.")

    # Update cumulative charging power to include grid charging
    results_df['cumulative_charge_power'] = results_df['charge_power'] + results_df['grid_charge_power']
    '''
    '''
    # Third iteration: Simulate grid charging for each week
    results_df['week'] = results_df['datetime'].dt.isocalendar().week  # Add a column for the week number
    results_df['day'] = results_df['datetime'].dt.date  # Add a column for the day

    for week, week_data in results_df.groupby('week'):
        # Calculate the total discharge for the week (8 kWh per day)
        num_days_in_week = week_data['day'].nunique()  # Count unique days in the week
        total_discharge = 8 * num_days_in_week  # Total discharge for the week

        # Calculate the total charging power for the week
        total_charging_power = week_data['charging_power'].sum() + week_data['grid_charging_power'].sum()

        # Calculate the grid charge needed for the week
        grid_charge_needed = total_discharge - total_charging_power

        # Sort the week data by price for grid charging
        week_data = week_data.sort_values(by='price')

        for i, row in week_data.iterrows():
            dt = row['datetime']
            price = row['price']
            charging_power = row['charging_power']
            grid_charging_power = 0
            weekday = dt.weekday()
            is_weekend = weekday >= 5  # Saturday and Sunday are weekends

            # Charging allowed: 6 PM to 8 AM on weekdays or the entire day on weekends
            if grid_charge_needed > 0 and (is_weekend or dt.time() >= time(18, 0) or dt.time() <= time(8, 0)):
                                    # Determine the maximum grid charging power allowed
                    max_grid_charging_power = max_charge_per_interval - charging_power
                    grid_charging_power = min(grid_charge_needed, max_grid_charging_power)
                    grid_charging_power = max(0, grid_charging_power)  # Ensure it does not go below 0

                    # Update grid_charge_needed and grid_charging_power
                    grid_charge_needed -= grid_charging_power
                    results_df.loc[row.name, 'grid_charging_power'] = grid_charging_power

        # Verify that the total grid charging power matches the weekly difference
        total_grid_charging_power = week_data['grid_charging_power'].sum()
        if not abs(total_grid_charging_power - (total_discharge - total_charging_power)) < 1e-6:
            print(f"Warning: Grid charging power mismatch in week {week}.")

    # Update cumulative charging power to include grid charging
    results_df['cumulative_charging_power'] = results_df['charging_power'] + results_df['grid_charging_power']
    '''
    # Ensure the final result is ordered chronologically
    results_df = results_df.sort_values(by='datetime')  # Sort by datetime

    # Save the DataFrame to an Excel file
    results_df['datetime'] = pd.to_datetime(results_df['datetime']).dt.tz_localize(None)  # Remove timezone info
    results_df.to_excel('results/ev_charge_schedule_with_charging.xlsx', index=False)
    print(f"Charge schedule saved to {'results/ev_charge_schedule_with_charging.xlsx'}")

        # Load data
    df = results_df.copy()

    # Convert datetime column to pandas datetime type
    df['datetime'] = pd.to_datetime(df['datetime'])

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
    plt.title("EV Battery Charging Heatmap (Year Overview)", fontsize=18)
    plt.xlabel("Time of Day", fontsize=16)
    plt.ylabel("Date", fontsize=16)
    plt.xticks(fontsize=14, rotation=45)
    plt.yticks(fontsize=14)

    # Adjust colorbar font size
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(labelsize=14)  # Set font size for colorbar ticks

    plt.tight_layout()
    plt.savefig('results/EV_battery_heatmap.png')
    plt.show()

    '''
    # ---- 2️⃣ Average Daily Charging Profile ----
    avg_daily_profile = df.groupby('time_of_day')['charge_power'].mean()

    plt.figure(figsize=(18, 6))
    avg_daily_profile.plot(kind='line', color='teal')
    plt.title('Average Daily EV Charging Profile', fontsize=18)
    plt.xlabel('Time of Day')
    plt.ylabel('Average Charge Power (kW)')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


    # ---- 3️⃣ Full Time Series (Daily Average) ----
    daily_avg_power = df.set_index('datetime')['charge_power'].resample('D').mean()

    plt.figure(figsize=(20, 6))
    daily_avg_power.plot(kind='line', color='purple')
    plt.title('Daily Average EV Charging Power Over the Year', fontsize=18)
    plt.xlabel('Date')
    plt.ylabel('Average Charge Power (kW)')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()


    # ---- 4️⃣ Filled Area Chart (Full Year) ----
    plt.figure(figsize=(20, 6))
    df.set_index('datetime')['charge_power'].plot(kind='area', color='skyblue', alpha=0.6)
    plt.title('EV Charging Power Over the Year (Area Chart)', fontsize=18)
    plt.xlabel('Date')
    plt.ylabel('Charge Power (kW)')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()
    '''
    return results_df