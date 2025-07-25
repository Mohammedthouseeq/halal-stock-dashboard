import streamlit as st
import requests

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
  background-color: white !important;
}
</style>
""", unsafe_allow_html=True)

st.title("📈 Halal Stock Dashboard — Current Prices with Logos")

API_KEY = st.secrets["ALPHA_VANTAGE_KEY"]

symbols = ["AAPL", "MSFT", "NVDA", "ADBE", "TSLA"]
banned = ["JPM", "KO", "PEP", "WFC", "LVS"]  # banned stocks
filtered = [s for s in symbols if s not in banned]

# Map symbols to company domains for logos
logo_domains = {
    "AAPL": "apple.com",
    "MSFT": "microsoft.com",
    "NVDA": "nvidia.com",
    "ADBE": "adobe.com",
    "TSLA": "tesla.com"
}

def fetch_current_quote(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json().get("Global Quote", {})
    price = data.get("05. price", "N/A")
    change_percent = data.get("10. change percent", "N/A")
    return price, change_percent

for symbol in filtered:
    price, change = fetch_current_quote(symbol)
    logo_url = f"https://logo.clearbit.com/{logo_domains[symbol]}"
    col1, col2 = st.columns([1,4])
    with col1:
        st.image(logo_url, width=50)
    with col2:
        st.write(f"**{symbol}:** ${price} ({change})")
