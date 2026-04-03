import os
import json
import random
import pickle
import sys
import numpy as np
from tensorflow.keras.models import load_model
from pycoingecko import CoinGeckoAPI

# -------------------- Add Project Root to Path --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Import custom package utilities
try:
    from chatbot.nlp_utils import preprocess_text, extract_entities
except ImportError:
    from nlp_utils import preprocess_text, extract_entities

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cg = CoinGeckoAPI()

# -------------------- Load Model & Metadata --------------------
model = load_model(os.path.join(BASE_DIR, 'moonchat_model.keras'))
with open(os.path.join(BASE_DIR, 'moonchat_vectorizer.pkl'), 'rb') as f:
    vectorizer = pickle.load(f)
with open(os.path.join(BASE_DIR, 'moonchat_classes.json'), 'r') as f:
    classes = json.load(f)

# Internal name to CoinGecko ID mapping
CG_MAP = {
    'bitcoin': 'bitcoin',
    'ethereum': 'ethereum',
    'cardano': 'cardano',
    'solana': 'solana',
    'dogecoin': 'dogecoin',
    'litecoin': 'litecoin',
    'xrp': 'ripple'
}

def get_live_data(coin_name):
    """Fetch live price, ATH, ATL from CoinGecko."""
    coin_id = CG_MAP.get(coin_name.lower())
    if not coin_id: return None
    try:
        data = cg.get_coin_by_id(id=coin_id, localization=False, tickers=False, market_data=True, community_data=False, developer_data=False, sparkline=False)
        m_data = data['market_data']
        return {
            'name': data['name'],
            'price': m_data['current_price']['usd'],
            'ath': m_data['ath']['usd'],
            'atl': m_data['atl']['usd'],
            'mcap': m_data['market_cap']['usd'],
            'change_24h': m_data['price_change_percentage_24h']
        }
    except Exception: return None

def get_performance_data(perf_type='gainers'):
    """Fetch top gainers or losers."""
    try:
        markets = cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=100, page=1)
        markets = [m for m in markets if m.get('price_change_percentage_24h') is not None]
        if perf_type == 'gainers':
            sorted_list = sorted(markets, key=lambda x: x['price_change_percentage_24h'], reverse=True)
            title = "🚀 Top 5 Gainers (24h)"
        else:
            sorted_list = sorted(markets, key=lambda x: x['price_change_percentage_24h'], reverse=False)
            title = "📉 Top 5 Losers (24h)"
        response = f"{title}:\n"
        for i, coin in enumerate(sorted_list[:5], 1):
            response += f"{i}. {coin['name']} ({coin['symbol'].upper()}): {coin['price_change_percentage_24h']:+.2f}%\n"
        return response
    except Exception: return "Market data currently unavailable."

# Load response pools
responses = {}
try:
    import pandas as pd
    data_path = os.path.join(BASE_DIR, 'moonchat_data_final.csv')
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        for intent in df['intent'].unique():
            responses[intent] = df[df['intent'] == intent]['response'].unique().tolist()
except Exception: responses = {}

def get_response(msg):
    entities = extract_entities(msg)
    cleaned_msg = preprocess_text(msg)
    X = vectorizer.transform([cleaned_msg]).toarray()
    results = model.predict(X)[0]
    
    # Get top 2 predictions for "Did you mean?" logic
    top_indices = np.argsort(results)[-2:][::-1]
    intent = classes[top_indices[0]]
    confidence = results[top_indices[0]]
    
    print(f"[MoonChat] Intent: {intent} ({confidence:.2f}), Next: {classes[top_indices[1]]} ({results[top_indices[1]]:.2f})")

    # 1. Very Low Confidence Fallback (< 0.20)
    if confidence < 0.20:
        return "I'm not sure what you mean. I can help with crypto prices, founders, gainers/losers, or definitions! Try 'price of BTC'."

    # 2. "Did you mean?" Logic (0.20 - 0.45)
    if confidence < 0.45:
        alt_intent = classes[top_indices[1]]
        return f"I think you're asking about **{intent.replace('_', ' ')}**, but I'm not 100% sure. Did you mean to ask about **{alt_intent.replace('_', ' ')}** instead?"

    # 3. Handle Performance Data
    if intent == 'gainers': return get_performance_data('gainers')
    if intent == 'losers': return get_performance_data('losers')

    # 4. Handle Real-Time Price/ATH/ATL
    if intent in ['price', 'ath', 'atl'] or any(t in ['ath', 'atl', 'high', 'low'] for t in entities['terms']):
        if entities['coins']:
            coin = entities['coins'][0]
            data = get_live_data(coin)
            if data:
                if 'ath' in cleaned_msg or 'high' in cleaned_msg or intent == 'ath':
                    return f"The All-Time High (ATH) for {data['name']} is ${data['ath']:,}. Currently: ${data['price']:,}."
                if 'atl' in cleaned_msg or 'low' in cleaned_msg or intent == 'atl':
                    return f"The All-Time Low (ATL) for {data['name']} is ${data['atl']:,}. Currently: ${data['price']:,}."
                return f"Symbol: {coin.upper()}\nPrice: ${data['price']:,} USD\n24h Change: {data['change_24h']:.2f}%\nMarket Cap: ${data['mcap']:,}"
        if intent == 'price': return "Which cryptocurrency price? E.g., 'price of Bitcoin'."

    # 5. Handle Strict Factual Intents
    if intent in ['founder', 'year', 'definition', 'trend']:
        all_detected = entities['coins'] + entities['terms']
        if all_detected:
            pool = responses.get(intent, [])
            matched = [r for r in pool if any(ent.lower() in r.lower() for ent in all_detected)]
            if matched: return random.choice(matched)
            return f"I don't have the {intent} for {all_detected[0]} yet."
        return f"Which cryptocurrency for {intent}? I know about Bitcoin, Ethereum, Cardano, etc."

    # 6. Default Pooled Responses
    pool = responses.get(intent, ["I'm here to help with crypto! Ask me anything."])
    return random.choice(pool)