from datetime import datetime, time, timedelta
import pandas as pd

def charge_ev_weekly(data, battery_capacity, max_charge_percent=100, max_charge_rate=2.3, drive_discharge=8):
    """
    Models an EV battery charging process for all weeks in the dataset.
    The battery discharges during daily driving (8 kWh between 8 AM and 6 PM) and charges
    during the cheapest possible time between 6 PM and 8 AM on weekdays and the entire day on weekends.

    Args:
        data (pd.DataFrame): DataFrame containing 'datetime', 'price', and 'power_surplus' for each time interval.
        battery_capacity (float): Maximum capacity of the battery (kWh).
        max_charge_percent (float): Maximum charge level as a percentage of battery capacity.

    Returns:
        pd.DataFrame: DataFrame containing the updated charge levels for all weeks.
    """
    max_charge = battery_capacity * (max_charge_percent / 100)
    results = []

    # Sort data by datetime for the discharging simulation
    data = data.sort_values(by='datetime')  # Ensure data is sorted by datetime

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
            "charging_power": 0,  # No charging during this iteration
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
        charging_power = 0
        weekday = dt.weekday()
        is_weekend = weekday >= 5  # Saturday and Sunday are weekends

        # Charging allowed: 6 PM to 8 AM on weekdays or the entire day on weekends
        if (is_weekend or dt.time() >= time(18, 0) or dt.time() <= time(8, 0)):
            charge_needed = max_charge - results_df.loc[row.name, 'discharge_charge']
            if power_surplus > 0:
                # Use power surplus to charge as much as possible
                charging_power = min(charge_needed, power_surplus)

                    # Update the charging power in the results DataFrame
        results_df.loc[row.name, 'charging_power'] = charging_power

    # Recalculate updated_charge in chronological order
    results_df = results_df.sort_values(by='datetime')  # Return to chronological order
    for i, row in results_df.iterrows():
        # Calculate updated_charge as discharge_charge + charging_power
        updated_charge = row['discharge_charge'] + row['charging_power']
        if updated_charge > max_charge:
            updated_charge = max_charge  # Ensure updated_charge does not exceed max_charge
            charging_power = max_charge - row['discharge_charge']
        results_df.loc[row.name, 'charging_power'] = charging_power  # Update charging power in the DataFrame
        results_df.loc[row.name, 'updated_charge'] = updated_charge  # Ensure updated_charge does not exceed max_charge

    # Save the DataFrame to an Excel file
    results_df['datetime'] = pd.to_datetime(results_df['datetime']).dt.tz_localize(None)  # Remove timezone info
    results_df.to_excel('results/ev_charge_schedule_with_charging.xlsx', index=False)
    print(f"Charge schedule saved to {'results/ev_charge_schedule_with_charging.xlsx'}")

    return results_df