import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Constants for PV system
beta = np.radians(20)  # Panel tilt angle (radians)
rho = 0.2  # Ground reflectance
A = 2  # Panel area (m^2)
eta = 0.18  # Panel efficiency (18%)
N = 15  # Number of panels
T_ref = 25  # Reference temperature (°C)
temp_coeff = -0.004  # Temperature coefficient of efficiency (per °C)
latitude = np.radians(50.93)  # Hasselt, Belgium (radians)
longitude = 5.34
phi_panel = np.radians(180)  # Panel azimuth angle (radians)

# Load data
irradiance_data = pd.read_excel("Irradiance_data.xlsx", parse_dates=["DateTime"])
load_data = pd.read_excel("Load_profile_8.xlsx", parse_dates=["Datum_Startuur"])

# Resample data to 15-minute averages
irradiance_data = irradiance_data.resample('15min', on='DateTime').mean().reset_index()
load_data = load_data.resample('15min', on='Datum_Startuur').mean().reset_index()

# Extract necessary values
irradiance_data["Hour"] = irradiance_data["DateTime"].dt.hour
load_data["Hour"] = load_data["Datum_Startuur"].dt.hour
local_time = irradiance_data["DateTime"].dt.hour + irradiance_data["DateTime"].dt.minute / 60
day_of_year = irradiance_data["DateTime"].dt.dayofyear

# Vectorized solar position calculation
def calculate_solar_position(latitude, longitude, local_time, day_of_year):
    B = np.radians((360 / 365) * (day_of_year - 81))
    eot = 9.87 * np.sin(2 * B) - 7.53 * np.cos(B) - 1.5 * np.sin(B)
    standard_meridian = 15 * round(longitude / 15)
    solar_time = local_time + (4 * (longitude - standard_meridian) + eot) / 60
    h_angle = np.radians(15 * (solar_time - 12))
    declination = np.radians(23.45 * np.sin(np.radians((360 / 365) * (day_of_year - 81))))
    zenith_angle = np.arccos(np.sin(latitude) * np.sin(declination) + np.cos(latitude) * np.cos(declination) * np.cos(h_angle))
    sin_azimuth = (np.cos(declination) * np.sin(h_angle)) / np.sin(zenith_angle)
    azimuth = np.degrees(np.arcsin(sin_azimuth))
    azimuth = np.where(azimuth >= 0, azimuth, azimuth + 360)
    return zenith_angle, np.radians(azimuth)

# Vectorized PV power calculation
def calculate_pv_power(GlobRad, DiffRad, T_cell, latitude, longitude, time, day_of_year):
    theta_z_rad, gamma_s_rad = calculate_solar_position(latitude, longitude, time, day_of_year)
    GHI = np.maximum(0, GlobRad)
    DHI = np.maximum(0, DiffRad)
    DNI = np.where(np.cos(theta_z_rad) > 0, np.where(GHI > DHI, (GHI - DHI) / np.maximum(np.cos(theta_z_rad), 1e-10), 0), 0)
    cos_theta_i = np.cos(theta_z_rad) * np.cos(beta) + np.sin(theta_z_rad) * np.sin(beta) * np.cos(gamma_s_rad - phi_panel)
    G_POA = DNI * cos_theta_i + DHI * (1 + np.cos(beta)) / 2 + GHI * rho * (1 - np.cos(beta)) / 2
    eta_temp = eta * (1 + temp_coeff * (T_cell - T_ref))
    return np.maximum(0, G_POA * A * eta_temp * N) / 1000  # Convert to kWh


# Compute PV power output
irradiance_data["Power_Output_kWh"] = calculate_pv_power(
    irradiance_data["GlobRad"].values,
    irradiance_data["DiffRad"].values,
    irradiance_data["T_RV_degC"].values,
    latitude,
    longitude,
    local_time.values,
    day_of_year.values
)

# Resample the load data to hourly intervals and calculate the sum for each hour
load_data = load_data.set_index("Datum_Startuur").resample('H').sum().reset_index()

# Extract the hour from the timestamp
load_data["Hour"] = load_data["Datum_Startuur"].dt.hour

# Calculate average hourly consumption
hourly_load = load_data.groupby("Hour")["Volume_Afname_kWh"].mean()

# Compute average hourly power output
hourly_power_output = irradiance_data.groupby("Hour")["Power_Output_kWh"].mean()

# Compute daily averages
average_daily_power_output = hourly_power_output.sum()
average_daily_load = hourly_load.sum()

print(f"Average daily power output: {average_daily_power_output:.2f} kWh")
print(f"Average daily load: {average_daily_load:.2f} kWh")

# Export the data to an Excel file
output_data = pd.DataFrame({
    "DateTime": irradiance_data["DateTime"],
    "Power_Output_kWh": irradiance_data["Power_Output_kWh"],
    "Load_kWh": load_data["Volume_Afname_kWh"]
})
output_data.to_excel("output_data.xlsx", index=False)
print("DONE")

# Plot results
plt.figure(figsize=(10, 5))
plt.plot(hourly_power_output.index, hourly_power_output.values, marker='o', linestyle='-', color='b', label='Power Output')
plt.plot(hourly_load.index, hourly_load.values, marker='o', linestyle='-', color='r', label='Load')
plt.xlabel("Hour of the Day")
plt.ylabel("Energy (kWh)")
plt.title("Average Hourly Power Output vs. Load")
plt.legend()
plt.grid()
plt.show()
print("hello world")
print("het werkt?")