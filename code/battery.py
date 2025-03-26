import pandas as pd
import numpy as np
from calculations_power import power_output, load_power

def power_difference_if_generated_is_larger():
    # Get the power output and load data
    irradiance_data = power_output(N=1, beta=30, A=1.6, eta=0.15, phi_panel=180)
    load_data = load_power()

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
print(difference_data)