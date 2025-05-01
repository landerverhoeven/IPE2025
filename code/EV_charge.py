from datetime import datetime, time, timedelta
import pandas as pd

def charge_ev_weekly(data, battery_capacity, min_charge_percent=30, max_charge_percent=100, max_charging_rate=2.3):
    """
    Models an EV battery charging process for all weeks in the dataset with restrictions and dynamic charging rates.

    Args:
        data (pd.DataFrame): DataFrame containing 'datetime', 'price', and 'power_surplus' for each time interval.
        battery_capacity (float): Maximum capacity of the battery (kWh).
        min_charge_percent (float): Minimum charge level as a percentage of battery capacity.
        max_charge_percent (float): Maximum charge level as a percentage of battery capacity.
        max_charging_rate (float): Maximum charging rate (kW).

    Returns:
        pd.DataFrame: DataFrame containing the charging schedule and updated charge levels for all weeks.
    """
    min_charge = battery_capacity * (min_charge_percent / 100)
    max_charge = battery_capacity * (max_charge_percent / 100)
    results = []

    # Sort data by datetime
    data = data.sort_values(by='datetime')  # Ensure data is sorted by datetime

    # Initialize the starting charge level
    current_charge = max_charge  # Start with a full battery

    # First iteration: Use only power surplus
    start_of_week = data['datetime'].iloc[0]
    while start_of_week < data['datetime'].iloc[-1]:
        end_of_week = start_of_week + timedelta(days=7)

        # Filter data for the current week
        weekly_data = data[(data['datetime'] >= start_of_week) & (data['datetime'] < end_of_week)]
        weekly_data = weekly_data.sort_values(by='ev_price')  # Sort by EV electricity price (cheapest first)

        # Process the weekly data (power surplus only)
        for _, entry in weekly_data.iterrows():
            dt = entry['datetime']
            price = entry['ev_price']
            power_surplus = entry['power_difference_kwh']
            weekday = dt.weekday()
            is_weekend = weekday >= 5

            # Define charging availability
            weekday_start = time(18, 0)  # 6 PM
            weekday_end = time(8, 0)    # 8 AM
            weekend_start = time(8, 0)  # 8 AM
            weekend_end = time(18, 0)   # 6 PM

            # Determine if charging is allowed
            charging_allowed = False
            if is_weekend:
                charging_allowed = True
            elif weekday_start <= dt.time() or dt.time() <= weekday_end:
                charging_allowed = True

            # Simulate weekday driving (8 kWh per day)
            if not is_weekend and weekend_end >= dt.time() >= weekend_start:
                current_charge -= 8 / (10 * 4)  # Spread 8 kWh over 10 hours (15-min intervals)
                current_charge = max(current_charge, min_charge)  # Ensure minimum charge is maintained

            # Simulate weekend driving (20% of battery capacity)
            if is_weekend and weekend_start <= dt.time() <= weekend_end:
                current_charge -= battery_capacity * 0.2 / (10 * 4)  # Spread 20% over 10 hours (15-min intervals)
                current_charge = max(current_charge, min_charge)  # Ensure minimum charge is maintained

            # Charge the battery using power surplus only
            charging_power = 0
            if charging_allowed and current_charge < max_charge and power_surplus > 0:
                charge_needed = max_charge - current_charge
                charging_power = min(charge_needed, max_charging_rate * 0.25, power_surplus)  # Use solar surplus
                current_charge += charging_power
                current_charge = min(current_charge, max_charge)  # Ensure max charge is not exceeded

            # Append the results for this time interval
            results.append({
                "datetime": dt,
                "price": price,
                "power_surplus": power_surplus,
                "charging_power": charging_power,
                "updated_charge": current_charge
            })

        # Move to the next week
        start_of_week = end_of_week

    # Second iteration: Use grid power if needed
    for entry in results:
        if entry['charging_power'] == 0 and entry['updated_charge'] < max_charge:
            charge_needed = max_charge - entry['updated_charge']
            charging_power = min(charge_needed, max_charging_rate * 0.25)
            entry['charging_power'] += charging_power
            entry['updated_charge'] += charging_power
            entry['updated_charge'] = min(entry['updated_charge'], max_charge)

    # Ensure the results are sorted chronologically by datetime
    results = sorted(results, key=lambda x: x['datetime'])

    # Convert the results list to a pandas DataFrame
    results_df = pd.DataFrame(results)

    # Save the DataFrame to an Excel file
    results_df['datetime'] = pd.to_datetime(results_df['datetime']).dt.tz_localize(None)  # Remove timezone info
    results_df.to_excel('results/ev_charge_schedule_all_weeks.xlsx', index=False)
    print(f"Charge schedule saved to {'results/ev_charge_schedule_all_weeks.xlsx'}")

    return results_df


'''
RESTRICTIONS: 
- EV charging is allowed only during the night (from 6 PM to 8 AM) on weekdays and all day on weekends.
- The EV battery must maintain a minimum charge level for emergency use. (e.g., 30% of the battery capacity). Give explaination why this number is chosen
- The EV battery cannot exceed its maximum charge level (e.g., 100% of the battery capacity).
- on weekends take away a certain amount from the battery to simulate driving, e.g., 20% of the battery capacity. spread over the 8am to 6pm.
- Assume the car drives 40 km per day and consumes 20 kWh/100 km. This means the car consumes 8 kWh per day. This is removed from the battery during the day.
- The car is charged during blocks of 1 week when the price is cheapest during this week
- max charging rate is 2,3 kW
- At the end of the week, the battery should be charged to its maximum charge level.
- First the car is charged using the power surplus of the solar panels, then the rest is charged using the grid.
-make an extra column in data with the price of electricity for the EV, meaning that the power surplus from the solar panels is free and the rest is charged using the grid.


'''