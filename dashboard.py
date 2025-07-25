import streamlit as st
import requests

# White background style
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
  background-color: white !important;
  padding: 1rem 2rem;
}
@media (max-width: 600px) {
  .stock-row {
    flex-direction: column !important;
    align-items: flex-start !important;
  }
  .stock-logo {
    margin-bottom: 0.5rem !important;
  }
  .stock-text {
    font-size: 1.2rem !important;
  }
}
</style>
""", unsafe_allow_html=True)

st.title("📈 Halal Stock Dashboard — Current Prices with Logos")

API_KEY = st.secrets["ALPHA_VANTAGE_KEY"]

symbols = ["AAPL", "MSFT", "NVDA", "ADBE", "TSLA"]
banned = ["JPM", "KO", "PEP", "WFC", "LVS"]  # banned stocks
filtered = [s for s in symbols if s not in banned]

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
    
    cols = st.columns([1, 4])
    with cols[0]:
        st.image(logo_url, width=60)
    with cols[1]:
        st.markdown(f"<div style='font-size:1.4rem;'><b>{symbol}</b>: ${price} ({change})</div>", unsafe_allow_html=True)

