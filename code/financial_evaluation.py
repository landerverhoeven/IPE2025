# Calculate CAPEX, OPEX, Net Present Value (NPV) and/or Payback Period to find the financial optimum
#   Parameters:
#       - capex: Capital Expenditure (initial investment cost)
#       - opex: Annual Operational Expenditure
#       - cash_flows: List of annual cash flows (revenues - costs)
#       - discount_rate: Discount rate for NPV calculation

import numpy as np
from day_night_electricity_cost import day_night_electricity_cost
from dynamic_electricity_cost import calculate_total_dynamic_cost

# CAPEX (Capital Expenditure) calculation
def calculate_capex(investment_cost, financing_rate, financing_period):
    """
    Calculate the Capital Expenditure (CAPEX) for a project.

    Parameters:
        investment_cost (float): The total cost of the project.
        financing_rate (float): The interest rate for financing.
        financing_period (int): The period over which the financing is spread.

    Returns:
        float: The CAPEX value.
    """
    # Calculate the CAPEX using the formula
    capex = investment_cost# * (1 + financing_rate) ** financing_period
    return capex

cost_panels = 4000
cost_inverter = 1000
cost_battery = 2000
cost_installation = 1000
cost_other = 0
investment_cost = cost_panels + cost_inverter + cost_battery + cost_installation + cost_other
financing_rate = 0.05  # Example financing rate (5%)
financing_period = 20  # Example financing period (20 years)
capex = calculate_capex(investment_cost, financing_rate, financing_period)
print(f"CAPEX: {capex:.2f} euros")


# OPEX (Operational Expenditure) calculation
opex = 0 # I don't get what this would be, operation is zero unless you pay for cleaning, maintenance, insurance or count depreciation
print(f"OPEX: {opex:.2f} euros")

# NPV (Net Present Value) calculation
def net_present_value(Total_cost_without_solar, Total_electricity_cost_solar, capex, opex, discount_rate, financing_period):
    annual_net_savings = Total_cost_without_solar - Total_electricity_cost_solar - opex
    npv = -capex + sum(annual_net_savings / (1 + discount_rate)**t for t in range(1, financing_period + 1))
    return npv

# Example parameters for NPV calculation
from main import data, totalcost_variable, totalcost_dynamic
data2 = data.copy()
data2["Power_Output_kWh"] = 0

print("VARIABLE")
_, Total_cost_without_solar_variable = day_night_electricity_cost(data2, [0])
print("total cost without solar panels: ", Total_cost_without_solar_variable)
print("total cost with solar panels: ", totalcost_variable)
net_present_value_variable = net_present_value(Total_cost_without_solar_variable, totalcost_variable, capex, opex, discount_rate=0.05, financing_period=20)
print(f"NPV: {net_present_value_variable:.2f} euros")


print("DYNAMIC")
Total_cost_without_solar_dynamic = calculate_total_dynamic_cost(data2, [0])
print("total cost without solar panels: ", Total_cost_without_solar_dynamic)
print("total cost with solar panels: ", totalcost_dynamic)

net_present_value_dynamic = net_present_value(Total_cost_without_solar_dynamic, totalcost_dynamic, capex, opex, discount_rate=0.05, financing_period=20)
print(f"NPV: {net_present_value_dynamic:.2f} euros")

# VOORLOPIG KLOPPEN DEZE WAARDEN ECHT VOOR GEEN METER WANT IK KOM HIER ZWAAR NEGATIEVE NPV UIT MAAR DA IS OKE IK FIX NOG
# Miss onlogische voorbeeldwaarden, foute formule, of zonnepanelen zijn gewoon niet rendabel


# Payback Period calculation
def payback_period(Total_cost_without_solar, Total_electricity_cost_solar, capex, opex):
    annual_net_savings = Total_cost_without_solar - Total_electricity_cost_solar - opex
    payback_period = capex / annual_net_savings
    return payback_period

payback_period_variable = payback_period(Total_cost_without_solar_variable, totalcost_variable, capex, opex)
print(f"Payback Period Variable: {payback_period_variable:.0f} years")

payback_period_dynamic = payback_period(Total_cost_without_solar_dynamic, totalcost_dynamic, capex, opex)
print(f"Payback Period Dynamic: {payback_period_dynamic:.0f} years")