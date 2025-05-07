import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def average_power(power_output, load_profile):
    power_output = power_output.copy()
    load_profile = load_profile.copy()

    # Set the index to 'DateTime' for resampling
    power_output.set_index('DateTime', inplace=True)
    load_profile.set_index('Datum_Startuur', inplace=True)

    # Normalize timezones by removing them
    power_output.index = power_output.index.tz_localize(None)
    load_profile.index = load_profile.index.tz_localize(None)

    # Resample data to 15-minute intervals and calculate the mean for each interval
    power_output_resampled = power_output.resample('15min').mean()
    load_profile_resampled = load_profile.resample('15min').mean()

    # Group by time of day to calculate the average across all days
    power_output_resampled['TimeOfDay'] = power_output_resampled.index.time
    load_profile_resampled['TimeOfDay'] = load_profile_resampled.index.time

    average_power_output = power_output_resampled.groupby('TimeOfDay')['Power_Output_kWh'].mean()
    average_load = load_profile_resampled.groupby('TimeOfDay')['Volume_Afname_kWh'].mean()

    # Convert time to minutes since midnight for plotting
    average_power_output.index = [t.hour * 60 + t.minute for t in average_power_output.index]
    average_load.index = [t.hour * 60 + t.minute for t in average_load.index]
    
    print(f"Total average power output: {average_power_output.sum():.2f} kWh")
    # Plot average power output and load for every 15 minutes
    plt.figure(figsize=(14, 8))
    plt.plot(average_power_output.index, average_power_output.values, marker='none', linestyle='-', color='b', label='Average Power Output')
    plt.plot(average_load.index, average_load.values, marker='none', linestyle='-', color='r', label='Average Load')
    plt.xlabel("Time of Day (minutes since midnight)")
    plt.ylabel("Energy (kWh)")
    plt.title("Average Power Output and Load for Every 15 Minutes")
    plt.legend()
    plt.grid()
    plt.xticks(np.arange(0, 1441, 60), labels=[f'{h}:00' for h in range(25)], rotation=45)
    plt.tight_layout()
    plt.show()

    return average_power_output, average_load


def power_per_year(power_output, load_profile):
    power_output = power_output.copy()
    load_profile = load_profile.copy()

    # Compute daily power output and daily load using pivot_table
    daily_load = load_profile.pivot_table(index=load_profile['Datum_Startuur'].dt.date, 
                                          values='Volume_Afname_kWh', 
                                          aggfunc='sum')
    daily_power_output = power_output.pivot_table(index=power_output['DateTime'].dt.date, 
                                                  values='Power_Output_kWh', 
                                                  aggfunc='sum')

    # Convert the index to DatetimeIndex
    daily_load.index = pd.to_datetime(daily_load.index)
    daily_power_output.index = pd.to_datetime(daily_power_output.index)

    # Compute the mean daily power output and daily load across all years using resample
    average_daily_power_output = daily_power_output.resample('D').mean()
    average_daily_load = daily_load.resample('D').mean()

    print(f"Average daily load: {average_daily_load.mean().iloc[0]:.2f} kWh")
    print(f"Average daily power output: {average_daily_power_output.mean().iloc[0]:.2f} kWh")

    total_power_output = power_output['Power_Output_kWh'].sum()
    print('Total power output:', total_power_output, 'kWh')

    # Plot the load and power output values using matplotlib
    plt.figure(figsize=(14, 8))
    plt.plot(daily_load.index, daily_load.values, label='Load (Volume_Afname_kWh)', marker='none', linestyle='-')
    plt.plot(daily_power_output.index, daily_power_output.values, label='Power Output', marker='none', linestyle='-')
    plt.xlabel('Time')
    plt.ylabel('Power [kWh]')
    plt.title('Load and Power Output Profile')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def belpex_visualisation(belpex_data):
    belpex_data = belpex_data.copy()

    # Ensure the 'datetime' column is timezone-naive for plotting
    belpex_data['datetime'] = belpex_data['datetime'].dt.tz_localize(None)

    # Plot the value of the Euro column as a function of datetime
    plt.figure(figsize=(14, 8))
    plt.plot(belpex_data['datetime'], belpex_data['Euro'], marker='none', linestyle='-', color='g', label='Euro Value')
    plt.xlabel('Datetime')
    plt.ylabel('Euro Value')
    plt.title('Euro Value Over Time')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
