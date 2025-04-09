import numpy as np
import pandas as pd
import pvlib
import matplotlib.pyplot as plt

def calculation_power_output(N, beta, A, eta, phi_panel, irradiance_data):
    # Constants for PV system
    rho = 0.2  # Ground reflectance
    T_ref = 25  # Reference temperature (°C)
    temp_coeff = -0.004  # Temperature coefficient of efficiency (per °C)
    latitude = 50.93  # Hasselt, Belgium (degrees)
    longitude = 5.34
    
    # Lists to store values for plotting
    local_time_list = []
    zenith_angle_list = []
    azimuth_list = []
    GHI_list = []
    DHI_list = []
    DNI_list = []
    cos_theta_i_list = []
    G_POA_list = []
    temperature_list = []
    eta_temp_list = []
    power_output_list = []

    def calculate_solar_position(latitude, longitude, local_time):
        # Calculate solar position using pvlib
        solar_position = pvlib.solarposition.get_solarposition(local_time, latitude, longitude)
        zenith_angle = solar_position['zenith']
        azimuth = solar_position['azimuth']
        return np.radians(zenith_angle), np.radians(azimuth)

    def calculate_pv_power(local_time, GlobRad, DiffRad, T_cell_gable_roof, T_cell_flat_roof):
        # Calculate solar position
        theta_z_rad, gamma_s_rad = calculate_solar_position(latitude, longitude, local_time)
        
        if phi_panel > np.radians(10):
            # Gable roof
            T_cell = T_cell_gable_roof
        else:  # Flat roof
            T_cell = T_cell_flat_roof

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
        power_output = np.maximum(0, G_POA * A * eta_temp * N) / 1000  # Convert to kWh
        
        # Store values for plotting
        local_time_list.append(local_time)
        zenith_angle_list.append(theta_z_rad)
        azimuth_list.append(gamma_s_rad)
        GHI_list.append(GHI)
        DHI_list.append(DHI)
        DNI_list.append(DNI)
        cos_theta_i_list.append(cos_theta_i)
        G_POA_list.append(G_POA)
        temperature_list.append(T_cell)
        eta_temp_list.append(eta_temp)
        power_output_list.append(power_output)
        
        return power_output

    # Compute PV power output
    irradiance_data["Power_Output_kWh"] = calculate_pv_power(
        irradiance_data["DateTime"].values,
        irradiance_data["GlobRad"].values,
        irradiance_data["DiffRad"].values,
        irradiance_data["T_RV_degC"].values,
        irradiance_data["T_CommRoof_degC"].values
    )
    
    # Plot the values
    plt.figure(figsize=(15, 10))
    
    plt.subplot(3, 4, 1)
    plt.plot(local_time_list, zenith_angle_list, label='Zenith Angle (rad)')
    plt.xlabel('Local Time')
    plt.ylabel('Zenith Angle (rad)')
    plt.legend()
    
    plt.subplot(3, 4, 2)
    plt.plot(local_time_list, azimuth_list, label='Azimuth (rad)')
    plt.xlabel('Local Time')
    plt.ylabel('Azimuth (rad)')
    plt.legend()
    
    plt.subplot(3, 4, 3)
    plt.plot(local_time_list, GHI_list, label='GHI')
    plt.xlabel('Local Time')
    plt.ylabel('GHI')
    plt.legend()
    
    plt.subplot(3, 4, 4)
    plt.plot(local_time_list, DHI_list, label='DHI')
    plt.xlabel('Local Time')
    plt.ylabel('DHI')
    plt.legend()
    
    plt.subplot(3, 4, 5)
    plt.plot(local_time_list, DNI_list, label='DNI')
    plt.xlabel('Local Time')
    plt.ylabel('DNI')
    plt.legend()
    
    plt.subplot(3, 4, 6)
    plt.plot(local_time_list, cos_theta_i_list, label='Cos(theta_i)')
    plt.xlabel('Local Time')
    plt.ylabel('Cos(theta_i)')
    plt.legend()
    
    plt.subplot(3, 4, 7)
    plt.plot(local_time_list, G_POA_list, label='G_POA')
    plt.xlabel('Local Time')
    plt.ylabel('G_POA')
    plt.legend()
    
    plt.subplot(3, 4, 8)
    plt.plot(local_time_list, temperature_list, label='Temperature')
    plt.xlabel('Local Time')
    plt.ylabel('Temperature')
    plt.legend()
    
    plt.subplot(3, 4, 9)
    plt.plot(local_time_list, eta_temp_list, label='Efficiency (eta_temp)')
    plt.xlabel('Local Time')
    plt.ylabel('Efficiency (eta_temp)')
    plt.legend()
    
    plt.subplot(3, 4, 10)
    plt.plot(local_time_list, power_output_list, label='Power Output (kWh)')
    plt.xlabel('Local Time')
    plt.ylabel('Power Output (kWh)')
    plt.legend()
    
    plt.tight_layout()
    plt.show()
    
    return irradiance_data[["DateTime", "Power_Output_kWh"]]

