import streamlit as st
import requests

# White background style
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
  background-color: white !important;
  padding: 1rem 2rem;
}
</style>
""", unsafe_allow_html=True)

# Centered heading on top
st.markdown("""
    <h1 style='text-align: center; color: black; margin-bottom: 2rem;'>
        📈 Halal Stock Dashboard — Current Prices with Logos
    </h1>
""", unsafe_allow_html=True)

API_KEY = st.secrets["ALPHA_VANTAGE_KEY"]

symbols = [
    "AAPL", "MSFT", "NVDA", "ADBE", "TSLA", "GOOGL", "AMZN", "META",
    "INTC", "CSCO", "ORCL", "CRM", "AMD", "QCOM", "AVGO"
]

banned = ["JPM", "KO", "PEP", "WFC", "LVS"]  # banned stocks
filtered = [s for s in symbols if s not in banned]

logo_domains = {
    "AAPL": "apple.com",
    "MSFT": "microsoft.com",
    "NVDA": "nvidia.com",
    "ADBE": "adobe.com",
    "TSLA": "tesla.com",
    "GOOGL": "abc.xyz",
    "AMZN": "amazon.com",
    "META": "fb.com",
    "INTC": "intel.com",
    "CSCO": "cisco.com",
    "ORCL": "oracle.com",
    "CRM": "salesforce.com",
    "AMD": "amd.com",
    "QCOM": "qualcomm.com",
    "AVGO": "broadcom.com",
}

def fetch_current_quote(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json().get("Global Quote", {})
    price = data.get("05. price", "N/A")
    change_percent = data.get("10. change percent", "N/A")
    return price, change_percent

# Display all stocks in columns (4 per row)
cols_per_row = 4
rows = (len(filtered) + cols_per_row - 1) // cols_per_row

for row in range(rows):
    cols = st.columns(cols_per_row)
    for i in range(cols_per_row):
        idx = row * cols_per_row + i
        if idx >= len(filtered):
            break
        symbol = filtered[idx]
        price, change = fetch_current_quote(symbol)
        logo_url = f"https://logo.clearbit.com/{logo_domains[symbol]}"
        with cols[i]:
            st.image(logo_url, width=70)
            st.markdown(f"### {symbol}")
            st.markdown(f"**Price:** ${price}")
            st.markdown(f"**Change:** {change}")
