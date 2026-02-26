

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page Setup
st.set_page_config(page_title="DCA Simulator", layout="wide")

st.title("The Dollar Cost Averaging (DCA) Simulator")
st.markdown("### *Analyzing Market Cycles from 1980 to Present*")

# --- SIDEBAR: USER CONTROLS ---
st.sidebar.header("Simulation Settings")
ticker_symbol = st.sidebar.text_input("Ticker (e.g., SPY, AAPL, MSFT)", value="SPY").upper()
invest_amount = st.sidebar.number_input("Amount per Interval ($)", value=100)

# --- DATE RANGE CONFIGURATION ---
today = datetime.now().date()
absolute_min = datetime(1980, 1, 1).date() 
default_start = datetime(2010, 1, 1).date()

st.sidebar.subheader("Simulation Dates")

# Start Date
start_date = st.sidebar.date_input(
    "Start Date", 
    value=default_start, 
    min_value=absolute_min,
    max_value=today
)

# Reset End Date Button
if st.sidebar.button("🕒 Reset End Date to Today"):
    st.session_state["end_date_key"] = today

# End Date Input (Linked to Session State)
end_date = st.sidebar.date_input(
    "End Date", 
    value=st.session_state.get("end_date_key", today), 
    key="end_date_key",
    min_value=start_date,
    max_value=today
)

freq_options = {"Daily": "B", "Weekly": "W-MON", "Monthly": "MS"}
frequency = st.sidebar.selectbox("Investment Frequency", list(freq_options.keys()))

# --- DATA FETCHING ---
@st.cache_data
def load_data(symbol, start, end):
    try:
        # auto_adjust handles stock splits (crucial for 1980s data like AAPL)
        df = yf.download(symbol, start=start, end=end, auto_adjust=True)
        return df['Close'] if not df.empty else None
    except:
        return None

prices = load_data(ticker_symbol, start_date, end_date)

if prices is not None:
    if isinstance(prices, pd.DataFrame):
        prices = prices.iloc[:, 0]

    # --- MATH ENGINE ---
    # Resample filters the data to only the days an investment was made
    buy_days = prices.resample(freq_options[frequency]).first().dropna()
    buy_prices = prices[prices.index.isin(buy_days.index)]
    
    # Financial Stats
    total_intervals = len(buy_prices)
    total_invested = total_intervals * invest_amount
    shares_held = (invest_amount / buy_prices).sum()
    current_price = float(prices.iloc[-1])
    portfolio_value = shares_held * current_price
    avg_cost = total_invested / shares_held
    
    # Using the first actual purchase price as the "Day 1" benchmark
    day_1_price = float(buy_prices.iloc[0])
    
    total_growth = ((portfolio_value / total_invested) - 1) * 100
    total_profit = portfolio_value - total_invested

    # --- SECTION 1: THE INVESTOR STORY ---
    st.header("📝 Your Investment Story")
    first_purchase = buy_prices.index[0].strftime('%B %d, %Y')
    last_purchase = buy_prices.index[-1].strftime('%B %d, %Y')
    
    # Fixed spelling mapping (Dictionary approach)
    freq_map = {"Daily": "day", "Weekly": "week", "Monthly": "month"}
    display_freq = freq_map.get(frequency, "interval")
    
    # Duration calculation
    duration_years = round((buy_prices.index[-1] - buy_prices.index[0]).days / 365.25, 1)
    
    st.write(f"""
    On **{first_purchase}**, you began an investment journey with **{ticker_symbol}**. 
    By contributing **${invest_amount:,.2f}** every **{display_freq}**, you built your position 
    consistently for **{duration_years} years**.
    
    In total, you followed through with **{total_intervals} individual investments**. 
    Whether the market was up or down, you remained disciplined until your final purchase on **{last_purchase}**.
    """)

    # --- SECTION 2: THE FINANCIAL BREAKDOWN ---
    st.subheader("📊 Key Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Money Spent", f"${total_invested:,.2f}")
    col2.metric("Total Shares Owned", f"{shares_held:.3f}")
    col3.metric("Current Portfolio Value", f"${portfolio_value:,.2f}")
    col4.metric("Total Growth (%)", f"{total_growth:.2f}%", f"${total_profit:,.2f} Profit")

    st.divider()

    # --- SECTION 3: THE DCA ANALYSIS ---
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📈 Historical Price Action")
        st.line_chart(prices)
    
    with c2:
        st.subheader("💡 Educational Context")
        st.write("**The 'Averaging' Effect:**")
        st.metric("Your Average Cost", f"${avg_cost:,.2f}")
        st.metric("Price on Your First Day", f"${day_1_price:,.2f}")
        
        cost_savings = day_1_price - avg_cost
        if cost_savings > 0:
            st.success(f"DCA reduced your cost by **${cost_savings:,.2f}** per share compared to a Day 1 Lump Sum!")
        else:
            st.info("Because the market trended up consistently, your initial purchase was actually your cheapest entry.")

    # --- SECTION 4: RECESSION MARKERS ---
    st.subheader("🌪️ Historical Resilience")
    major_events = [
        ("1987 Black Monday", "1987-10-19", "1987-10-20"),
        ("Dot-Com Bubble Burst", "2000-03-10", "2002-10-09"),
        ("2008 Financial Crisis", "2007-10-09", "2009-03-09"),
        ("2020 COVID-19 Crash", "2020-02-19", "2020-03-23")
    ]
    
    # Check which events overlap with the user's investment period
    active_events = [e for e, s, end in major_events if buy_prices.index[0] < pd.to_datetime(s) < prices.index[-1]]
    
    if active_events:
        st.write("You stayed the course through these significant market downturns:")
        for event in active_events:
            st.warning(f"⚠️ **{event}:** Your DCA plan kept buying while others were fearful, capturing shares at lower prices.")
    else:
        st.write("Your selected timeframe didn't include a major historic crash, but DCA is still your best defense for when the next one arrives.")

else:
    st.error("No data found. Check your ticker or date range. (Note: Many crypto tickers don't go back to the 80s!)")
