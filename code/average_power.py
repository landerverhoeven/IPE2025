import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def average_power(power_output, load_profile):
    power_output = power_output.copy()
    load_profile = load_profile.copy()

    # Set the index to 'DateTime' for resampling
    power_output.set_index('DateTime', inplace=True)
    load_profile.set_index('Datum_Startuur', inplace=True)

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

    # Plot average power output and load for every 15 minutes
    plt.figure(figsize=(14, 8))
    plt.plot(average_power_output.index, average_power_output.values, marker='o', linestyle='-', color='b', label='Average Power Output')
    plt.plot(average_load.index, average_load.values, marker='x', linestyle='-', color='r', label='Average Load')
    plt.xlabel("Time of Day (minutes since midnight)")
    plt.ylabel("Energy (kWh)")
    plt.title("Average Power Output and Load for Every 15 Minutes")
    plt.legend()
    plt.grid()
    plt.xticks(np.arange(0, 1441, 60), labels=[f'{h}:00' for h in range(25)], rotation=45)
    plt.tight_layout()
    plt.show()