import pandas as pd
import pvlib
import numpy as np

def calculation_power_output(WP_panel, N_module, tilt_module, azimuth_module, irradiance_data):
    
    # Constants for PV system
    albedo = 0.2  # Ground reflectance
    temp_coeff = -0.004  # Temperature coefficient of efficiency (per °C)
    latitude = 50.93  # Hasselt, Belgium (degrees)
    longitude = 5.34

    # Calculate DC capacity
    dc_capacity = N_module * WP_panel  # Total DC capacity in W


    # Handle timezone and daylight saving time transitions
    irradiance_data["DateTime"] = handle_dst_transitions(irradiance_data["DateTime"])

    # Calculate solar position
    solar_position = pvlib.solarposition.get_solarposition(
        time=irradiance_data["DateTime"], latitude=latitude, longitude=longitude
    )

    def handle_dst_transitions(datetime_series):

        # Localize to Europe/Brussels and handle ambiguous times
        datetime_series = datetime_series.dt.tz_localize("Europe/Brussels", ambiguous="NaT")

        # Identify missing or ambiguous times
        time_diffs = datetime_series.diff()

        # Handle added hours (time difference > 1 hour)
        added_hours = time_diffs[time_diffs > pd.Timedelta(hours=1)].index
        for idx in added_hours:
            # Duplicate the previous timestamp
            datetime_series[idx] = datetime_series[idx - 1]

        # Handle skipped hours (time difference < 1 hour)
        skipped_hours = time_diffs[time_diffs < pd.Timedelta(hours=1)].index
        for idx in skipped_hours:
            # Interpolate the missing timestamp
            datetime_series[idx] = datetime_series[idx - 1] + pd.Timedelta(hours=1)

        # Convert to UTC
        datetime_series = datetime_series.dt.tz_convert("UTC")

        return datetime_series

    # Calculate DNI from GHI and DHI
    irradiance_data["DNI"] = pvlib.irradiance.dni(
        ghi=irradiance_data["GlobRad"], dhi=irradiance_data["DiffRad"], solar_zenith=solar_position["zenith"]
    )

    # Calculate POA irradiance
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

    # Determine cell temperature based on tilt angle
    if tilt_module > np.radians(10):
        # Gable roof
        T_cell = irradiance_data["T_RV_degC"]
    else:  # Flat roof
        T_cell = irradiance_data["T_CommRoof_degC"]

    # Calculate cell temperature
    irradiance_data["T_cell"] = pvlib.temperature.sapm_cell(
        poa_global=poa["poa_global"],
        temp_air=T_cell,
        wind_speed=1.0,  # Assume 1 m/s wind speed
        model="open_rack_glass_glass",
    )

    # Calculate DC power output
    irradiance_data["Power_Output_kW"] = pvlib.pvsystem.pvwatts_dc(
        g_poa_effective=poa["poa_global"],
        temp_cell=irradiance_data["T_cell"],
        pdc0=dc_capacity,
        gamma_pdc=temp_coeff
    ) / 1000  # Convert W to kW

    # Convert power to energy (kWh) for 1-minute intervals
    irradiance_data["Power_Output_kWh"] = irradiance_data["Power_Output_kW"] / 60  # kW to kWh for 1 minute

    return irradiance_data[["DateTime", "Power_Output_kWh"]]