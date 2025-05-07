import pandas as pd

# SOURCE: ENGIE Electrabel - Dynamic electricity prices

def calculate_total_dynamic_cost(data, battery):
    data = data.copy()
    # check if battery is dataframe or not
    if isinstance(battery, pd.DataFrame):
        battery = battery.copy()
    else:
        battery = pd.DataFrame({'charge_power': [0] * len(data)})

    """
    Calculate the total yearly electricity cost, including dynamic and fixed costs.
    Returns the total cost.
    """
    # Calculate electricity cost for each 15-minute interval
    vat_tarrif = 1.06  # VAT tariff

    # Calculate the difference between the load profile and the power output
    data['electricity_needed'] = data['Volume_Afname_kWh'] - data['Power_Output_kWh'] + battery['charge_power'] 
    
    # Update the condition to handle element-wise comparison
    data['effective_electricity_needed'] = data['electricity_needed'].apply(lambda x: x if x > 0 else 0)

    def load_average_kW_peak(data):
        # Calculate kW_peak (maximum load in kW) for each month using 15-minute intervals
        data['Month'] = data['datetime'].dt.month
        data['effective_electricity_needed'] = data['effective_electricity_needed'] / 0.25  # Convert kWh to kW (15 minutes = 0.25 hours)
        kW_peak_matrix = data.groupby('Month')['effective_electricity_needed'].max().reset_index()
        kW_peak_matrix.rename(columns={'effective_electricity_needed': 'kW_peak'}, inplace=True)

        # Calculate the average kW_peak across all months
        average_kW_peak = kW_peak_matrix['kW_peak'].mean()

        # Ensure the average_kW_peak is at least 2.5 kW
        if average_kW_peak < 2.5:
            average_kW_peak = 2.5
        return average_kW_peak
    
    def calculation_dynamic_dynamic_cost(electricity_needed, euro, effective_electricity_needed):
        # Use NumPy operations to handle arrays element-wise
        import numpy as np

        # Dynamic tariff calculation
        dynamic_tariff = np.where(
            electricity_needed > 0,
            ((1.316 + 0.1 * euro) * vat_tarrif / 100) * electricity_needed,
            ((-1.3050 + 0.1 * euro) * vat_tarrif / 100) * electricity_needed
        )
        costs_green_energy = 1.060 / 100 * effective_electricity_needed
        costs_chp = 1.582 / 100 * effective_electricity_needed

        # Network costs
        take_off_tariff = (5.60719 / 100) * effective_electricity_needed

        # Taxes
        energy_contribution = (0.20417 / 100) * effective_electricity_needed
        federal_duties = (5.03288 / 100) * effective_electricity_needed

        return dynamic_tariff, costs_green_energy, costs_chp, take_off_tariff, energy_contribution, federal_duties

    # Correct the multi-column assignment
    (data['dynamic_tariff'], data['costs_green_energy'], data['costs_chp'], 
     data['take_off_tariff'], data['energy_contribution'], data['federal_duties']) = calculation_dynamic_dynamic_cost(
        electricity_needed=data['electricity_needed'].values,
        euro=data['Euro'].values,
        effective_electricity_needed=data['effective_electricity_needed'].values
    )

    # Cost energy produced
    fixed_fee = 100.70
    dynamic_tariff = data['dynamic_tariff'].sum()
    costs_green_energy = data['costs_green_energy'].sum()
    costs_chp = data['costs_chp'].sum()
    total_cost_energy_produced = fixed_fee + dynamic_tariff + costs_green_energy + costs_chp
    #print(f"Cost energy produced (Yearly): €{total_cost_energy_produced:.2f}")

    # Network costs
    data_management_fee = 18.56  # Annual fee
    take_off_tariff = data['take_off_tariff'].sum()
    capacity_tarrif = 51.9852 * load_average_kW_peak(data)  # Annual capacity tariff per kW
    total_network_cost = data_management_fee + take_off_tariff + capacity_tarrif
    #print(f"Network Cost (Yearly): €{total_network_cost:.2f}")

    # Taxes
    energy_contribution = data['energy_contribution'].sum()
    federal_duties = data['federal_duties'].sum()
    total_taxes = energy_contribution + federal_duties
    #print(f"Taxes (Yearly): €{total_taxes:.2f}")

    # Total yearly cost
    total_cost = total_cost_energy_produced + total_network_cost + total_taxes
    #print(f"Total Cost (Yearly): €{total_cost:.2f}")

    return total_cost