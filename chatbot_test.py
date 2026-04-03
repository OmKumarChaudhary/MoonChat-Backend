import sys
import os
sys.path.append(os.getcwd())
from chatbot.chat import get_response

test_queries = [
    "Who is the top gainer today?",     # New: Gainers
    "Show me the biggest losers",       # New: Losers
    "What is the price of Bitcoin?",    # Live Price
    "Highest price of Cardano ever?",   # Live ATH
    "Who created Ethereum?",            # Factual
    "What is DeFi?",                    # Definition
    "hi moonchat"                       # Greeting
]

print("--- MoonChat Performance & Accuracy Verification ---")
for query in test_queries:
    print(f"User: {query}")
    try:
        response = get_response(query)
        print(f"Bot:  {response}")
    except Exception as e:
        print(f"Bot Error: {e}")
    print("-" * 30)
