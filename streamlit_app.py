import streamlit as st
import pandas as pd
import numpy as np
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
def fetch_klines_binance(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume", "close_time",
            "quote_asset_volume", "number_of_trades", "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        df = df.astype(float)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df
    except Exception as e:
        st.error(f"❌ Ошибка при получении {symbol}: {e}")
        return None

def bollinger_breakout(df, deviation):
    df["MA20"] = df["close"].rolling(window=20).mean()
    df["std"] = df["close"].rolling(window=20).std()
    df["upper"] = df["MA20"] + deviation * df["std"]
    df["lower"] = df["MA20"] - deviation * df["std"]

    last = df.iloc[-1]
    if last["close"] > last["upper"]:
        return "🔺 Breakout ↑"
    elif last["close"] < last["lower"]:
        return "🔻 Breakout ↓"
    else:
        return ""

st.sidebar.title("⚙️ Настройки")
deviation = st.sidebar.select_slider(
    "Отклонение от линии", 
    options=[round(x * 0.2, 1) for x in range(3, 26)],
    value=2.0
)

st.sidebar.markdown("🕒 Обновление каждые 30 секунд")
st.write(f"**Отклонение**: {deviation}")

signals = []

for symbol in symbol_list:
    df = fetch_klines_binance(symbol)
    if df is None or df.empty:
        continue

    signal = bollinger_breakout(df, deviation)
    last_price = df["close"].iloc[-1]
    signals.append({
        "Пара": symbol,
        "Цена": round(last_price, 4),
        "Сигнал": signal
    })

df_signals = pd.DataFrame(signals)
df_signals = df_signals[df_signals["Сигнал"] != ""]

if df_signals.empty:
    st.info("❕ Не удалось получить сигналы или нет пробоев.")
else:
    st.success("✅ Обнаружены сигналы!")
    st.dataframe(df_signals, use_container_width=True)
