# Calculate CAPEX, OPEX, Net Present Value (NPV) and/or Payback Period to find the financial optimum
#   Parameters:
#       - capex: Capital Expenditure (initial investment cost)
#       - opex: Annual Operational Expenditure
#       - cash_flows: List of annual cash flows (revenues - costs)
#       - discount_rate: Discount rate for NPV calculation

import numpy as np
from day_night_electricity_cost import day_night_electricity_cost
from dynamic_electricity_cost import calculate_total_dynamic_cost
from tabulate import tabulate

# CAPEX (Capital Expenditure) calculation
def calculate_capex(investment_cost, financing_rate, financing_period):
    capex = investment_cost# * (1 + financing_rate) ** financing_period
    return capex

cost_panels = 4000
cost_inverter = 1000
cost_battery = 2000
cost_installation = 1000
cost_other = 0



# NPV (Net Present Value) calculation
def net_present_value(Total_cost_without_solar, Total_electricity_cost_solar, capex, opex, discount_rate, financing_period):
    annual_net_savings = Total_cost_without_solar - Total_electricity_cost_solar - opex
    npv = -capex + sum(annual_net_savings / (1 + discount_rate)**t for t in range(1, financing_period + 1))
    return npv

# Example parameters for NPV calculation

# VOORLOPIG KLOPPEN DEZE WAARDEN ECHT VOOR GEEN METER WANT IK KOM HIER ZWAAR NEGATIEVE NPV UIT MAAR DA IS OKE IK FIX NOG
# Miss onlogische voorbeeldwaarden, foute formule, of zonnepanelen zijn gewoon niet rendabel


# Payback Period calculation
'''
def payback_period(Total_cost_without_solar, Total_electricity_cost_solar, capex, opex):
    annual_net_savings = Total_cost_without_solar - Total_electricity_cost_solar - opex
    payback_period = capex / annual_net_savings
    return payback_period
'''
def payback_period(Total_cost_without_solar, Total_electricity_cost_solar, capex, opex, financing_rate):
    annual_net_savings = Total_cost_without_solar - Total_electricity_cost_solar - opex
    cumulative_discounted = 0
    for t in range(1, 100):
        discounted = annual_net_savings / (1 + financing_rate) ** t
        cumulative_discounted += discounted
        if cumulative_discounted >= capex:
            payback_period = t
            break
    return payback_period


# ______ Financial Evaluation ______
def financial_evaluation(data, totalcost_variable, totalcost_dynamic, investment_cost, financing_rate, financing_period):
    data = data.copy()  # Create a copy of the data to avoid modifying the original DataFrame
    print("______ FINANCIAL EVALUATION ______")
    # CAPEX (Capital Expenditure) calculation
    capex = calculate_capex(investment_cost, financing_rate, financing_period)
    print(f"CAPEX: {capex:.2f} euros")

    # OPEX (Operational Expenditure) calculation
    opex = 0 # I don't get what this would be, operation is zero unless you pay for cleaning, maintenance, insurance or count depreciation
    print(f"OPEX: {opex:.2f} euros")

    # Calculate NPV (Net Present Value)
    datanosolar = data.copy()
    datanosolar["Power_Output_kWh"] = 0
    totalcost_without_solar_variable = day_night_electricity_cost(datanosolar, [0])[1]
    totalcost_without_solar_dynamic = calculate_total_dynamic_cost(datanosolar, [0])
    net_present_value_variable = net_present_value(totalcost_without_solar_variable, totalcost_variable, capex, opex, financing_rate, financing_period)
    net_present_value_dynamic = net_present_value(totalcost_without_solar_dynamic, totalcost_dynamic, capex, opex, financing_rate, financing_period)
    
    # Payback Period calculation
    payback_period_variable = payback_period(totalcost_without_solar_variable, totalcost_variable, capex, opex, financing_rate)
    payback_period_dynamic = payback_period(totalcost_without_solar_dynamic, totalcost_dynamic, capex, opex, financing_rate)

    # Print the results
    table_data = [
        ["Total electricity cost without solar", f"{totalcost_without_solar_variable:.2f} euros", f"{totalcost_without_solar_dynamic:.2f} euros"],
        ["Total electricity Cost With solar", f"{totalcost_variable:.2f} euros", f"{totalcost_dynamic:.2f} euros"],
        ["Net Present Value", f"{net_present_value_variable:.2f} euros", f"{net_present_value_dynamic:.2f} euros"],
        ["Payback Period", f"{payback_period_variable:.0f} years", f"{payback_period_dynamic:.0f} years"],
    ]
    print(tabulate(table_data, headers=["", "Variable", "Dynamic"], tablefmt="grid"))

    return capex, opex, net_present_value_variable, net_present_value_dynamic, payback_period_variable, payback_period_dynamic