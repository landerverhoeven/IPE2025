import pandas as pd
import numpy as np
import matplotlib.pyplot as plt  # Import matplotlib for plotting
from calculations_power import calculation_power_output
from main import load_profile, irradiance_path, WP_panel, N_module, tilt_module, azimuth_module

def power_difference_if_generated_is_larger():
    # Load the irradiance data from the file defined in main.py
    irradiance_data = pd.read_excel(irradiance_path)

    # Get the power output and load data
    irradiance_data = calculation_power_output(
        WP_panel=WP_panel,
        N_module=N_module,
        tilt_module=np.degrees(tilt_module),  # Convert tilt angle to degrees
        azimuth_module=np.degrees(azimuth_module),  # Convert azimuth angle to degrees
        irradiance_data=irradiance_data
    )
    load_data = load_profile  # Use load_profile directly as it is a DataFrame

    # Ensure both datetime columns have the same type (remove timezone from DateTime)
    irradiance_data["DateTime"] = irradiance_data["DateTime"].dt.tz_localize(None)
    load_data["Datum_Startuur"] = pd.to_datetime(load_data["Datum_Startuur"])  # Ensure it's in datetime format

    # Merge the data on the datetime columns
    merged_data = pd.merge(irradiance_data, load_data, left_on="DateTime", right_on="Datum_Startuur")

    # Calculate the difference where generated power is larger than consumed power
    merged_data["Power_Difference_kWh"] = np.where(
        merged_data["Power_Output_kWh"] > merged_data["Volume_Afname_kWh"],
        merged_data["Power_Output_kWh"] - merged_data["Volume_Afname_kWh"],
        0
    )

    return merged_data[["DateTime", "Power_Difference_kWh"]]

# Example usage
difference_data = power_difference_if_generated_is_larger()

# Save the results to a new file
difference_data.to_excel('results/power_difference_if_generated_is_larger.xlsx', index=False)

# Plot the results
plt.figure(figsize=(10, 6))
plt.plot(difference_data["DateTime"], difference_data["Power_Difference_kWh"], label="Power Difference (kWh)", color="blue")
plt.xlabel("DateTime")
plt.ylabel("Power Difference (kWh)")
plt.title("Power Difference Over Time")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('results/power_difference_plot.png')  # Save the plot as an image
plt.show()