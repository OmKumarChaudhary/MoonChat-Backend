import time
from flask import Blueprint, jsonify, request
from pycoingecko import CoinGeckoAPI
from utils.cache_manager import cache_manager

# Create a Blueprint for crypto-related routes
crypto_bp = Blueprint('crypto', __name__)

# Initialize CoinGecko API client
cg = CoinGeckoAPI()

# Cache TTL constants (in seconds)
PRICES_TTL = 300  # 5 minutes
SEARCH_TTL = 3600 # 1 hour for search results

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
    Uses persistent caching to avoid rate limits and handle slow CPU environments.
    """
    cache_key = 'top_100_prices'
    
    # 1. Try to get fresh cached data
    cached_data = cache_manager.get(cache_key, ttl=PRICES_TTL)
    if cached_data:
        return jsonify(cached_data), 200

    try:
        # 2. Get live data from CoinGecko
        # Set a timeout context if possible, but CoinGeckoAPI doesn't direct support it easily here
        # We'll just handle the exception if it's too slow
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
        
        # 3. Save to persistent cache
        cache_manager.set(cache_key, formatted_data)
        return jsonify(formatted_data), 200
        
    except Exception as e:
        print(f"Error fetching live prices: {e}. Falling back to cache.")
        # 4. Fallback: Return whatever we have in cache, even if stale
        last_known_data = cache_manager.get_last_resort(cache_key)
        if last_known_data:
            return jsonify(last_known_data), 200
        return jsonify({'error': 'Service overloaded and no cached data available.'}), 503

@crypto_bp.route('/search', methods=['GET'])
def search_cryptos():
    """
    Searches for cryptocurrencies and fetches their real-time market data.
    Uses persistent caching with long TTL for search results.
    """
    query = request.args.get('query', '').lower().strip()
    if not query:
        return jsonify([])
    
    cache_key = f'search_{query}'
    
    # 1. Check cache first
    cached_results = cache_manager.get(cache_key, ttl=SEARCH_TTL)
    if cached_results:
        return jsonify(cached_results), 200

    try:
        # 2. Use CoinGecko's search endpoint to find matching coins
        search_results = cg.search(query=query)
        search_coins = search_results.get('coins', [])
        
        if not search_coins:
            return jsonify([])

        # 3. Extract IDs for the top search results
        coin_ids = [coin['id'] for coin in search_coins[:20]]
        
        # 4. Fetch real-time market data for these specific IDs
        market_data = cg.get_coins_markets(
            vs_currency='usd',
            ids=','.join(coin_ids),
            price_change_percentage='24h'
        )
        
        market_map = {item['id']: item for item in market_data}
        
        # 5. Format the final results
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
        
        # 6. Save to cache
        cache_manager.set(cache_key, formatted_results)
        return jsonify(formatted_results), 200
        
    except Exception as e:
        print(f"Error searching cryptos: {e}. Falling back to cache.")
        last_resort = cache_manager.get_last_resort(cache_key)
        if last_resort:
            return jsonify(last_resort), 200
        return jsonify({'error': str(e)}), 500
