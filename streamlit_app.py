import streamlit as st
import pandas as pd
import numpy as np
import datetime
import time
import requests

st.set_page_config(page_title="Bollinger Dashboard", layout="wide")
st.title("📈 Crypto Bollinger Breakout Signals")

symbol_list = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "MATICUSDT", "DOTUSDT"
]

interval = "15"  # в минутах
limit = 100

@st.cache_data(ttl=30)
def fetch_klines(symbol):
    now = int(time.time())
    from_time = now - int(limit) * int(interval) * 60

    url = f"https://api.bybit.com/v2/public/kline/list?symbol={symbol}&interval={interval}&limit={limit}&from={from_time}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if "result" in data and "data" in data["result"] or "result" in data and isinstance(data["result"], list):
            candles = data["result"]["data"] if "data" in data["result"] else data["result"]
            df = pd.DataFrame(candles)
            df["open_time"] = pd.to_datetime(df["open_time"], unit="s")
            df.set_index("open_time", inplace=True)
            df["close"] = df["close"].astype(float)
            return df
        else:
            raise ValueError("Пустой ответ")
    except Exception as e:
        st.warning(f"Ошибка при получении {symbol}: {e}")
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
    st.info("Не удалось получить данные ни по одной паре или нет сигналов.")
else:
    st.success("Обнаружены сигналы!")
    st.dataframe(df_signals, use_container_width=True)
