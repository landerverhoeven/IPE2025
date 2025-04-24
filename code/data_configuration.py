import time as time
start_time = time.time()
import pandas as pd
import numpy as np
from correct_data_files import all_correct_data_files


# Constants for PV system
tilt_module = np.radians(30)  # Panel tilt angle (radians)
azimuth_module = np.radians(90)  # Panel azimuth angle (radians)
WP_panel = 350  # Panel power (W)
N_module = 15  # Number of panels

# Calculate power_output, load_profile, and belpex_data
power_output_data = pd.read_excel('data/Irradiance_data.xlsx')
load_profile_data = pd.read_excel('data/Load_profile_8.xlsx')
belpex_data_data = pd.read_excel('data/Belpex_2024.xlsx')
data, power_output, load_profile, belpex_data = all_correct_data_files(power_output_data, load_profile_data, belpex_data_data, WP_panel, N_module, tilt_module, azimuth_module)
# Save the corrected data to a csv file
data.to_pickle('data/Corrected_data.pkl')
power_output.to_pickle('data/Corrected_power_output.pkl')
load_profile.to_pickle('data/Corrected_load_profile.pkl')
belpex_data.to_pickle('data/Corrected_belpex_data.pkl')

end_time = time.time()
print("Time taken to run the script: ", end_time - start_time, " seconds")