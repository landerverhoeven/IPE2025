import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#from calculations_power import power_output, load_power

# General 
vat_tarrif = 1
# price_day, price_night, injection_price, load_consumption, power_output_data
def day_night_electricity_cost(data, battery):
    # Electricity production
    data = data.copy()
    # check if battery is dataframe or not
    if isinstance(battery, pd.DataFrame):
        battery = battery.copy()
    else:
        battery = pd.DataFrame({'charge_power': [0] * len(data)})

   # Prices for day and night source: engie (vtest)
    price_day = 0.1489 + 0.0117 + 0.0042 # Price for day + green energy + WKK
    price_night = 0.1180 + 0.0117 + 0.0042 # Price for night + green energy + WKK
    injection_price = 0.0465  # Example price for injection

    # charge power from smartmodel
    
    # Initialize the cost columns
    # Calculate the difference between the load profile and the power output
    data['electricity_needed'] = (data['Volume_Afname_kWh'] - data['Power_Output_kWh'] + battery['charge_power']).apply(lambda x: x if x > 0 else 0)
    data['electricity_injected'] = (data['Volume_Afname_kWh'] - data['Power_Output_kWh'] + battery['charge_power']).apply(lambda x: -x if x < 0 else 0)

    data['electricity_cost'] = 0
    data['network_costs_per_15min'] = 0
    data['taxes'] = 0
    data['total_cost_per_15min'] = 0
    data['income_energy_injected'] = 0

    # Calculate kW_peak
    kw_peak_sum = 0
    for month in data['datetime'].dt.month.unique():
        kw_peak_month = data[data['datetime'].dt.month == month]['electricity_needed'].max()
#        #print(f'Month {month}: kW_peak_month = {kw_peak_month}')
        kw_peak_sum = kw_peak_sum + kw_peak_month
    kw_peak = kw_peak_sum / 12 * 4  # Average kW_peak per quarter hour

    # Calculate the electricity cost based on day and night tariffs
    data['electricity_cost'] = np.where(
        data['datetime'].apply(is_daytime),
        price_day * data['electricity_needed'],
        price_night * data['electricity_needed'])    
    
    # fixed fee
    fixed_fee = 20 
    
    # Network costs (vat incl.) #VREG says these are the prices for Fluvius midden-Vlaanderen, maybe it makes more sense to use Fluvius Zenne-Dijle bcs Leuven is part of that? (I already changed it to Leuven) BUT NEEDS TO BE THE SAME EVERYWHERE
    capacity_tarrif = 59.1475 # eur/kW/year Source: https://www.vlaamsenutsregulator.be/sites/default/files/Distributienettarieven_2025/vereenvoudigde_tarieflijsten_elek_2025.pdf
    take_off_fee = 64.2466 / 1000 # 56.0719 eur/MWh
    data_management_fee = 18.56 #eur/year
    max_network_cost = 347.2738 #eur/year

    # Taxes
    energy_contribution = 0 #apperently this is something else than energiefonds# from Flemish government 2025 source: https://www.vlaanderen.be/belastingen-en-begroting/vlaamse-belastingen/energieheffingen/bijdrage-energiefonds-heffing-op-afnamepunten-van-elektriciteit/tarief-van-de-bijdrage-energiefonds
    federal_energy_tax = 50.33 / 1000 # vat incl. from federal government source: https://www.test-aankoop.be/woning-energie/gas-elektriciteit-mazout-pellets/nieuws/accijnzen-gas-elektriciteit-1-april


    # calculate all cost per 15min
    data['network_costs_per_15min'] = take_off_fee * data['electricity_needed']
    data['taxes'] = (energy_contribution+federal_energy_tax) * data['electricity_needed'] # no taxes on income energy contribution
    data['total_cost_per_15min'] = data['electricity_cost'] + data['network_costs_per_15min'] + data['taxes']
    data['income_energy_injected'] = -1 * injection_price * data['electricity_injected']

    # Calculate total cost for the year
    total_electricity_cost = data['electricity_cost'].sum() + fixed_fee
    total_network_costs = data['network_costs_per_15min'].sum() + capacity_tarrif * kw_peak + data_management_fee
    total_taxes = data['taxes'].sum()
    total_injected_income = data['income_energy_injected'].sum()
    #print('total_injected_income:', total_injected_income, 'eur')
    total_cost_fullyear = total_electricity_cost + total_network_costs + total_taxes + total_injected_income
    # just to check if the calculation is correct
    #total_cost_fullyear2 = load_consumption['total_cost_per_15min'].sum() + fixed_fee + capacity_tarrif * kw_peak + data_management_fee
    #print('total cost fullyear:', total_cost_fullyear)
    #print('total cost fullyear2:', total_cost_fullyear2)

    # Remove timezone information from date_time column
    data['datetime'] = data['datetime'].dt.tz_localize(None)
    # Save the results to a new file
    #load_consumption.to_excel('results\\electricity_cost_results_day_night.xlsx', index=False)
    
    '''
    # Print somle useful information
    print('total electricity costs:', total_electricity_cost, 'eur')
    print('network costs:', total_network_costs, 'eur')
    print('taxes:', total_taxes, 'eur')
    print('total costs:', total_cost_fullyear, 'eur')
    '''
    return data, total_cost_fullyear

def is_daytime(timestamp):
    hour = timestamp.hour
    weekday = timestamp.weekday()
    # Daytime is between 7 and 22 on weekdays
    if weekday < 5 and 7 <= hour < 22:
        return True
    return False

'''
# Prices for day and night source: engie (vtest)
price_day = 0.1489  # Example price for day
price_night = 0.1180  # Example price for night

# Read data from Excel files
# load_profile = pd.read_excel(r'data\#Load_profile_8.xlsx')  # File with date-time and consumption values

# Convert the first column to date_time format
load_profile['Datum_Startuur'] = pd.to_datetime(load_profile.iloc[:, 0])

# Calculate day and night electricity cost
# load_profile, totalelectricity, totalnetwork, totaltaxes, totalcost = day_night_electricity_cost(
#     price_day, price_night, load_profile, power_output_data)

# Print some useful information
# print(load_profile.head())
print('total electricity costs:', totalelectricity, 'eur')
print('network costs:', totalnetwork, 'eur')
print('taxes:', totaltaxes, 'eur')
print('total costs:', totalcost, 'eur')

# Load day and night
load_day = load_profile[load_profile['Datum_Startuur'].apply(is_daytime)]
load_night = load_profile[~load_profile['Datum_Startuur'].apply(is_daytime)]
print('day load:', load_day['Volume_Afname_kWh'].sum(), 'kWh')
print('night load:', load_night['Volume_Afname_kWh'].sum(), 'kWh')

# Remove timezone information from date_time column
load_profile['Datum_Startuur'] = load_profile['Datum_Startuur'].dt.tz_localize(None)

# Save the results to a new file
load_profile.to_excel(r'results\electricity_cost_results_day_night.xlsx', index=False)

# Plot the total cost per 15min
plt.plot(load_profile['Datum_Startuur'], load_profile['total_cost_per_15min'])
plt.xlabel('Date Time')
plt.ylabel('Total Cost per 15min')
plt.title('Total Cost per 15min Over Time')
plt.xlim(pd.Timestamp('2022-01-01'), pd.Timestamp('2022-01-02'))
plt.show()
'''

'''
# Load day and night
load_day = load_profile[load_profile['Datum_Startuur'].apply(is_daytime)]
load_night = load_profile[~load_profile['Datum_Startuur'].apply(is_daytime)]
print('day load:', load_day['Volume_Afname_kWh'].sum(), 'kWh')
print('night load:', load_night['Volume_Afname_kWh'].sum(), 'kWh')
print(power_output.head())
power_output_day = power_output[power_output['DateTime'].apply(is_daytime)]
power_output_night = power_output[~power_output['DateTime'].apply(is_daytime)]
print('Day power output:', power_output_day['Power_Output_kWh'].sum(), 'kWh')
print('Night power output:', power_output_night['Power_Output_kWh'].sum(), 'kWh')

# Plot the total cost per 15min
plt.plot(load_profile['Datum_Startuur'], load_profile['total_cost_per_15min'])
plt.xlabel('Date Time')
plt.ylabel('Total Cost per 15min')
plt.title('Total Cost per 15min Over Time')
plt.xlim(pd.Timestamp('2022-01-01'), pd.Timestamp('2022-01-02'))
plt.show()
'''