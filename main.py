import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Your Alpha Vantage API key
API_KEY = '4BDKJHW8LPKHKUHU'


# Function to search for company stock symbols
def search_symbol(company, api_key):
    url = f'https://www.alphavantage.co/query'
    params = {
        'function': 'SYMBOL_SEARCH',
        'keywords': company,
        'apikey': api_key
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if "bestMatches" in data and data["bestMatches"]:
            matches = data["bestMatches"]
            return [(match["1. symbol"], match["2. name"]) for match in matches]
        else:
            return None
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None


# Function to get real-time stock data from Alpha Vantage
def get_stock_data(stock, stock_interval, api_key):
    url = f'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': stock,
        'interval': stock_interval,
        'apikey': api_key
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if f"Time Series ({stock_interval})" in data:
            return data[f"Time Series ({stock_interval})"]
        else:
            return None
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None


# Function to get weekly stock high prices
def get_weekly_highs(stock_symbol_, api_key):
    url = f'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': stock_symbol_,
        'apikey': api_key
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if "Time Series (Daily)" in data:
            daily_data = data["Time Series (Daily)"]
            df_ = pd.DataFrame.from_dict(daily_data, orient='index')
            df_['timestamp'] = pd.to_datetime(df_.index)
            df_['close'] = df_['4. close'].astype(float)
            df_ = df_.sort_values('timestamp', ascending=False)  # Sort by date

            # Filter data for the last 7 days
            df_last_week = df_.head(7)
            max_close = df_last_week['close'].max()
            max_date = df_last_week.loc[df_last_week['close'].idxmax(), 'timestamp']

            return {
                "max_close": max_close,
                "max_date": max_date,
                "data": df_last_week
            }
        else:
            return None
    else:
        st.error(f"Error fetching weekly data: {response.status_code}")
        return None


# Streamlit app layout
st.title("Real-Time Stock Price Dashboard")

# Step 1: Company name search
user_company_name = st.text_input("Enter Company Name (e.g., Apple)", "")

if user_company_name:
    company_symbols = search_symbol(user_company_name, API_KEY)

    if company_symbols:
        st.subheader("Search Results")
        selected_stock = st.selectbox(
            "Select a Stock Symbol",
            company_symbols,
            format_func=lambda x: f"{x[0]} - {x[1]}"
        )
    else:
        st.warning("No matches found. Try another company name.")
        selected_stock = None
else:
    selected_stock = None

# Step 2: Interval selection
selected_interval = st.selectbox(
    "Select Time Interval",
    options=["1min", "5min", "15min", "30min", "60min"],
    index=1  # Default to "5min"
)

# Step 3: Fetch and display stock data
if selected_stock:
    stock_symbol = selected_stock[0]  # Extract symbol from selected option

    # Weekly highs
    weekly_data = get_weekly_highs(stock_symbol, API_KEY)

    if weekly_data:
        st.subheader(f"Weekly High for {stock_symbol.upper()}")
        st.write(f"Highest Closing Price: **${weekly_data['max_close']}** on **{weekly_data['max_date'].date()}**")
        st.write("Last Week's Data:")
        st.dataframe(weekly_data["data"][['timestamp', 'close']])

    # Real-time data
    stock_data = get_stock_data(stock_symbol, selected_interval, API_KEY)

    if stock_data:
        # Convert the data into a pandas DataFrame
        df = pd.DataFrame.from_dict(stock_data, orient='index')
        df['timestamp'] = pd.to_datetime(df.index)
        df['open'] = df['1. open'].astype(float)
        df['high'] = df['2. high'].astype(float)
        df['low'] = df['3. low'].astype(float)
        df['close'] = df['4. close'].astype(float)
        df['volume'] = df['5. volume'].astype(int)

        # Display the dataframe as a table
        st.subheader(f"Stock Data for {stock_symbol.upper()} ({selected_interval} Interval)")
        st.write(df[['timestamp', 'open', 'high', 'low', 'close', 'volume']])

        # Plot the stock prices using Plotly
        fig = px.line(df, x='timestamp', y='close', title=f'{stock_symbol.upper()} Stock Price')
        st.plotly_chart(fig)
    else:
        st.warning("No real-time data available for the selected stock and interval.")
