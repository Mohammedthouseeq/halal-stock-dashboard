import streamlit as st
import requests

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
  background-color: white !important;
}
</style>
""", unsafe_allow_html=True)

st.title("📈 Halal Stock Dashboard — Current Prices")

API_KEY = st.secrets["ALPHA_VANTAGE_KEY"]

symbols = ["AAPL", "MSFT", "NVDA", "ADBE", "TSLA"]
banned = ["JPM", "KO", "PEP", "WFC", "LVS"]  # banned stocks
filtered = [s for s in symbols if s not in banned]

def fetch_current_quote(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json().get("Global Quote", {})
    price = data.get("05. price", "N/A")
    change_percent = data.get("10. change percent", "N/A")
    return price, change_percent

for symbol in filtered:
    price, change = fetch_current_quote(symbol)
    st.write(f"**{symbol}:** ${price} ({change})")
