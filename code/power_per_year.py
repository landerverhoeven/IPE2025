import pandas as pd
import matplotlib.pyplot as plt

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
    plt.plot(daily_load.index, daily_load.values, label='Load (Volume_Afname_kWh)', marker='o', linestyle='-')
    plt.plot(daily_power_output.index, daily_power_output.values, label='Power Output', marker='x', linestyle='-')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.title('Load and Power Output Profile (15-minute intervals)')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()