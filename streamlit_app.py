import streamlit as st
import pandas as pd
import numpy as np
import datetime
import requests

st.set_page_config(page_title="Bollinger Dashboard", layout="wide")

st.title("📈 Crypto Bollinger Breakout Signals")

symbol_list = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "MATICUSDT", "DOTUSDT"
]

interval = "15m"
limit = 100

@st.cache_data(ttl=30)
def fetch_klines(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    try:
        data = response.json()
    except Exception as e:
        st.warning(f"Ошибка при получении данных по {symbol}: {e}")
        return pd.DataFrame()
    
    if isinstance(data, list):
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_vol", "taker_buy_quote_vol", "ignore"
        ])
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        df = df.astype(float)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df["close"] = df["close"].astype(float)
        return df

    return pd.DataFrame()
    
    if "result" in data and "list" in data["result"]:
        df = pd.DataFrame(data["result"]["list"], columns=[
            "timestamp", "open", "high", "low", "close", "volume", "_", "__", "___", "____", "_____"
        ])
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        df = df.astype(float)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df["close"] = df["close"].astype(float)
        return df

    return pd.DataFrame()
    if "result" in data and "list" in data["result"]:
        df = pd.DataFrame(data["result"]["list"], columns=[
            "timestamp", "open", "high", "low", "close", "volume", "_", "__", "___", "____", "_____"
        ])
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        df = df.astype(float)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df["close"] = df["close"].astype(float)
        return df
    return pd.DataFrame()

def bollinger_breakout(df, deviation):
    df["MA20"] = df["close"].rolling(window=20).mean()
    df["std"] = df["close"].rolling(window=20).std()
    df["upper"] = df["MA20"] + deviation * df["std"]
    df["lower"] = df["MA20"] - deviation * df["std"]

    last_candle = df.iloc[-1]
    if last_candle["close"] > last_candle["upper"]:
        return "🔺 Breakout ↑"
    elif last_candle["close"] < last_candle["lower"]:
        return "🔻 Breakout ↓"
    else:
        return ""

st.sidebar.title("⚙️ Настройки")
deviation = st.sidebar.select_slider("Отклонение от линии", options=[
    0.5, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2, 2.3, 2.4, 2.6, 2.8, 3, 3.3, 3.5,
    3.8, 4, 4.2, 4.4, 4.6, 4.8, 5, 5.5
], value=2)

st.sidebar.markdown("🕒 Обновление каждые 30 секунд")

st.write(f"**Отклонение**: {deviation}")

data = []
for symbol in symbol_list:
    df = fetch_klines(symbol)
    if df.empty:
        continue
    signal = bollinger_breakout(df, deviation)
    last_close = df["close"].iloc[-1]
    data.append({
        "Пара": symbol,
        "Цена": round(last_close, 4),
        "Сигнал": signal
    })

df_signals = pd.DataFrame(data)
df_signals = df_signals[df_signals["Сигнал"] != ""]

if df_signals.empty:
    st.info("Нет пробоя по текущим монетам.")
else:
    st.success("Обнаружены сигналы!")
    st.dataframe(df_signals, use_container_width=True)
