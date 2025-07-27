import streamlit as st
import requests
import time
from datetime import datetime, timedelta
import json

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

# Rate limiting configuration
DAILY_LIMIT = 500
MINUTE_LIMIT = 5
ACTIVE_START_HOUR = 6  # 6 AM
ACTIVE_END_HOUR = 21   # 9 PM
ACTIVE_HOURS = ACTIVE_END_HOUR - ACTIVE_START_HOUR  # 15 hours (6 AM to 9 PM)

def is_within_active_hours():
    """Check if current time is within active trading hours (6 AM - 9 PM)"""
    current_hour = datetime.now().hour
    return ACTIVE_START_HOUR <= current_hour < ACTIVE_END_HOUR

def get_daily_usage_key():
    """Get key for daily usage tracking"""
    return f"daily_usage_{datetime.now().strftime('%Y-%m-%d')}"

def get_minute_usage_key():
    """Get key for minute usage tracking"""
    return f"minute_usage_{datetime.now().strftime('%Y-%m-%d_%H:%M')}"

def check_rate_limits():
    """Check if we can make API requests without exceeding limits"""
    # First check if we're within active hours
    if not is_within_active_hours():
        return False
    
    daily_key = get_daily_usage_key()
    minute_key = get_minute_usage_key()
    
    daily_usage = st.session_state.get(daily_key, 0)
    minute_usage = st.session_state.get(minute_key, 0)
    
    return daily_usage < DAILY_LIMIT and minute_usage < MINUTE_LIMIT

def increment_usage():
    """Increment API usage counters"""
    daily_key = get_daily_usage_key()
    minute_key = get_minute_usage_key()
    
    st.session_state[daily_key] = st.session_state.get(daily_key, 0) + 1
    st.session_state[minute_key] = st.session_state.get(minute_key, 0) + 1

def get_optimal_refresh_interval():
    """Calculate optimal refresh interval based on active hours (6 AM - 9 PM)"""
    stocks_count = len(filtered)
    
    # Calculate how many times we can refresh all stocks during active hours (15 hours)
    max_refreshes_per_active_period = DAILY_LIMIT // stocks_count
    
    # Distribute refreshes evenly across 15 active hours (6 AM to 9 PM)
    active_seconds = ACTIVE_HOURS * 3600  # 15 hours in seconds
    
    if max_refreshes_per_active_period <= 1:
        return active_seconds  # Once per active period
    else:
        # Calculate interval to distribute refreshes evenly
        interval = active_seconds // max_refreshes_per_active_period
        # Minimum 10 minutes between refreshes to avoid over-refreshing
        return max(interval, 600)

# Calculate optimal caching duration
OPTIMAL_CACHE_TTL = get_optimal_refresh_interval()

@st.cache_data(ttl=OPTIMAL_CACHE_TTL)
def fetch_current_quote(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    
    try:
        # Check rate limits before making request
        if not check_rate_limits():
            if not is_within_active_hours():
                current_hour = datetime.now().hour
                if current_hour < ACTIVE_START_HOUR:
                    next_active = f"{ACTIVE_START_HOUR:02d}:00"
                    return None, None, f"Markets closed. Trading hours: 6 AM - 9 PM. Next open: {next_active}"
                else:
                    return None, None, f"Markets closed. Trading hours: 6 AM - 9 PM. Opens tomorrow at 6 AM"
            
            daily_usage = st.session_state.get(get_daily_usage_key(), 0)
            minute_usage = st.session_state.get(get_minute_usage_key(), 0)
            
            if daily_usage >= DAILY_LIMIT:
                return None, None, f"Daily limit reached ({daily_usage}/{DAILY_LIMIT}). Resets at midnight."
            if minute_usage >= MINUTE_LIMIT:
                return None, None, f"Minute limit reached ({minute_usage}/{MINUTE_LIMIT}). Wait 1 minute."
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        # Increment usage counter after successful request
        increment_usage()
        
        data = response.json()
        
        # Debug: Show raw response for troubleshooting
        if st.session_state.get('debug_mode', False):
            st.write(f"Debug - Raw response for {symbol}:", data)
        
        # Check for API error messages
        if "Error Message" in data:
            return None, None, data.get("Error Message", "Unknown error")
        
        if "Note" in data:
            return None, None, data.get("Note", "Rate limit or other issue")
        
        # Extract quote data
        quote_data = data.get("Global Quote", {})
        
        if not quote_data:
            return None, None, "No quote data found"
        
        price = quote_data.get("05. price")
        change_percent = quote_data.get("10. change percent")
        
        if price is None or change_percent is None:
            # Try alternative field names
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

# Display rate limit status and trading hours
st.sidebar.markdown("## 📊 API Usage Status")

# Show trading hours status
current_hour = datetime.now().hour
is_active = is_within_active_hours()

if is_active:
    st.sidebar.success(f"🟢 **MARKET OPEN** ({current_hour:02d}:00)")
    st.sidebar.write(f"**Trading Hours:** 6 AM - 9 PM")
else:
    if current_hour < ACTIVE_START_HOUR:
        next_open_time = f"Today at {ACTIVE_START_HOUR:02d}:00"
    else:
        next_open_time = f"Tomorrow at {ACTIVE_START_HOUR:02d}:00"
    st.sidebar.error(f"🔴 **MARKET CLOSED** ({current_hour:02d}:00)")
    st.sidebar.write(f"**Next Open:** {next_open_time}")

daily_usage = st.session_state.get(get_daily_usage_key(), 0)
minute_usage = st.session_state.get(get_minute_usage_key(), 0)

st.sidebar.progress(daily_usage / DAILY_LIMIT)
st.sidebar.write(f"**Daily:** {daily_usage}/{DAILY_LIMIT} requests")
st.sidebar.progress(minute_usage / MINUTE_LIMIT if minute_usage <= MINUTE_LIMIT else 1.0)
st.sidebar.write(f"**This Minute:** {minute_usage}/{MINUTE_LIMIT} requests")

# Show optimal refresh schedule
stocks_count = len(filtered)
max_refreshes = DAILY_LIMIT // stocks_count
st.sidebar.write(f"**Stocks:** {stocks_count}")
st.sidebar.write(f"**Max Refreshes (6AM-9PM):** {max_refreshes}")
st.sidebar.write(f"**Cache Duration:** {OPTIMAL_CACHE_TTL // 60} minutes")

# Reset usage button (for testing)
if st.sidebar.button("🔄 Reset Usage Counters"):
    for key in list(st.session_state.keys()):
        if key.startswith('daily_usage_') or key.startswith('minute_usage_'):
            del st.session_state[key]
    st.sidebar.success("Usage counters reset!")

# Add debug toggle
if st.checkbox("🔧 Debug Mode (Show API responses)"):
    st.session_state.debug_mode = True
else:
    st.session_state.debug_mode = False

# Smart refresh button - only if within limits and active hours
can_refresh = check_rate_limits() and is_within_active_hours()
remaining_daily = DAILY_LIMIT - daily_usage
remaining_stocks = remaining_daily // len(filtered) if remaining_daily > 0 else 0

if not is_within_active_hours():
    current_hour = datetime.now().hour
    if current_hour < ACTIVE_START_HOUR:
        st.warning(f"🕕 Markets closed. Trading starts at 6:00 AM")
    else:
        st.warning(f"🕘 Markets closed. Trading ended at 9:00 PM. Opens tomorrow at 6:00 AM")
elif can_refresh and remaining_stocks > 0:
    if st.button(f"🔄 Refresh All Prices ({remaining_stocks} refreshes left today)"):
        st.cache_data.clear()
        st.rerun()
else:
    st.warning(f"⚠️ Cannot refresh: Daily limit would be exceeded. {remaining_daily} requests remaining.")

# Load stocks with intelligent batching
if is_within_active_hours():
    st.write("📈 **Loading Stock Prices...**")
    
    # Show next refresh time
    next_refresh = datetime.now() + timedelta(seconds=OPTIMAL_CACHE_TTL)
    st.info(f"ℹ️ **Auto-refresh:** Every {OPTIMAL_CACHE_TTL // 60} minutes | Next refresh: {next_refresh.strftime('%H:%M')}")
else:
    current_hour = datetime.now().hour
    if current_hour < ACTIVE_START_HOUR:
        st.info(f"🕕 **Markets Open in:** {ACTIVE_START_HOUR - current_hour} hours (6:00 AM)")
    else:
        hours_until_open = (24 - current_hour) + ACTIVE_START_HOUR
        st.info(f"🕘 **Markets Open in:** {hours_until_open} hours (Tomorrow 6:00 AM)")
    st.write("📊 **Showing Last Available Prices**")

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
                st.write("🏢")
            
            st.markdown(f"### {symbol}")
            
            # Check if we can make this request
            if not is_within_active_hours():
                st.info("🕘 Markets closed")
                continue
            elif not check_rate_limits():
                st.warning("⚠️ Rate limit reached")
                continue
            
            # Add delay between requests to respect minute limits
            if idx > 0:
                time.sleep(12)  # 5 requests per minute = 12 second intervals
            
            with st.spinner(f"Loading {symbol}..."):
                price, change, error = fetch_current_quote(symbol)
            
            if error:
                st.error(f"❌ {error}")
            elif price and change:
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

# Footer with rate limit strategy
st.markdown("---")
st.info(f"""
🎯 **Smart Rate Limiting Strategy:**
- **Trading Hours:** 6:00 AM - 9:00 PM (15 hours active)
- **Daily Limit:** 500 requests distributed across trading hours only
- **Current Schedule:** Refresh every {OPTIMAL_CACHE_TTL // 60} minutes during market hours
- **Stocks per Refresh:** {len(filtered)} stocks
- **Daily Refreshes:** Up to {DAILY_LIMIT // len(filtered)} times (during trading hours)
- **Minute Limit:** Maximum 5 requests per minute with 12-second intervals
- **Inactive Hours:** No API calls made between 9 PM - 6 AM (saves quota)
""")