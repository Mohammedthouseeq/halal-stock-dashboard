import streamlit as st
import pandas as pd
import requests

# Set white background
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
  background-color: white !important;
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Halal Stock Dashboard", layout="wide")
st.title("📈 Halal Stock Dashboard")

API_KEY = st.secrets["ALPHA_VANTAGE_KEY"]

# List of symbols to analyze (North America)
symbols = ["AAPL", "MSFT", "NVDA", "ADBE", "TSLA"]

# List of banned symbols (banks, alcohol, gambling, etc.)
banned = ["JPM", "KO", "PEP", "WFC", "LVS"]  # example banned symbols

# Filter symbols for halal compliance
filtered = [s for s in symbols if s not in banned]

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

for symbol in filtered:
    st.subheader(symbol)
    data = get_stock_data(symbol)
    if data is not None and "4. close" in data.columns:
        st.line_chart(data["4. close"])
    else:
        st.warning("⚠️ Live data unavailable. Showing sample chart.")
        sample = pd.DataFrame({
            'Day': pd.date_range(end=pd.Timestamp.today(), periods=7),
            'Price': [100, 101, 99, 98, 100, 102, 103]
        }).set_index('Day')
        st.line_chart(sample)
