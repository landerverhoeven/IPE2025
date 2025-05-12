import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def conventional_battery(battery_capacity, data):
    data = data.copy()  # Create a copy of the input DataFrame to avoid modifying the original
    """
    Simulates the charging and discharging of a battery based on power surplus and deficit.

    Parameters:
        battery_capacity (float): Maximum capacity of the battery in kWh.
        data (DataFrame): DataFrame containing hourly power data with columns:
                          - 'datetime': Timestamp of the hour
                          - 'power_difference_kwh': Surplus (+) or deficit (-) of power in kWh

    Returns:
        charge_schedule (list): List of dictionaries with charging details.
        discharge_schedule (list): List of dictionaries with discharging details.
    """
    # Initialize variables
    current_charge = 0  # Current charge level of the battery
    charge_amount = 0  # Amount of power charged during the hour
    discharge_amount = 0  # Amount of power discharged during the hour
    charge_schedule = []  # To store charging details
    discharge_schedule = []  # To store discharging details
    charge_discharge_schedule = []  # To store charge/discharge schedule

    # Iterate through each hour in the data
    for _, row in data.iterrows():
        hour = row['datetime']
        power_difference = row['power_difference_kwh_for_conventional']

        if power_difference > 0:
            # Surplus of power: Charge the battery
            charge_amount = min(power_difference, battery_capacity - current_charge)
            current_charge += charge_amount
            discharge_amount = 0  # Reset discharge amount
            
            
        elif power_difference < 0:
            # Deficit of power: Discharge the battery
            discharge_amount = min(abs(power_difference), current_charge)
            current_charge -= discharge_amount
            charge_amount = 0
        discharge_schedule.append({
                'hour': hour,
                'discharge_power': discharge_amount,
                'current_charge': current_charge
        })
        charge_schedule.append({
                'hour': hour,
                'charge_power': charge_amount,
                'current_charge': current_charge
            })
        charge_discharge_schedule.append({
                'hour': hour,
                'charge_power': charge_amount-discharge_amount,
                'current_charge': current_charge
            })

    convention_charge_schedule_df = pd.DataFrame(charge_schedule)
    convention_discharge_schedule_df = pd.DataFrame(discharge_schedule)
    convention_charge_discharge_schedule_df = pd.DataFrame(charge_discharge_schedule)

    # Remove timezone information from datetime columns
    if 'hour' in convention_charge_schedule_df.columns:
        convention_charge_schedule_df['hour'] = pd.to_datetime(convention_charge_schedule_df['hour']).dt.tz_localize(None)
    if 'hour' in convention_discharge_schedule_df.columns:
        convention_discharge_schedule_df['hour'] = pd.to_datetime(convention_discharge_schedule_df['hour']).dt.tz_localize(None)
    if 'hour' in convention_charge_discharge_schedule_df.columns:
        convention_charge_discharge_schedule_df['hour'] = pd.to_datetime(convention_charge_discharge_schedule_df['hour']).dt.tz_localize(None)

    # Save the conventional charge and discharge schedules to Excel
    with pd.ExcelWriter('results/conventional_battery_schedules.xlsx') as writer:
        convention_charge_schedule_df.to_excel(writer, sheet_name='Charge Schedule', index=False)
        convention_discharge_schedule_df.to_excel(writer, sheet_name='Discharge Schedule', index=False)
        convention_charge_discharge_schedule_df.to_excel(writer, sheet_name='Charge Discharge Schedule', index=False)


    # Load Excel data
    df = convention_charge_discharge_schedule_df.copy()

    # Extract relevant time info
    df['date'] = df['hour'].dt.date  # Extract the date for the y-axis
    df['time'] = df['hour'].dt.time  # Extract the time for the x-axis

    # Create heatmap matrix (date vs. time)
    heatmap_data = df.pivot_table(
        index='date',  # Rows represent dates
        columns='time',  # Columns represent times
        values='charge_power',
        aggfunc='mean'
    ).fillna(0)

    # Plot heatmap
    plt.figure(figsize=(18, 8))
    ax = sns.heatmap(
        heatmap_data,
        cmap="BrBG",  # Diverging colormap: green for positive, blue for negative
        center=0,  # Center the colormap at 0
        cbar_kws={'label': 'Charge Power (kW)'},  # Remove 'fontsize' from here
        xticklabels=8,  # Show every 8th time label
        yticklabels=30  # Show every 30th date label
    )

    # Set title and axis labels with larger font sizes
    plt.title("Conventional Battery Charging/Discharging Heatmap (Year Overview)", fontsize=18)
    plt.xlabel("Time of Day", fontsize=16)
    plt.ylabel("Date", fontsize=16)
    plt.xticks(fontsize=14, rotation=45)  # Rotate x-axis labels for better readability
    plt.yticks(fontsize=14)

    # Adjust colorbar font size
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(labelsize=14)  # Set font size for colorbar ticks

    plt.tight_layout()
    plt.savefig('results/conventional_battery_heatmap.png')
    #plt.show()

    # Zoomed-in week view (e.g., May 30 to June 5, 2000)
    week_data = df[(df['hour'] >= pd.Timestamp('2000-05-30')) & (df['hour'] < pd.Timestamp('2000-06-06'))]

    plt.figure(figsize=(16, 6))
    plt.plot(week_data['hour'], week_data['charge_power'], color='teal', linewidth=1)
    plt.axhline(0, color='black', linestyle='--', linewidth=0.8)
    plt.title("Conventional Battery Charging/Discharging – Week View (May 30 to June 5)", fontsize=16)
    plt.ylabel("Charge Power (kW)", fontsize=14)
    plt.xlabel("Datetime", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('results/conventional_battery_week_view.png')
    #plt.show()

        # Extract month
    df['month'] = df['hour'].dt.month

    # Separate charge and discharge values
    df['charged'] = df['charge_power'].clip(lower=0)  # Only positive values (charging)
    df['discharged'] = -df['charge_power'].clip(upper=0)  # Negative values flipped positive (discharging)

    # Monthly summary
    monthly_summary = df.groupby('month')[['charged', 'discharged']].sum()

    # Plot grouped bar chart
    plt.figure(figsize=(12, 6))
    monthly_summary.plot(kind='bar', stacked=False, color=['green', 'blue'], width=0.8)
    plt.title("Monthly Energy Charged and Discharged by Conventional Battery")
    plt.xlabel("Month", fontsize=14)
    plt.ylabel("Energy (kWh)", fontsize=14)
    plt.xticks(
        ticks=range(0, 12),
        labels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        rotation=45,
        fontsize=12
    )
    plt.yticks(fontsize=12)
    plt.legend(["Charged", "Discharged"], fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('results/conventional_battery_monthly_summary.png')
    #plt.show()

    return convention_charge_schedule_df, convention_discharge_schedule_df, convention_charge_discharge_schedule_df
