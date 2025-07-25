import streamlit as st
import pandas as pd
import requests
st.markdown("""
    <style>
        body {
            background-color: white !important;
            color: black;
        }
        .stApp {
            background-color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Halal Stock Dashboard", layout="wide")
st.title("📈 Halal Stock Dashboard")

API_KEY = st.secrets["ALPHA_VANTAGE_KEY"]

def get_stock_data(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if "Time Series (Daily)" in data:
        df = pd.DataFrame(data["Time Series (Daily)"]).T
        df = df.astype(float)
        return df
    else:
        return None

symbols = ["AAPL", "MSFT", "NVDA", "ADBE", "TSLA"]
filtered_symbols = [s for s in symbols if s not in ["JPM", "WFC", "KO", "PEP", "LVS"]]

for symbol in filtered_symbols:
    st.subheader(symbol)
    data = get_stock_data(symbol)
    if data is not None:
        st.line_chart(data["4. close"])
    else:
        st.write("⚠️ No data available.")
