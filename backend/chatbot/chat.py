import json
import numpy as np
from tensorflow.keras.models import load_model
import nltk
from nltk.stem import WordNetLemmatizer
import string
import pandas as pd
import os
from pycoingecko import CoinGeckoAPI

lemmatizer = WordNetLemmatizer()
cg = CoinGeckoAPI()

# Define paths relative to this script's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(BASE_DIR, "moonchat_model.h5")
words_path = os.path.join(BASE_DIR, "moonchat_words.json")
classes_path = os.path.join(BASE_DIR, "moonchat_classes.json")
data_path = os.path.join(BASE_DIR, "moonchat_data.csv")

# Load model and data
model = load_model(model_path)
words = json.load(open(words_path))
classes = json.load(open(classes_path))
df = pd.read_csv(data_path, encoding='latin-1')


def preprocess(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = nltk.word_tokenize(text)
    return [lemmatizer.lemmatize(token) for token in tokens]

def bow(text):
    tokenized = preprocess(text)
    bag = [1 if w in tokenized else 0 for w in words]
    return np.array(bag)

def predict_class(text):
    pred = model.predict(np.array([bow(text)]))[0]
    return classes[np.argmax(pred)]

def get_crypto_price(text):
    """Fetches real-time price for the mentioned coin."""
    text_clean = text.lower()
    coin_map = {
        'btc': 'bitcoin', 'bitcoin': 'bitcoin',
        'eth': 'ethereum', 'ethereum': 'ethereum', 'etherum': 'ethereum',
        'sol': 'solana', 'solana': 'solana',
        'doge': 'dogecoin', 'dogecoin': 'dogecoin',
        'ada': 'cardano', 'cardano': 'cardano',
        'xrp': 'ripple', 'ripple': 'ripple',
        'dot': 'polkadot', 'polkadot': 'polkadot',
        'bnb': 'binancecoin', 'binance coin': 'binancecoin',
        'ltc': 'litecoin', 'litecoin': 'litecoin',
        'ape': 'apecoin', 'apecoin': 'apecoin',
        'matic': 'matic-network', 'polygon': 'matic-network',
        'shib': 'shiba-inu', 'shiba inu': 'shiba-inu',
        'link': 'chainlink', 'chainlink': 'chainlink',
        'uni': 'uniswap', 'uniswap': 'uniswap',
        'near': 'near', 'near protocol': 'near',
        'atom': 'cosmos', 'cosmos': 'cosmos'
    }
    
    found_coin = None
    for key in coin_map:
        if key in text_clean:
            found_coin = coin_map[key]
            break
            
    # Dynamic search if not found in common map
    if not found_coin:
        try:
            # Extract potential coin name
            query = text_clean.replace("price", "").replace("what is", "").replace("how much is", "").replace("of", "").replace("the", "").strip()
            if query:
                search_results = cg.search(query=query)
                if search_results.get('coins'):
                    found_coin = search_results['coins'][0]['id']
        except Exception:
            pass

    if found_coin:
        try:
            price_data = cg.get_price(ids=found_coin, vs_currencies='usd')
            if found_coin in price_data:
                price = price_data[found_coin]['usd']
                return f"The current price of {found_coin.replace('-', ' ').capitalize()} is ${price:,.2f} USD."
        except Exception:
            return f"I found the coin '{found_coin}', but I couldn't fetch its live price right now."
    
    return "I can fetch real-time prices for almost any crypto! Try asking 'Price of Bitcoin' or 'How much is Solana?'"

def get_response(text):
    intent = predict_class(text)
    
    if intent == 'price':
        return get_crypto_price(text)
        
    responses = df[df['intent']==intent]['response'].values
    if len(responses) > 0:
        return responses[0]
    return "I'm not sure how to help with that yet, but I'm learning every day!"