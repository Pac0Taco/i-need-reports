import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt


def process_data(data, start_date, end_date, interval):
    # Define weekly intervals based on user selection
    if interval == "daily":
        velocity_str = "/day"
        freq_val = 'D'
    elif interval == "weekly":
        velocity_str = "/week"
        freq_val = 'W-SUN'
    elif interval == "bi-weekly":
        velocity_str = "/2-weeks"
        freq_val = '2W-SUN'
    elif interval == "monthly":
        velocity_str = "/month"
        freq_val = 'M'
    else:
        raise ValueError("Invalid interval selection")


    date_range = pd.date_range(start=start_date, end=end_date, freq=freq_val)


    # Define weekly intervals
    burndown_df = pd.DataFrame({'Date': date_range})

    # Calculate the cumulative sum of story points for tickets created during or before each interval
    burndown_df['Cumulative_Created'] = burndown_df['Date'].apply(
        lambda x: data.loc[data['Created'] <= x, 'Story Points'].sum())

    # Calculate the cumulative sum of story points for tickets resolved during or before each interval
    burndown_df['Cumulative_Resolved'] = burndown_df['Date'].apply(
        lambda x: data.loc[data['Resolved'] <= x, 'Story Points'].sum())

    # Calculate the remaining scope for each interval
    burndown_df['Remaining_Scope'] = burndown_df['Cumulative_Created'] - burndown_df['Cumulative_Resolved']
    
    


    # Calculate average velocity and predicted burndown
    current_date = pd.Timestamp(datetime.date.today())
    past_data = burndown_df[burndown_df['Date'] <= current_date]
    if custom_velocity > 0:
        average_velocity = custom_velocity
    else:
        average_velocity = past_data['Cumulative_Resolved'].iloc[-1] / len(past_data)
    burndown_df['Predicted_Burndown'] = burndown_df['Remaining_Scope'].copy()
    burndown_df['Adjusted_Predicted_Burndown'] = burndown_df['Remaining_Scope'].copy()
    predicted_value = burndown_df['Remaining_Scope'].iloc[0]
    for i in range(len(burndown_df)):
        if burndown_df['Date'].iloc[i] > current_date:
            predicted_value = burndown_df['Predicted_Burndown'].iloc[i-1] - average_velocity
            burndown_df['Predicted_Burndown'].iloc[i] = max(predicted_value, 0)
        if burndown_df['Date'].iloc[i] >= current_date:
            adjusted_value = predicted_value + 0.15 * burndown_df['Remaining_Scope'].iloc[i]
        else:
            adjusted_value = burndown_df['Remaining_Scope'].iloc[i]
        burndown_df['Adjusted_Predicted_Burndown'].iloc[i] = max(adjusted_value, 0)


    return burndown_df, average_velocity, velocity_str


def plot_burndown(burndown_df, velocity, start_date, end_date):
    # Convert the native datetime.date objects to pandas Timestamps
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)
    # Filter the data based on the selected date range
    burndown_df = burndown_df[(burndown_df['Date'] >= start_date) & (burndown_df['Date'] <= end_date)]




    current_date = pd.Timestamp(datetime.date.today())
    plt.figure(figsize=(14, 6))
    # Plot only the past remaining scope
    past_data = burndown_df[burndown_df['Date'] <= pd.Timestamp(datetime.date.today())]
    plt.plot(past_data['Date'], past_data['Remaining_Scope'], label='Remaining Scope', color='green', zorder=2)
    
    # Plot the predicted burndown
    plt.plot(burndown_df['Date'], burndown_df['Predicted_Burndown'], label='Predicted Burndown', linestyle=':', color='red', zorder=1)
    future_data = burndown_df[burndown_df['Date'] >= current_date]
    #plt.plot(future_data['Date'], future_data['Adjusted_Predicted_Burndown'], label='Adjusted Predicted Burndown (15% Increase)', linestyle=':', color='green')

    
    # Highlight the predicted completion date
    future_data = burndown_df[burndown_df['Date'] > pd.Timestamp(datetime.date.today())]
    predicted_completion_date = future_data[future_data['Predicted_Burndown'] <= 0]['Date'].min()
    if predicted_completion_date:
        
        if pd.notna(predicted_completion_date):
            plt.axvline(x=predicted_completion_date, color='blue', linestyle='--')

            plt.text(predicted_completion_date, burndown_df['Remaining_Scope'].max() * 0.9, f' {predicted_completion_date.strftime("%Y-%m-%d")}', verticalalignment='center', horizontalalignment='left', color='blue', fontsize=10)
        
        plt.fill_between(past_data['Date'], past_data['Remaining_Scope'], color='green', alpha=0.1)
        plt.title(f'Burndown Chart (Velocity: {velocity:.2f} story points{velocity_str})')
        plt.xlabel('Date')
        plt.ylabel('Story Points')
        plt.xticks(burndown_df['Date'][::2], rotation=45)
        plt.legend()
        plt.grid(axis='y')
        plt.tight_layout()
        return plt

# Streamlit App
interval = st.sidebar.selectbox("Select Interval:", ["bi-weekly", "daily", "weekly", "monthly"])




start_date = st.sidebar.date_input('Start Date', datetime.date(2022, 7, 1))
end_date = st.sidebar.date_input('End Date', datetime.date(2024, 1, 1))
custom_velocity = st.sidebar.number_input("Velocity Override", 0)

uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file:
    data = pd.read_excel(uploaded_file, parse_dates=['Created', 'Resolved'])
    burndown_df, velocity, velocity_str = process_data(data, start_date, end_date, interval)
    chart = plot_burndown(burndown_df, velocity, start_date, end_date)
    st.pyplot(chart)