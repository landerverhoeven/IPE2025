from datetime import datetime, time

def charge_ev_daily(current_charge, max_charge, min_charge, power_diff, data):
    """
    Models an EV battery charging process for multiple days with dynamic charging rate based on power difference.
    !!!!CHARGING EVERY 3 DAYS MAYBE??
    Args:
        current_charge (float): Current charge level of the battery (kWh).
        max_charge (float): Maximum capacity of the battery (kWh).
        min_charge (float): Minimum charge level required for emergency use (kWh).
        power_diff (list): List of available power differences between PV generation and load (kW) for each day.
        data (list): List of datetime objects representing the days to simulate.

    Returns:
        list: List of dictionaries containing the ideal charging time and updated charge level for each day.
    """
    results = []

    for day, power in zip(data, power_diff):
        weekday = day.weekday()
        is_weekend = weekday >= 5

        # Define charging availability
        weekday_start = time(18, 0)  # 6 PM
        weekday_end = time(8, 0)    # 8 AM
        weekend_start = time(0, 0)  # Midnight
        weekend_end = time(23, 59)  # End of the day

        # Determine if charging is allowed
        if is_weekend:
            charging_allowed = True
        else:
            charging_allowed = False
            if day.time() >= weekday_start or day.time() <= weekday_end:
                charging_allowed = True

        # Ensure minimum charge is maintained
        if current_charge < min_charge:
            current_charge = min_charge

        # Calculate charging time and updated charge
        if charging_allowed and power > 0:  # Only charge if power_diff is positive
            charge_needed = max_charge - current_charge
            charging_time = charge_needed / power  # Use power_diff as the dynamic charging rate
            updated_charge = min(max_charge, current_charge + power * charging_time)
            result = {
                "date": day.strftime('%Y-%m-%d'),
                "ideal_charging_time": f"{day.strftime('%Y-%m-%d %H:%M:%S')}",
                "updated_charge": updated_charge
            }
        else:
            result = {
                "date": day.strftime('%Y-%m-%d'),
                "ideal_charging_time": "Charging not allowed at this time",
                "updated_charge": current_charge
            }

        results.append(result)

    return results


'''
RESTRICTIONS: 
- EV charging is allowed only during the night (from 6 PM to 8 AM) on weekdays and all day on weekends.
- The EV battery must maintain a minimum charge level for emergency use. (e.g., 30% of the battery capacity).
- The EV battery cannot exceed its maximum charge level (e.g., 100% of the battery capacity).
- The charging rate is dynamic and depends on the available power difference between PV generation and load.
- on weekends take away a certain amount from the battery to simulate driving, e.g., 20% of the battery capacity.

'''