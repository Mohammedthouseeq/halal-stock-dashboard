import streamlit as st
import requests
import time

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
  background-color: white !important;
  padding: 1rem 2rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
    <h1 style='text-align: center; color: black; margin-bottom: 2rem;'>
        📊 Halal Stock Dashboard
    </h1>
""", unsafe_allow_html=True)

# Check if API key exists
try:
    API_KEY = st.secrets["ALPHA_VANTAGE_KEY"]
    if not API_KEY:
        st.error("⚠️ Alpha Vantage API key not found in secrets!")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Error accessing API key: {e}")
    st.stop()

symbols = [
    "AAPL", "MSFT", "NVDA", "ADBE", "TSLA", "GOOGL", "AMZN", "META",
    "INTC", "CSCO", "ORCL", "CRM", "AMD", "QCOM", "AVGO"
]

banned = ["JPM", "KO", "PEP", "WFC", "LVS"]
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

@st.cache_data(ttl=300)
def fetch_current_quote(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        data = response.json()
        
        # Debug: Show raw response for troubleshooting
        if st.session_state.get('debug_mode', False):
            st.write(f"Debug - Raw response for {symbol}:", data)
        
        # Check for API error messages
        if "Error Message" in data:
            st.error(f"API Error for {symbol}: {data['Error Message']}")
            return None, None, data.get("Error Message", "Unknown error")
        
        if "Note" in data:
            st.warning(f"API Note for {symbol}: {data['Note']}")
            return None, None, data.get("Note", "Rate limit or other issue")
        
        # Extract quote data
        quote_data = data.get("Global Quote", {})
        
        if not quote_data:
            return None, None, "No quote data found"
        
        price = quote_data.get("05. price")
        change_percent = quote_data.get("10. change percent")
        
        if price is None or change_percent is None:
            # Try alternative field names (API sometimes changes field names)
            price = quote_data.get("price") or quote_data.get("current_price")
            change_percent = quote_data.get("change_percent") or quote_data.get("percent_change")
        
        if price is None or change_percent is None:
            available_fields = list(quote_data.keys())
            return None, None, f"Price or change data not found. Available fields: {available_fields}"
        
        return price, change_percent, None
        
    except requests.exceptions.Timeout:
        return None, None, "Request timeout"
    except requests.exceptions.RequestException as e:
        return None, None, f"Request error: {str(e)}"
    except Exception as e:
        return None, None, f"Unexpected error: {str(e)}"

# Add debug toggle
if st.checkbox("🔧 Debug Mode (Show API responses)"):
    st.session_state.debug_mode = True
else:
    st.session_state.debug_mode = False

# Add refresh button
if st.button("🔄 Refresh All Prices"):
    st.cache_data.clear()
    st.rerun()

# Test API connection first
st.write("🔍 Testing API connection...")
test_price, test_change, test_error = fetch_current_quote("AAPL")
if test_error:
    st.error(f"❌ API Connection Test Failed: {test_error}")
    st.info("💡 Common solutions:")
    st.info("1. Check if your Alpha Vantage API key is valid")
    st.info("2. You might have exceeded the API rate limit (5 requests/minute for free tier)")
    st.info("3. Try refreshing the page in a few minutes")
else:
    st.success("✅ API Connection Test Successful")

cols_per_row = 4
rows = (len(filtered) + cols_per_row - 1) // cols_per_row

for row in range(rows):
    cols = st.columns(cols_per_row)
    for i in range(cols_per_row):
        idx = row * cols_per_row + i
        if idx >= len(filtered):
            break
        symbol = filtered[idx]
        
        with cols[i]:
            # Show logo
            logo_url = f"https://logo.clearbit.com/{logo_domains[symbol]}"
            try:
                st.image(logo_url, width=70)
            except:
                st.write("🏢")  # Fallback emoji if logo fails
            
            st.markdown(f"### {symbol}")
            
            # Add small delay between requests to avoid rate limiting
            if idx > 0:
                time.sleep(0.2)
            
            with st.spinner(f"Loading {symbol}..."):
                price, change, error = fetch_current_quote(symbol)
            
            if error:
                st.error(f"❌ {error}")
            elif price and change:
                # Format price to 2 decimal places
                try:
                    price_float = float(price)
                    change_clean = change.replace('%', '').strip()
                    change_float = float(change_clean)
                    
                    st.markdown(f"**Price:** ${price_float:.2f}")
                    
                    # Color code the change
                    if change_float >= 0:
                        st.markdown(f"**Change:** <span style='color: green'>+{change}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**Change:** <span style='color: red'>{change}</span>", unsafe_allow_html=True)
                        
                except ValueError:
                    st.markdown(f"**Price:** ${price}")
                    st.markdown(f"**Change:** {change}")
            else:
                st.markdown("*Price data not available.*")

# Add footer with rate limit info
st.markdown("---")
st.info("ℹ️ **Rate Limits:** Alpha Vantage free tier allows 5 requests per minute and 500 per day. If prices aren't loading, you may have hit the rate limit.")