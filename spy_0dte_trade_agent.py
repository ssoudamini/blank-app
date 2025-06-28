# spy_0dte_trade_agent.py

import streamlit as st
import openai
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---- CONFIGURATION ---- #
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)
sheet = client.open("SPY_0DTE_Trade_Journal").sheet1

# ---- STREAMLIT UI ---- #
st.title("📈 SPY 0DTE Trade Logger")

st.markdown("""
Log your 0DTE SPY options trade here. The agent will calculate P&L and auto-tag trade setups using OpenAI.
""")

date = st.date_input("Trade Date", value=datetime.date.today())
market_bias = st.selectbox("Market Bias", ["Bullish", "Bearish", "Neutral"])
spy_open = st.number_input("SPY Opening Price", step=0.01)
premarket_high = st.number_input("Premarket High", step=0.01)
premarket_low = st.number_input("Premarket Low", step=0.01)
entry_time = st.time_input("Entry Time")
entry_option = st.selectbox("Option Type", ["Call", "Put"])
strike_price = st.number_input("Strike Price", step=1.0)
entry_price = st.number_input("Entry Price ($)", step=0.01)
exit_time = st.time_input("Exit Time")
exit_price = st.number_input("Exit Price ($)", step=0.01)
exit_reason = st.selectbox("Exit Reason", ["Target", "Stop", "Manual"])
spy_move = st.number_input("SPY % Move After Entry", step=0.01)
user_notes = st.text_area("Trade Notes")

if st.button("Log Trade"):
    # ---- CALCULATE P&L ---- #
    pnl_dollars = round((exit_price - entry_price) * 100, 2)
    pnl_percent = round(((exit_price / entry_price) - 1) * 100, 2) if entry_price else 0

    # ---- GPT TAGGING ---- #
    prompt = f"""
Given this trade: {entry_option} on SPY, Entry ${entry_price} at {entry_time}, Exit ${exit_price} at {exit_time},
notes: {user_notes}, SPY open: {spy_open}, strike: {strike_price}, market bias: {market_bias},
automatically summarize the setup (e.g., VWAP breakout, reversal, FOMO, etc.).
"""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    setup_summary = response.choices[0].message.content.strip()

    # ---- APPEND TO SHEET ---- #
    row = [str(date), market_bias, spy_open, f"{premarket_high}/{premarket_low}", str(entry_time),
           entry_option, strike_price, entry_price, str(exit_time), exit_price, exit_reason,
           pnl_dollars, pnl_percent, spy_move, user_notes, setup_summary]

    sheet.append_row(row)

    st.success(f"Trade logged successfully with setup: {setup_summary}")
