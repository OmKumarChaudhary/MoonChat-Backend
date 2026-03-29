import time
from flask import Blueprint, jsonify, request
from pycoingecko import CoinGeckoAPI

# Create a Blueprint for crypto-related routes
crypto_bp = Blueprint('crypto', __name__)

# Initialize CoinGecko API client
cg = CoinGeckoAPI()

# Simple In-Memory Cache
class CryptoCache:
    def __init__(self):
        self._data = {}

    def get(self, key):
        entry = self._data.get(key)
        if entry:
            # Check if the data is still fresh (e.g., within 2 minutes)
            if time.time() - entry['timestamp'] < 120:  # 120 seconds TTL
                return entry['value']
        return None

    def set(self, key, value):
        self._data[key] = {
            'value': value,
            'timestamp': time.time()
        }

# Global cache instance
price_cache = CryptoCache()
search_cache = CryptoCache()

@crypto_bp.route('/', methods=['GET'])
def crypto_root():
    """Status check for the crypto API."""
    return jsonify({
        'status': 'online',
        'message': 'MoonChat Crypto API is active',
        'endpoints': {
            'prices': '/api/crypto/prices',
            'search': '/api/crypto/search?query={coin}'
        }
    }), 200

@crypto_bp.route('/prices', methods=['GET'])
def get_crypto_prices():
    """
    Fetches the top 100 cryptocurrencies by market cap with their current prices and 24h changes.
    Uses caching to avoid rate limits and improve performance.
    """
    # Check cache first
    cached_data = price_cache.get('top_100_prices')
    if cached_data:
        return jsonify(cached_data), 200

    try:
        # Get live data from CoinGecko
        data = cg.get_coins_markets(
            vs_currency='usd',
            order='market_cap_desc',
            per_page=100,
            page=1,
            price_change_percentage='24h'
        )
        
        formatted_data = []
        for coin in data:
            formatted_data.append({
                'id': coin['id'],
                'symbol': coin['symbol'].upper(),
                'name': coin['name'],
                'image': coin['image'],
                'current_price': coin['current_price'],
                'price_change_percentage_24h': coin.get('price_change_percentage_24h', 0),
                'market_cap': coin.get('market_cap', 0)
            })
        
        # Save to cache
        price_cache.set('top_100_prices', formatted_data)
        return jsonify(formatted_data), 200
    except Exception as e:
        print(f"Error fetching crypto prices: {e}")
        return jsonify({'error': str(e)}), 500

@crypto_bp.route('/search', methods=['GET'])
def search_cryptos():
    """
    Searches for cryptocurrencies and fetches their real-time market data.
    Uses caching to improve performance for frequent searches.
    """
    query = request.args.get('query', '').lower().strip()
    if not query:
        return jsonify([])
    
    # Check cache for this specific query
    cached_results = search_cache.get(f'search_{query}')
    if cached_results:
        return jsonify(cached_results), 200

    try:
        # 1. Use CoinGecko's search endpoint to find matching coins
        search_results = cg.search(query=query)
        search_coins = search_results.get('coins', [])
        
        if not search_coins:
            return jsonify([])

        # 2. Extract IDs for the top search results
        coin_ids = [coin['id'] for coin in search_coins[:20]]
        
        # 3. Fetch real-time market data for these specific IDs
        market_data = cg.get_coins_markets(
            vs_currency='usd',
            ids=','.join(coin_ids),
            price_change_percentage='24h'
        )
        
        market_map = {item['id']: item for item in market_data}
        
        # 4. Format the final results
        formatted_results = []
        for coin in search_coins[:20]:
            market_info = market_map.get(coin['id'])
            
            formatted_results.append({
                'id': coin['id'],
                'symbol': coin['symbol'].upper(),
                'name': coin['name'],
                'image': market_info['image'] if market_info else coin['large'],
                'current_price': market_info['current_price'] if market_info else 0,
                'price_change_percentage_24h': market_info.get('price_change_percentage_24h', 0) if market_info else 0,
                'market_cap': market_info.get('market_cap', 0) if market_info else 0
            })
        
        # Save to cache
        search_cache.set(f'search_{query}', formatted_results)
        return jsonify(formatted_results), 200
    except Exception as e:
        print(f"Error searching cryptos with prices: {e}")
        return jsonify({'error': str(e)}), 500
