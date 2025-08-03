import streamlit as st
import pandas as pd
import numpy as np
import requests
import time

st.set_page_config(page_title="Bollinger Dashboard", layout="wide")
st.title("📈 Crypto Bollinger Breakout Signals")

symbol_list = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "MATICUSDT", "DOTUSDT"
]

# Соответствие Binance → CoinGecko
coingecko_ids = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum",
    "SOLUSDT": "solana",
    "BNBUSDT": "binancecoin",
    "XRPUSDT": "ripple",
    "DOGEUSDT": "dogecoin",
    "ADAUSDT": "cardano",
    "AVAXUSDT": "avalanche-2",
    "LINKUSDT": "chainlink",
    "MATICUSDT": "matic-network",
    "DOTUSDT": "polkadot"
}

@st.cache_data(ttl=60)
def fetch_klines(symbol):
    coin_id = coingecko_ids.get(symbol)
    if not coin_id:
        st.warning(f"⚠️ Неизвестный символ: {symbol}")
        return None

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=1&interval=hourly"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        prices = data["prices"]  # [[timestamp, price], ...]
        df = pd.DataFrame(prices, columns=["timestamp", "close"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        df["close"] = df["close"].astype(float)
        df["open"] = df["close"].shift(1)
        df["high"] = df["close"].rolling(2).max()
        df["low"] = df["close"].rolling(2).min()
        df["volume"] = 0  # нет данных о volume

        df.dropna(inplace=True)

        return df[["open", "high", "low", "close", "volume"]]

    except Exception as e:
        st.error(f"❌ Ошибка при получении {symbol} с CoinGecko: {e}")
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

st.sidebar.markdown("🕒 Обновление каждые 60 секунд")
st.write(f"**Отклонение**: {deviation}")

signals = []

for symbol in symbol_list:
    df = fetch_klines(symbol)
    time.sleep(1)  # соблюдение лимита CoinGecko

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

if df_signals.empty or "Сигнал" not in df_signals.columns:
    st.info("❕ Не удалось получить сигналы или нет пробоев.")
else:
    df_signals = df_signals[df_signals["Сигнал"] != ""]
    if df_signals.empty:
        st.info("❕ Нет сигналов на пробой.")
    else:
        st.success("✅ Обнаружены сигналы!")
        st.dataframe(df_signals, use_container_width=True)
