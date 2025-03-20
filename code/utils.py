def calculate_panel_output(irradiance, area, efficiency):
    return irradiance * area * efficiency

def calculate_energy_generated(irradiance_data, panel_area, panel_efficiency):
    energy_generated = []
    for index, row in irradiance_data.iterrows():
        output = calculate_panel_output(row['Irradiance'], panel_area, panel_efficiency)
        energy_generated.append(output)
    return energy_generated

def resample_data(data, frequency, time_column):
    return data.resample(frequency, on=time_column).mean().reset_index()

def convert_to_radians(degrees):
    return np.radians(degrees)