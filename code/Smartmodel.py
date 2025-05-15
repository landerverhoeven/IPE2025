import pandas as pd
import numpy as np
from pulp import *
import matplotlib.pyplot as plt
import seaborn as sns
from pulp import LpProblem, LpVariable, LpMaximize, lpSum, LpStatus, value

def smartmodel():
    # -------------------
    # SMART MODEL
    # -------------------
    # Load data
    # Assuming the data is in a file named 'data.xlsx' in the 'results' directory
    # The file should contain columns: 'datetime', 'Power_Output_kWh', 'Volume_Afname_kWh', and 'Euro'
    # Load data
    df = pd.read_excel('results/data.xlsx')

    # Prepare data
    dt = 0.25  # 15-minute interval in hours
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['pv'] = df['Power_Output_kWh'] / dt
    df['load'] = df['Volume_Afname_kWh'] / dt
    df['price'] = df['Euro']
    df['residual'] = df['load'] - df['pv']

    # Battery specs
    c_max = 6.5
    d_max = 6.5
    E_max = 6.5
    E_min = 0.0
    eta_c = 1
    eta_d = 1
    aplha = 100
    """
    T = len(df)
    hours = range(T)

    # Optimization model
    prob = LpProblem("Battery_Optimization", LpMinimize)
    c = LpVariable.dicts("charge", hours, 0, c_max)
    d = LpVariable.dicts("discharge", hours, 0, d_max)
    SOC = LpVariable.dicts("SOC", hours, E_min, E_max)

    # Objective function
    prob += lpSum([df['price'].iloc[t] * (c[t] - d[t]) for t in hours])

    # Constraints
    for t in hours:
        if t == 0:
            prob += SOC[t] == E_max / 2 + (eta_c * c[t] - d[t] * (1 / eta_d)) * dt
        else:
            prob += SOC[t] == SOC[t - 1] + (eta_c * c[t] - d[t] * (1 / eta_d)) * dt

        # Charge only when overgeneration
        if df['residual'].iloc[t] < 0:
            prob += c[t] <= min(c_max, -df['residual'].iloc[t])
        else:
            prob += c[t] == 0

        # Discharge only when residual load
        if df['residual'].iloc[t] > 0:
            prob += d[t] <= min(d_max, df['residual'].iloc[t])
        else:
            prob += d[t] == 0

    # SOC cyclical constraint
    prob += SOC[T - 1] == E_max / 2

    # Solve
    prob.solve()

    # Add results
    df['charge_kW'] = [value(c[t]) for t in hours]
    df['discharge_kW'] = [value(d[t]) for t in hours]
    df['SOC_kWh'] = [value(SOC[t]) for t in hours]

    print("Optimization status:", LpStatus[prob.status])
    print("Total energy cost (€):", value(prob.objective))
    df['charge_power'] = (df['charge_kW'] - df['discharge_kW'])*dt  # Positive for charging, negative for discharging

    # Save results
    df.to_excel('results/optimized_battery_schedule.xlsx', index=False)
    """


    # Load your data (adjust the path as needed)

    # Prepare the data
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['residual'] = df['load'] - df['pv']
    df['price'] = df['price'].astype(float)
    df = df.sort_values('datetime').reset_index(drop=True)

    # Model parameters
    prices = df['price'].values
    residual = df['residual'].values
    N = len(df)
    delta_t = 0.25  # 15-minute intervals


    # Define the optimization problem
    model = LpProblem("Maximize_Saved_Money", LpMaximize)

    # Define variables
    c = LpVariable.dicts("charge", range(N), 0, c_max)
    d = LpVariable.dicts("discharge", range(N), 0, d_max)
    E = LpVariable.dicts("energy", range(N), 0, E_max)

    # Objective function
    model += lpSum(prices[t] * (d[t] - c[t]) + aplha*(d[t] + c[t]) for t in range(N))

    # Constraints
    for t in range(N):
        if t == 0:
            model += E[t] == E_max / 2
        else:
            model += E[t] == E[t-1] + delta_t * (eta_c * c[t] - d[t] *(1/eta_d))

        if residual[t] >= 0:
            model += c[t] == 0
        else:
            model += c[t] <= -residual[t]

        if residual[t] <= 0:
            model += d[t] == 0
        else:
            model += d[t] <= residual[t]

    # Cyclic constraint
    model += E[N-1] == E_max / 2

    # Solve
    model.solve()

    # Collect results
    df['charge_kW'] = [value(c[t]) for t in range(N)]
    df['discharge_kW'] = [value(d[t]) for t in range(N)]
    df['SOC_kWh'] = [value(E[t]) for t in range(N)]
    df['charge_power'] = (df['charge_kW'] - df['discharge_kW'])*dt  # Positive for charging, negative for discharging


    # Total savings
    total_savings = sum(prices[t] * (value(d[t]) - value(c[t])) for t in range(N))
    print("Total monetary savings (€):", total_savings)

    #save results
    df.to_excel('results/optimized_battery_schedule.xlsx', index=False)

    # -------------------
    # PLOT RESULTS
    # -------------------
    import matplotlib.dates as mdates

    plt.figure(figsize=(15, 10))

    # SOC
    plt.subplot(3, 1, 1)
    plt.plot(df['datetime'], df['SOC_kWh'], label='State of Charge (kWh)', color='black')
    plt.ylabel('SOC (kWh)')
    plt.title('Battery State of Charge Over Time')
    plt.grid(True)

    # Charging/Discharging
    plt.subplot(3, 1, 2)
    plt.plot(df['datetime'], df['charge_kW'], label='Charging', color='green', alpha=0.6)
    plt.plot(df['datetime'], df['discharge_kW'], label='Discharging', color='red', alpha=0.6)
    plt.ylabel('Power (kW)')
    plt.title('Battery Charging and Discharging')
    plt.legend()
    plt.grid(True)

    # Price & Residual Load
    plt.subplot(3, 1, 3)
    plt.plot(df['datetime'], df['price'], label='Electricity Price (€/MWh)', color='blue')
    plt.plot(df['datetime'], df['residual'], label='Residual Load (kW)', color='purple', alpha=0.6)
    plt.ylabel('Value')
    plt.title('Price and Residual Load')
    plt.legend()
    plt.grid(True)

    # Format x-axis
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    plt.show()

    # -------------------
    # PLOT HEATMAP
    # -------------------

    # Combine charging and discharging into a single column
    
    # Prepare data for the heatmap
    df['date'] = df['datetime'].dt.date  # Extract the date for the y-axis
    df['time'] = df['datetime'].dt.time  # Extract the time for the x-axis

    # Pivot table for charge power heatmap
    heatmap_data = df.pivot_table(
        index='date',  # Rows represent dates
        columns='time',  # Columns represent times
        values='charge_power',  # Values represent the charge power
        aggfunc='mean'
    ).fillna(0)

    # Plot heatmap
    plt.figure(figsize=(18, 8))
    sns.heatmap(
        heatmap_data,
        cmap="BrBG",  # Diverging colormap: red for discharging, blue for charging
        center=0,  # Center the colormap at 0
        cbar_kws={'label': 'Charge Power (kW)'},  # Colorbar label
        xticklabels=8,  # Show every 8th time label
        yticklabels=30  # Show every 30th date label
    )
    plt.title("Battery Charge Power Heatmap", fontsize=18)
    plt.xlabel("Time of Day", fontsize=14)
    plt.ylabel("Date", fontsize=14)
    plt.xticks(fontsize=12, rotation=45)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.savefig('results/smart_model_heatmap.png')
    plt.show()
    # Zoomed-in week view (e.g., May 30 to June 5, 2000)
    week_data = df[(df['datetime'] >= pd.Timestamp('2000-05-30')) & (df['datetime'] < pd.Timestamp('2000-06-06'))]

    plt.figure(figsize=(16, 6))
    plt.plot(week_data['datetime'], week_data['charge_power'], color='teal', linewidth=1)
    plt.axhline(0, color='black', linestyle='--', linewidth=0.8)
    plt.title("Smart Battery Charging/Discharging – Week View (May 30 to June 5)")
    plt.ylabel("Charge Power (kW)")
    plt.xlabel("Datetime")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('results/smart_model_week_view.png')
    plt.show()

        # Extract month
    df['month'] = df['datetime'].dt.month

    # Separate charge and discharge values
    df['charged'] = df['charge_power'].clip(lower=0)  # Only positive values (charging)
    df['discharged'] = -df['charge_power'].clip(upper=0)  # Negative values flipped positive (discharging)

    # Monthly summary
    monthly_summary = df.groupby('month')[['charged', 'discharged']].sum()

    # Plot
    plt.figure(figsize=(10, 6))
    monthly_summary.plot(kind='bar', stacked=False, color=['green', 'blue'])
    plt.title("Monthly Energy Charged and Discharged by Smart Battery")
    plt.xlabel("Month")
    plt.ylabel("Energy (kWh)")
    plt.xticks(
        ticks=range(0, 12),
        labels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        rotation=45
    )
    plt.legend(["Charged", "Discharged"])
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('results/smart_model_monthly_summary.png')
    #plt.show()

    return df