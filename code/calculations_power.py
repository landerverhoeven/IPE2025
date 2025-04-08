import pandas as pd
import numpy as np

def power_output(N, beta, A, eta, phi_panel, irradiance_data):
    # Constants for PV system
    rho = 0.2  # Ground reflectance
    T_ref = 25  # Reference temperature (°C)
    temp_coeff = -0.004  # Temperature coefficient of efficiency (per °C)
    latitude = np.radians(50.93)  # Hasselt, Belgium (radians)
    longitude = 5.34
    
    # Extract necessary values
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
    return irradiance_data[["DateTime", "Power_Output_kWh"]]
