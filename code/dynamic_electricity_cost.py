import pandas as pd

# SOURCE: ENGIE Electrabel - Dynamic electricity prices

def calculate_total_dynamic_cost(power_output, load_profile, belpex_data):
    """
    Calculate the total yearly electricity cost, including dynamic and fixed costs.
    Returns the total cost.
    """
    # Calculate electricity cost for each 15-minute interval
    vat_tarrif = 1.06  # VAT tariff
    load_profile['electricity_cost'] = (
        ((0.1 * belpex_data['Euro'].values + 1.316) * vat_tarrif / 100) * load_profile['Volume_Afname_kWh'] +  # Cost energy produced
        (5.60719 / 100) * load_profile['Volume_Afname_kWh'] +  # Network costs
        ((0.20417 / 100) + (5.03288 / 100)) * load_profile['Volume_Afname_kWh']  # Taxes
    )

    # Total dynamic costs
    dynamic_costs = load_profile['electricity_cost'].sum()
    print(f"Dynamic Cost (Yearly): €{dynamic_costs:.2f}")
    
    # Fixed yearly costs
    fixed_fee = 100.70  # Fixed fee per year
    capacity_tarrif = 51.9852  # Annual capacity tariff per kW
    data_management_fee = 18.56  # Annual fee

    # Calculate kW_peak (maximum load in kW) for each month using 15-minute intervals
    load_profile['Month'] = load_profile['Datum_Startuur'].dt.month
    load_profile['load_consumption_kw'] = load_profile['Volume_Afname_kWh'] / 0.25  # Convert kWh to kW (15 minutes = 0.25 hours)
    kW_peak_matrix = load_profile.groupby('Month')['load_consumption_kw'].max().reset_index()
    kW_peak_matrix.rename(columns={'load_consumption_kw': 'kW_peak'}, inplace=True)

    # Calculate the average kW_peak across all months
    average_kW_peak = kW_peak_matrix['kW_peak'].mean()

    # Ensure the average_kW_peak is at least 2.5 kW
    if average_kW_peak < 2.5:
        average_kW_peak = 2.5

    # Calculate the total capacity tariff for the year
    total_capacity_tarrif = average_kW_peak * capacity_tarrif

    # Total yearly cost
    total_cost = dynamic_costs + fixed_fee + data_management_fee + total_capacity_tarrif

    # Print the total cost
    print(f"Total Electricity Cost (Yearly): €{total_cost:.2f}")
    print(f"belpex_data rows after filtering: {len(belpex_data)}")
    print(f"load_profile rows after filtering: {len(load_profile)}")
    print("belpex_data datetime range:", belpex_data['datetime'].min(), "to", belpex_data['datetime'].max())
    print("load_profile date_time range:", load_profile['Datum_Startuur'].min(), "to", load_profile['Datum_Startuur'].max())

    return total_cost