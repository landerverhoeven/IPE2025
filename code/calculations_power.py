import pandas as pd
import pvlib
import numpy as np
import matplotlib.pyplot as plt

def calculation_power_output(WP_panel, N_module, tilt_module, azimuth_module, irradiance_data):
    # Constants for PV system
    albedo = 0.2  # Ground reflectance
    temp_coeff = -0.004  # Temperature coefficient (per °C)
    latitude = 50.93   # Hasselt, Belgium (degrees)
    longitude = 5.34

    # Calculate DC capacity (in W)
    dc_capacity = N_module * WP_panel  

    # Ensure DateTime is a timezone-aware datetime in Europe/Brussels timezone
    irradiance_data["DateTime"] = pd.to_datetime(irradiance_data["DateTime"])  # Ensure DateTime is in datetime format
    if irradiance_data["DateTime"].dt.tz is None:
        irradiance_data["DateTime"] = irradiance_data["DateTime"].dt.tz_localize("Europe/Brussels", ambiguous="NaT", nonexistent="NaT")
    else:
        irradiance_data["DateTime"] = irradiance_data["DateTime"].dt.tz_convert("Europe/Brussels")
    
    # Convert DateTime to UTC for solar position calculations
    irradiance_data["DateTime_UTC"] = irradiance_data["DateTime"].dt.tz_convert("UTC")

    # Calculate solar position using the DateTime_UTC column
    solar_position = pvlib.solarposition.get_solarposition(
        time=irradiance_data["DateTime_UTC"], 
        latitude=latitude, 
        longitude=longitude
    )

    # Align solar_position with irradiance_data by copying the index
    solar_position.index = irradiance_data.index

    # Calculate DNI (Direct Normal Irradiance)
    irradiance_data["DNI"] = pvlib.irradiance.dni(
        ghi=irradiance_data["GlobRad"],
        dhi=irradiance_data["DiffRad"],
        zenith=solar_position["zenith"]
    )

    # Calculate POA (Plane-of-Array) irradiance
    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=tilt_module,
        surface_azimuth=azimuth_module,
        dni=irradiance_data["DNI"],
        ghi=irradiance_data["GlobRad"],
        dhi=irradiance_data["DiffRad"],
        solar_zenith=solar_position["zenith"],
        solar_azimuth=solar_position["azimuth"],
        albedo=albedo,
    )

    # Determine the ambient temperature column depending on the tilt angle
    irradiance_data["T_cell"] = irradiance_data["T_RV_degC"] if tilt_module > np.radians(10) else irradiance_data["T_CommRoof_degC"]

    # Calculate the DC power output using the PVWatts model and convert from W to kW
    irradiance_data["Power_Output_kW"] = pvlib.pvsystem.pvwatts_dc(
        g_poa_effective=poa["poa_global"],
        temp_cell=irradiance_data["T_cell"],
        pdc0=dc_capacity,
        gamma_pdc=temp_coeff
    ) / 1000  # Convert W to kW

    # Convert power to energy (kWh) for 1-minute intervals
    irradiance_data["Power_Output_kWh"] = irradiance_data["Power_Output_kW"] / 60
    
    return irradiance_data[["DateTime", "Power_Output_kWh"]]