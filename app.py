import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# Page Setup
st.set_page_config(page_title="DCA Simulator", layout="wide", page_icon="📈")

# Custom CSS for clean metric cards
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.6rem; }
    .stMetric { 
        background-color: rgba(28, 131, 225, 0.05); 
        padding: 10px; 
        border-radius: 8px; 
        border: 1px solid rgba(28, 131, 225, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("The Dollar Cost Averaging (DCA) Simulator")

# --- SIDEBAR: USER CONTROLS ---
st.sidebar.header("Simulation Settings")
ticker_symbol = st.sidebar.text_input("Ticker (e.g., SPY, AAPL, MSFT)", value="SPY").upper()
invest_amount = st.sidebar.number_input("Amount per Interval ($)", value=100)

# --- DATE RANGE CONFIGURATION ---
today = datetime.now().date()
absolute_min = datetime(1980, 1, 1).date() 
default_start = datetime(2010, 1, 1).date()

st.sidebar.subheader("Simulation Dates")
start_date = st.sidebar.date_input("Start Date", value=default_start, min_value=absolute_min, max_value=today)

if "end_date_key" not in st.session_state:
    st.session_state["end_date_key"] = today

if st.sidebar.button("🕒 Reset End Date to Today"):
    st.session_state["end_date_key"] = today

end_date = st.sidebar.date_input("End Date", value=st.session_state["end_date_key"], key="end_date_key", min_value=start_date, max_value=today)

freq_options = {"Daily": "B", "Weekly": "W-MON", "Monthly": "MS"}
frequency = st.sidebar.selectbox("Investment Frequency", list(freq_options.keys()))

# --- DATA FETCHING ---
@st.cache_data(ttl=3600)
def load_data(symbol, start, end):
    try:
        df = yf.download(symbol, start=start, end=end, auto_adjust=True)
        return df['Close'] if not df.empty else None
    except:
        return None

prices = load_data(ticker_symbol, start_date, end_date)

if prices is not None and not prices.empty:
    if isinstance(prices, pd.DataFrame):
        prices = prices.iloc[:, 0]

    # --- MATH ENGINE ---
    buy_days = prices.resample(freq_options[frequency]).first().dropna()
    buy_prices = prices[prices.index.isin(buy_days.index)]
    
    total_intervals = len(buy_prices)
    total_invested = total_intervals * invest_amount
    shares_held = (invest_amount / buy_prices).sum()
    current_price = float(prices.iloc[-1])
    portfolio_value = shares_held * current_price
    avg_cost = total_invested / shares_held
    day_1_price = float(buy_prices.iloc[0])
    total_growth = ((portfolio_value / total_invested) - 1) * 100
    total_profit = portfolio_value - total_invested

    # --- MAIN DASHBOARD LAYOUT ---
    
    # 1. METRICS GRID (Top of screen)
    st.subheader("📊 Performance Summary")
    
    # Row 1
    m1, m2, m3 = st.columns(3)
    m1.metric("Current Market Price", f"${current_price:,.2f}")
    m2.metric("Total Invested", f"${total_invested:,.2f}")
    m3.metric("Current Portfolio Value", f"${portfolio_value:,.2f}")

    # Row 2
    m4, m5, m6 = st.columns(3)
    m4.metric("Total Shares Owned", f"{shares_held:.3f}")
    m5.metric("Average Cost/Share", f"${avg_cost:,.2f}")
    m6.metric("Total Growth", f"{total_growth:.2f}%", f"${total_profit:,.2f} Profit")

    st.divider()

    # 2. CHARTS & STORY (Side-by-side)
    col_chart, col_story = st.columns([2, 1])
    
    with col_chart:
        st.subheader("📈 Price History")
        st.line_chart(prices)
    
    with col_story:
        st.subheader("📝 Your Story")
        first_p = buy_prices.index[0].strftime('%b %Y')
        last_p = buy_prices.index[-1].strftime('%b %Y')
        
        st.info(f"""
        Starting in **{first_p}**, you invested **${invest_amount}** at regular intervals. 
        
        Over **{total_intervals}** contributions, you've seen the price move from an initial **${day_1_price:,.2f} to the current ${current_price:,.2f}**.
        """)
        
        # Education Snippet
        cost_diff = day_1_price - avg_cost
        if cost_diff > 0:
            st.success(f"**DCA Success:** Your average cost is **${cost_diff:,.2f} lower** than if you bought everything on Day 1.")
        else:
            st.warning("**Strong Uptrend:** Buying on Day 1 would have been cheaper, but DCA reduced your risk of timing a peak.")

else:
    st.error("No data found for this ticker and date range.")
