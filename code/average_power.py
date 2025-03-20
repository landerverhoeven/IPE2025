import numpy as np
import matplotlib.pyplot as plt
from calculations_power import power_output, load_power

def average_power(N, beta, A, eta, phi_panel):
    # Get power output and load data
    power_output_data = power_output(N, beta, A, eta, phi_panel)
    load_data = load_power()

    # Compute daily power output
    daily_power_output = power_output_data.groupby(power_output_data["DateTime"].dt.dayofyear)["Power_Output_kWh"].sum()

    # Compute the mean daily power output across all years
    average_daily_power_output = daily_power_output.groupby(daily_power_output.index).mean()

    # Compute daily load
    daily_load = load_data.groupby(load_data["Datum_Startuur"].dt.dayofyear)["Volume_Afname_kWh"].sum()

    # Compute the mean daily load across all years
    average_daily_load = daily_load.groupby(daily_load.index).mean()

    print(f"Average daily power output: {average_daily_power_output.mean():.2f} kWh")
    print(f"Average daily load: {average_daily_load.mean():.2f} kWh")

    # Plot average daily power output across all years
    plt.figure(figsize=(10, 5))
    plt.plot(average_daily_power_output.index, average_daily_power_output.values, marker='o', linestyle='-', color='b', label='Average Daily Power Output')
    plt.xlabel("Day of the Year")
    plt.ylabel("Energy (kWh)")
    plt.title("Average Daily Power Output Across All Years")
    plt.legend()
    plt.grid()
    plt.show()