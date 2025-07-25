import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

API_KEY = "75730JF7ESBDGL7U"  # Your Alpha Vantage key

# Function to get stock data
def get_stock_data(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={API_KEY}&outputsize=compact"
    response = requests.get(url)
    data = response.json()
    ts = data.get("Time Series (Daily)", {})
    
    if not ts:
        return None

    df = pd.DataFrame.from_dict(ts, orient='index')
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df

# Streamlit layout
st.title("📈 Halal Stock Line Chart Viewer")

symbol = st.text_input("Enter Stock Symbol", "AAPL").upper()

if symbol:
    with st.spinner(f"Fetching data for {symbol}..."):
        df = get_stock_data(symbol)
        if df is not None:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df["5. adjusted close"], mode="lines", name="Adj Close"))
            fig.update_layout(
                title=f"{symbol} - Adjusted Closing Price (Past 100 Days)",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                height=500
            )
            st.plotly_chart(fig)
        else:
            st.error("Stock data not available or symbol is incorrect.")
