import pandas as pd

def conventional_battery(battery_capacity, data):
    data = data.copy()  # Create a copy of the input DataFrame to avoid modifying the original
    """
    Simulates the charging and discharging of a battery based on power surplus and deficit.

    Parameters:
        battery_capacity (float): Maximum capacity of the battery in kWh.
        data (DataFrame): DataFrame containing hourly power data with columns:
                          - 'datetime': Timestamp of the hour
                          - 'power_difference_kwh': Surplus (+) or deficit (-) of power in kWh

    Returns:
        charge_schedule (list): List of dictionaries with charging details.
        discharge_schedule (list): List of dictionaries with discharging details.
    """
    # Initialize variables
    current_charge = 0  # Current charge level of the battery
    charge_amount = 0  # Amount of power charged during the hour
    discharge_amount = 0  # Amount of power discharged during the hour
    charge_schedule = []  # To store charging details
    discharge_schedule = []  # To store discharging details
    charge_discharge_schedule = []  # To store charge/discharge schedule

    # Iterate through each hour in the data
    for _, row in data.iterrows():
        hour = row['datetime']
        power_difference = row['power_difference_kwh_for_conventional']

        if power_difference > 0:
            # Surplus of power: Charge the battery
            charge_amount = min(power_difference, battery_capacity - current_charge)
            current_charge += charge_amount
            discharge_amount = 0  # Reset discharge amount
            
            
        elif power_difference < 0:
            # Deficit of power: Discharge the battery
            discharge_amount = min(abs(power_difference), current_charge)
            current_charge -= discharge_amount
            charge_amount = 0
        discharge_schedule.append({
                'hour': hour,
                'discharge_power': discharge_amount,
                'current_charge': current_charge
        })
        charge_schedule.append({
                'hour': hour,
                'charge_power': charge_amount,
                'current_charge': current_charge
            })
        charge_discharge_schedule.append({
                'hour': hour,
                'charge_power': charge_amount-discharge_amount,
                'current_charge': current_charge
            })

    convention_charge_schedule_df = pd.DataFrame(charge_schedule)
    convention_discharge_schedule_df = pd.DataFrame(discharge_schedule)
    convention_charge_discharge_schedule_df = pd.DataFrame(charge_discharge_schedule)

    # Remove timezone information from datetime columns
    if 'hour' in convention_charge_schedule_df.columns:
        convention_charge_schedule_df['hour'] = pd.to_datetime(convention_charge_schedule_df['hour']).dt.tz_localize(None)
    if 'hour' in convention_discharge_schedule_df.columns:
        convention_discharge_schedule_df['hour'] = pd.to_datetime(convention_discharge_schedule_df['hour']).dt.tz_localize(None)
    if 'hour' in convention_charge_discharge_schedule_df.columns:
        convention_charge_discharge_schedule_df['hour'] = pd.to_datetime(convention_charge_discharge_schedule_df['hour']).dt.tz_localize(None)

    # Save the conventional charge and discharge schedules to Excel
    with pd.ExcelWriter('results/conventional_battery_schedules.xlsx') as writer:
        convention_charge_schedule_df.to_excel(writer, sheet_name='Charge Schedule', index=False)
        convention_discharge_schedule_df.to_excel(writer, sheet_name='Discharge Schedule', index=False)
        convention_charge_discharge_schedule_df.to_excel(writer, sheet_name='Charge Discharge Schedule', index=False)
        return convention_charge_schedule_df, convention_discharge_schedule_df, convention_charge_discharge_schedule_df
