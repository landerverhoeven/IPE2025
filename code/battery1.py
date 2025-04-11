import pandas as pd
import numpy as np

def calculate_power_difference(power_output, load_profile):
    """
    Calculate the difference between power generated and power consumed.

    :param power_output: DataFrame containing power output data with a 'DateTime' column and 'Power_Output_kWh'.
    :param load_profile: DataFrame containing load profile data with a 'Datum_Startuur' column and 'Volume_Afname_KWh'.
    :return: DataFrame with power difference.
    """
    # Ensure datetime columns are in the correct format
    power_output["DateTime"] = pd.to_datetime(power_output["DateTime"])
    load_profile["Datum_Startuur"] = pd.to_datetime(load_profile["Datum_Startuur"])

    # Set datetime columns as the index for resampling
    power_output.set_index("DateTime", inplace=True)
    load_profile.set_index("Datum_Startuur", inplace=True)

    # Resample data to 15-minute intervals and calculate the mean for each interval
    power_output_resampled = power_output.resample('15min').mean()
    load_profile_resampled = load_profile.resample('15min').mean()

    # Reset the index after resampling
    power_output_resampled.reset_index(inplace=True)
    load_profile_resampled.reset_index(inplace=True)

    # Remove timezone from DateTime column in power_output_resampled
    power_output_resampled["DateTime"] = power_output_resampled["DateTime"].dt.tz_localize(None)

    # Merge the dataframes on the timestamp
    merged_data = pd.merge(power_output_resampled, load_profile_resampled, left_on="DateTime", right_on="Datum_Startuur")

    # Calculate the power difference (ensure it's non-negative)
    merged_data["Power_Difference_kWh"] = np.where(
        merged_data["Power_Output_kWh"] > merged_data["Volume_Afname_kWh"],  # Update this column name if needed
        merged_data["Power_Output_kWh"] - merged_data["Volume_Afname_kWh"],  # Update this column name if needed
        0
    )

    return merged_data[["DateTime", "Power_Difference_kWh"]]


def calculate_average_daily_power_difference(power_difference_data):
    """
    Calculate the average power difference for each 15-minute interval over a single day.

    :param power_difference_data: DataFrame containing power difference data with 'DateTime' and 'Power_Difference_kWh'.
    :return: DataFrame with average power difference for each 15-minute interval of a day.
    """
    # Extract the time of day (ignoring the date)
    power_difference_data["TimeOfDay"] = power_difference_data["DateTime"].dt.strftime("%H:%M")

    # Group by the time of day and calculate the average power difference
    average_daily_difference = power_difference_data.groupby("TimeOfDay")["Power_Difference_kWh"].mean().reset_index()

    return average_daily_difference
