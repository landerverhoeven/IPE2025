import numpy as np
import matplotlib.pyplot as plt

def calculation_power_output_1(N, beta, A, eta, phi_panel, irradiance_data):
    # Constants for PV system
    rho = 0.2  # Ground reflectance
    T_ref = 25  # Reference temperature (°C)
    temp_coeff = -0.004  # Temperature coefficient of efficiency (per °C)
    latitude = np.radians(50.93)  # Hasselt, Belgium (radians)
    longitude = 5.34
    
    # Extract necessary values
    local_time = irradiance_data["DateTime"].dt.hour + irradiance_data["DateTime"].dt.minute / 60
    day_of_year = irradiance_data["DateTime"].dt.dayofyear
    
    def calculate_solar_position(latitude, longitude, local_time, day_of_year):
        # Calculate solar position parameters
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

    def calculate_pv_power(GlobRad, DiffRad, T_cell, latitude, longitude, local_time, day_of_year):
        # Calculate solar position
        theta_z_rad, gamma_s_rad = calculate_solar_position(latitude, longitude, local_time, day_of_year)
        
        # Calculate irradiance components
        GHI = np.maximum(0, GlobRad)
        DHI = np.maximum(0, DiffRad)
        DNI = np.where(np.cos(theta_z_rad) > 0, np.where(GHI > DHI, (GHI - DHI) / np.maximum(np.cos(theta_z_rad), 1e-10), 0), 0)
        
        # Calculate angle of incidence
        cos_theta_i = np.cos(theta_z_rad) * np.cos(beta) + np.sin(theta_z_rad) * np.sin(beta) * np.cos(gamma_s_rad - phi_panel)
        
        # Calculate plane of array irradiance
        G_POA = DNI * cos_theta_i + DHI * (1 + np.cos(beta)) / 2 + GHI * rho * (1 - np.cos(beta)) / 2
        
        # Adjust efficiency for temperature
        eta_temp = eta * (1 + temp_coeff * (T_cell - T_ref))
        
        # Calculate power output
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
    
    # Calculate zenith and azimuth angles
    zenith_angles = []
    azimuth_angles = []

    for lt, doy in zip(local_time, day_of_year):
        zenith_angle, azimuth_angle = calculate_solar_position(latitude, longitude, lt, doy)
        zenith_angles.append(zenith_angle)
        azimuth_angles.append(azimuth_angle)

    # Plot the results
    plt.figure(figsize=(10, 6))

    # Zenith angle plot
    plt.plot(local_time, zenith_angles, label="Zenith Angle (rad)", color="blue")

    # Azimuth angle plot
    plt.plot(local_time, azimuth_angles, label="Azimuth Angle (deg)", color="orange")

    # Add labels and legend
    plt.xlabel("Local Time (hours)")
    plt.ylabel("Radians")
    plt.title("Zenith and Azimuth Angles vs Local Time")
    plt.legend()
    plt.grid()

    # Show the plot
    plt.show()


    return irradiance_data[["DateTime", "Power_Output_kWh"]]
