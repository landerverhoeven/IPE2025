from datetime import datetime, time, timedelta
import pandas as pd

def charge_ev_weekly(data, battery_capacity, max_charge_percent=100):
    """
    Models an EV battery charging process for all weeks in the dataset.
    At the start of each week, the battery is fully charged, and the charge level decreases
    by 8 kWh between 8 AM and 6 PM every day of the week.

    Args:
        data (pd.DataFrame): DataFrame containing 'datetime' for each time interval.
        battery_capacity (float): Maximum capacity of the battery (kWh).
        max_charge_percent (float): Maximum charge level as a percentage of battery capacity.

    Returns:
        pd.DataFrame: DataFrame containing the updated charge levels for all weeks.
    """
    max_charge = battery_capacity * (max_charge_percent / 100)
    results = []

    # Sort data by datetime
    data = data.sort_values(by='datetime')  # Ensure data is sorted by datetime

    # Initialize the starting charge level
    start_of_week = data['datetime'].iloc[0]
    while start_of_week < data['datetime'].iloc[-1]:
        end_of_week = start_of_week + timedelta(days=7)

        # Filter data for the current week
        weekly_data = data[(data['datetime'] >= start_of_week) & (data['datetime'] < end_of_week)]

        # Start the week with a fully charged battery
        current_charge = max_charge

        # Process the weekly data
        for _, entry in weekly_data.iterrows():
            dt = entry['datetime']

            # Debugging: Print the current datetime and charge level
            print(f"Processing datetime: {dt}, Current charge: {current_charge}")

            # Simulate daily driving (8 kWh between 8 AM and 6 PM)
            if time(8, 0) <= dt.time() <= time(18, 0):
                print(f"Discharging at {dt} (8 AM - 6 PM)")
                current_charge -= 8 / (10 * 4)  # Spread 8 kWh over 10 hours (15-min intervals)
                current_charge = max(current_charge, 0)  # Ensure charge does not go below 0

            # Append the results for this time interval
            results.append({
                "datetime": dt,
                "updated_charge": current_charge
            })

        # Move to the next week
        start_of_week = end_of_week

    # Convert the results list to a pandas DataFrame
    results_df = pd.DataFrame(results)

    # Save the DataFrame to an Excel file
    results_df['datetime'] = pd.to_datetime(results_df['datetime']).dt.tz_localize(None)  # Remove timezone info
    results_df.to_excel('results/ev_charge_schedule_weekly_discharge.xlsx', index=False)
    print(f"Charge schedule saved to {'results/ev_charge_schedule_weekly_discharge.xlsx'}")

    return results_df