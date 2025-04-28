import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def calculate_power_difference(data):
    """
    Calculate the power difference between power output and load profile.

    Parameters:
        power_output (DataFrame): DataFrame containing power output data.
        load_profile (DataFrame): DataFrame containing load profile data.

    Returns:
        DataFrame: DataFrame containing the power difference.
    """
    # Debug: Print the structure of power_output and load_profile
    #print("Debug: Power Output Columns:", power_output.columns)
    #print(power_output.head())
    #print("Debug: Load Profile Columns:", load_profile.columns)
    #print(load_profile.head())

    # Normalize column names
    #power_output.columns = power_output.columns.str.strip().str.lower()
    #load_profile.columns = load_profile.columns.str.strip().str.lower()

    # Debug: Print normalized column names
    #print("Debug: Normalized Power Output Columns:", power_output.columns)
    #print("Debug: Normalized Load Profile Columns:", load_profile.columns)

    # Ensure 'datetime' and 'datum_startuur' are in the same timezone
    #power_output['datetime'] = pd.to_datetime(power_output['datetime']).dt.tz_localize(None)
    #load_profile['datum_startuur'] = pd.to_datetime(load_profile['datum_startuur'])

    # Debug: Print the dtypes after normalization
    #print("Debug: Power Output DateTime dtype:", power_output['datetime'].dtype)
    #print("Debug: Load Profile Datum_Startuur dtype:", load_profile['datum_startuur'].dtype)

    # Merge the dataframes on the datetime columns
    #merged_data = pd.merge(
    #    power_output,
    #    load_profile,
    #    left_on='datetime',
    #    right_on='datum_startuur',
    #    how='inner'
    #)

    # Debug: Print the merged_data columns
    #print("Debug: Merged DataFrame Columns:", merged_data.columns)

    # Calculate the power difference
    data['power_difference_kwh'] = data['Power_Output_kWh'] - data['Volume_Afname_kWh']
    """"
    plt.figure(figsize=(12, 6))
    #plt.plot(data['datetime'], data['Power_Output_kWh'], label='Power Output (kWh)', color='blue')
    plt.plot(data['datetime'], data['power_difference_kwh'], label='Power Difference (kWh)', color='orange')
    #plt.plot(data['datetime'], data['Volume_Afname_kWh'], label='Load Profile (kWh)', color='red')
    plt.xlabel('Datetime')
    plt.ylabel('Energy (kWh)')
    plt.title('Power Output, Power Difference, and Load Profile')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    """
    data['power_difference_kwh_for_conventional'] = data['power_difference_kwh']
    data['power_difference_kwh'] = data['power_difference_kwh'].clip(lower=0)

    """
    ## Plot power_output, power_difference, and load_profile on the same graph
    plt.figure(figsize=(12, 6))
    #plt.plot(data['datetime'], data['Power_Output_kWh'], label='Power Output (kWh)', color='blue')
    plt.plot(data['datetime'], data['power_difference_kwh'], label='Power Difference (kWh)', color='orange')
    #plt.plot(data['datetime'], data['Volume_Afname_kWh'], label='Load Profile (kWh)', color='red')
    plt.xlabel('Datetime')
    plt.ylabel('Energy (kWh)')
    plt.title('Power Output, Power Difference, and Load Profile')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    # Save the plot as an image
    plt.savefig('results/power_output_difference_load_profile.png')
    plt.show()
    """
    print('Total surplus:', data["power_difference_kwh"].sum(), 'kWh')

    return data[['datetime', 'power_difference_kwh']]


def calculate_average_daily_power_difference(power_difference_data):
    """
    Calculate the average daily power difference.

    Parameters:
        power_difference_data (DataFrame): DataFrame containing power difference data.

    Returns:
        DataFrame: DataFrame containing the average daily power difference.
    """
    # Debug: Print the structure of power_difference_data
    #print("Debug: Power Difference DataFrame Columns:", power_difference_data.columns)

    # Use the lowercase column name 'datetime'
    power_difference_data["TimeOfDay"] = power_difference_data["datetime"].dt.strftime("%H:%M")
    average_daily_difference = power_difference_data.groupby("TimeOfDay")["power_difference_kwh"].mean().reset_index()
    average_daily_difference.rename(columns={"power_difference_kwh": "Average_Power_Difference_kWh"}, inplace=True)

    return average_daily_difference
