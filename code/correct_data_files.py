import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from calculations_power import calculation_power_output

def correct_belpex_data(belpex_data):
    belpex_data = belpex_data.copy()  # Avoid SettingWithCopyWarning

    # Ensure the 'Date' column is in string format
    belpex_data['Date'] = belpex_data['Date'].astype(str)

    # Append '00:00' to rows where only the date is present (no time)
    belpex_data['Date'] = belpex_data['Date'].apply(lambda x: x if ':' in x else f"{x} 00:00")

    # Convert the 'Date' column to datetime format
    belpex_data['datetime'] = pd.to_datetime(belpex_data['Date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # Drop rows with invalid datetime values (NaT)
    belpex_data = belpex_data.dropna(subset=['datetime']).copy()

    # Drop rows where the date is February 29
    belpex_data = belpex_data[~((belpex_data['datetime'].dt.month == 2) & (belpex_data['datetime'].dt.day == 29))]

    # Convert the 'Euro' column to numeric and drop invalid rows
    belpex_data['Euro'] = pd.to_numeric(belpex_data['Euro'], errors='coerce')
    belpex_data = belpex_data.dropna(subset=['Euro']).copy()

    # Drop duplicate datetime values by aggregating numeric columns
    numeric_columns = belpex_data.select_dtypes(include='number').columns
    belpex_data = belpex_data.groupby('datetime', as_index=False)[numeric_columns].mean()

    # Resample to 15-minute intervals
    belpex_data = belpex_data.set_index('datetime').resample('15min').ffill().reset_index()

    # Change the year of belpex_data to 2000
    belpex_data['datetime'] = belpex_data['datetime'].apply(lambda x: x.replace(year=2000))

    # Add missing rows till 23:45:00
    last_row = belpex_data.iloc[-1]
    last_datetime = last_row['datetime']
    additional_rows = []
    for i in range(1, 4):
        new_datetime = last_datetime + pd.Timedelta(minutes=15 * i)
        new_row = last_row.copy()
        new_row['datetime'] = new_datetime
        additional_rows.append(new_row)
    belpex_data = pd.concat([belpex_data, pd.DataFrame(additional_rows)], ignore_index=True)

    return belpex_data[["datetime", "Euro"]]


def correct_load_profile(load_profile):
    load_profile = load_profile.copy()  # Avoid SettingWithCopyWarning

    # Ensure 'Datum_Startuur' is in datetime format
    load_profile['Datum_Startuur'] = pd.to_datetime(load_profile['Datum_Startuur'], errors='coerce')

    # Drop rows with invalid datetime values (NaT)
    load_profile = load_profile.dropna(subset=['Datum_Startuur']).copy()

    # Drop rows where the date is February 29
    load_profile = load_profile[~((load_profile['Datum_Startuur'].dt.month == 2) & (load_profile['Datum_Startuur'].dt.day == 29))]

    # Convert the 'Volume_Afname_kWh' column to numeric and drop invalid rows
    load_profile['Volume_Afname_kWh'] = pd.to_numeric(load_profile['Volume_Afname_kWh'], errors='coerce')
    load_profile = load_profile.dropna(subset=['Volume_Afname_kWh']).copy()

    # Change the year of 'Datum_Startuur' to 2000
    load_profile['Datum_Startuur'] = load_profile['Datum_Startuur'].apply(lambda x: x.replace(year=2000))

    # Identify periods with missing data
    missing_periods_load = load_profile[load_profile['Volume_Afname_kWh'].isna()]

    # Group by consecutive missing periods
    missing_periods_load['group'] = (missing_periods_load.index.to_series().diff() != pd.Timedelta('15min')).cumsum()

    for group_load, period_load in missing_periods_load.groupby('group'):
        start_date_load = period_load.index.min().normalize()
        end_date_load = period_load.index.max().normalize()

        # Calculate the number of days in the period
        num_days_load = (end_date_load - start_date_load).days + 1

        # Get the data for the days before and after the period
        before_period_load = load_profile.loc[start_date_load - pd.Timedelta(days=num_days_load):start_date_load - pd.Timedelta(minutes=15)]
        after_period_load = load_profile.loc[end_date_load + pd.Timedelta(minutes=15):end_date_load + pd.Timedelta(days=num_days_load)]

        # Calculate the total load for the days before and after the period
        before_load_load = before_period_load['Volume_Afname_kWh'].sum()
        after_load_load = after_period_load['Volume_Afname_kWh'].sum()

        # Fill the missing data with the data from the day with the lowest load
        if before_load_load < after_load_load:
            fill_data_load = before_period_load['Volume_Afname_kWh']
        else:
            fill_data_load = after_period_load['Volume_Afname_kWh']

        # Repeat the fill data to match the length of the missing period
        fill_data_load = fill_data_load.iloc[:len(period_load)].values

        # Fill the missing period with the fill data
        load_profile.loc[period_load.index, 'Volume_Afname_kWh'] = fill_data_load

    # Reset index to keep 'Datum_Startuur' as a column
    load_profile.reset_index(inplace=True)

    return load_profile[["Datum_Startuur", "Volume_Afname_kWh"]]


def correct_irradiance_data(WP_panel, N_module, tilt_module, azimuth_module, irradiance_data):
    irradiance_data = irradiance_data.copy()  # Avoid SettingWithCopyWarning

    # Ensure the 'DateTime' column is in datetime format
    irradiance_data['DateTime'] = pd.to_datetime(irradiance_data['DateTime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # Drop rows with invalid datetime values (NaT)
    irradiance_data = irradiance_data.dropna(subset=['DateTime']).copy()

    # Drop rows where the date is February 29
    irradiance_data = irradiance_data[~((irradiance_data['DateTime'].dt.month == 2) & (irradiance_data['DateTime'].dt.day == 29))]

    # Ensure numeric columns are properly formatted
    numeric_columns = ['GlobRad', 'DiffRad', 'T_RV_degC', 'T_CommRoof_degC']  # Replace with actual column names
    for col in numeric_columns:
        irradiance_data[col] = pd.to_numeric(irradiance_data[col], errors='coerce')

    # Initialize power_output as a DataFrame
    power_output = pd.DataFrame()

    power_output = calculation_power_output(WP_panel, N_module, tilt_module, azimuth_module, irradiance_data)
    # Resample to 15-minute intervals
    power_output = power_output.set_index('DateTime').resample('15min').sum().reset_index()

    # Change the year of load_profile to 2000
    power_output['DateTime'] = power_output['DateTime'].apply(lambda x: x.replace(year=2000))

    # Identify zero power output periods
    power_output['is_zero'] = power_output['Power_Output_kWh'] == 0

    # Group consecutive zero periods
    power_output['group'] = (~power_output['is_zero']).cumsum()

    # Identify groups where the zero period lasts more than 1 day (96 intervals for 15-minute data)
    zero_groups = power_output[power_output['is_zero']].groupby('group').size()
    long_zero_groups = zero_groups[zero_groups > 96].index

    # Handle long zero periods
    for group in long_zero_groups:
        period_power = power_output[power_output['group'] == group]

        # Get the start and end indices of the missing group
        start_idx = period_power.index.min()
        end_idx = period_power.index.max()

        # Calculate the length of the missing group
        group_length = len(period_power)

        # Create fake groups before and after the missing group
        before_period_power = power_output.loc[start_idx - group_length:start_idx - 1]
        after_period_power = power_output.loc[end_idx + 1:end_idx + group_length]

        # Skip if fake groups are incomplete
        if len(before_period_power) < group_length or len(after_period_power) < group_length:
            continue

        # Calculate total power output for fake groups
        before_total = before_period_power['Power_Output_kWh'].sum()
        after_total = after_period_power['Power_Output_kWh'].sum()

        # Choose the fake group with the lowest total power output
        if before_total < after_total:
            fill_data = before_period_power['Power_Output_kWh'].values
        else:
            fill_data = after_period_power['Power_Output_kWh'].values

        # Replace the missing group with the chosen fake group
        power_output.loc[period_power.index, 'Power_Output_kWh'] = fill_data

    # Preserve single-day zero periods (do not change their values)
    single_day_groups = zero_groups[zero_groups <= 96].index
    for group in single_day_groups:
        power_output.loc[power_output['group'] == group, 'Power_Output_kWh'] = 0

    # Drop helper columns
    power_output = power_output.drop(columns=['is_zero', 'group'])

    return power_output[["DateTime", "Power_Output_kWh"]]

def all_correct_data_files(power_output_old, load_profile_old, belpex_data_old, WP_panel, N_module, tilt_module, azimuth_module):
    power_output_old = power_output_old.copy()  # Avoid SettingWithCopyWarning
    load_profile_old = load_profile_old.copy()  # Avoid SettingWithCopyWarning
    belpex_data_old = belpex_data_old.copy()  # Avoid SettingWithCopyWarning

    power_output = correct_irradiance_data(WP_panel, N_module, tilt_module, azimuth_module, power_output_old)  # File with date-time and irradiance values
    load_profile = correct_load_profile(load_profile_old)  # File with date-time and consumption values
    belpex_data = correct_belpex_data(belpex_data_old)  # File with date-time and index values

    # Make all the timestamps timezone-aware
    belpex_data["datetime"] = belpex_data["datetime"].dt.tz_localize("Europe/Brussels", ambiguous="NaT", nonexistent="NaT")
    #power_output["DateTime"] = power_output["DateTime"].dt.tz_convert("Europe/Brussels")
    #load_profile["Datum_Startuur"] = load_profile["Datum_Startuur"].dt.tz_convert("Europe/Brussels")

    data = pd.DataFrame()
    data['datetime'] = power_output['DateTime']
    data['Power_Output_kWh'] = power_output['Power_Output_kWh']
    data['Volume_Afname_kWh'] = load_profile['Volume_Afname_kWh']
    data['Euro'] = belpex_data['Euro']
    

    return data, power_output, load_profile, belpex_data