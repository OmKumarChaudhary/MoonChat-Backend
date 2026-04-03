import re
import string
import os
import nltk
from nltk.stem import WordNetLemmatizer

# Ensure NLTK data is available in a specific directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
NLTK_DATA_PATH = os.path.join(PROJECT_ROOT, 'nltk_data')

if NLTK_DATA_PATH not in nltk.data.path:
    nltk.data.path.append(NLTK_DATA_PATH)

try:
    nltk.data.find('corpora/wordnet', paths=[NLTK_DATA_PATH])
except LookupError:
    os.makedirs(NLTK_DATA_PATH, exist_ok=True)
    nltk.download('wordnet', download_dir=NLTK_DATA_PATH)
    nltk.download('omw-1.4', download_dir=NLTK_DATA_PATH)

lemmatizer = WordNetLemmatizer()

# Noise words (Stop Words) to filter out for better keyword focus
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "until", "while",
    "of", "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out",
    "on", "off", "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", "d", "ll",
    "m", "o", "re", "ve", "y", "ain", "aren", "couldn", "didn", "doesn", "hadn",
    "hasn", "haven", "isn", "ma", "mightn", "mustn", "needn", "shan", "shouldn",
    "wasn", "weren", "won", "wouldn", "tell", "show", "give", "please", "me", "i",
    "you", "he", "she", "it", "we", "they", "them", "us", "him", "her", "my", "your",
    "his", "its", "our", "their", "mine", "yours", "hers", "ours", "theirs", "do",
    "does", "did", "doing", "be", "is", "am", "are", "was", "were", "been", "being",
    "have", "has", "had", "having", "who", "whom", "this", "that", "these", "those"
}

CONTRACTIONS = {
    "what's": "what is", "it's": "it is", "i'm": "i am",
    "he's": "he is", "she's": "she is", "we're": "we are",
    "they're": "they are", "you're": "you are", "that's": "that is",
    "there's": "there is", "here's": "here is", "who's": "who is",
    "how's": "how is", "where's": "where is", "when's": "when is",
    "why's": "why is", "let's": "let us", "can't": "cannot",
    "won't": "will not", "don't": "do not", "doesn't": "does not",
    "didn't": "did not", "isn't": "is not", "aren't": "are not",
    "wasn't": "was not", "weren't": "were not", "haven't": "have not",
    "hasn't": "has not", "hadn't": "had not", "wouldn't": "would not",
    "couldn't": "could not", "shouldn't": "should not",
    "ive": "i have", "youve": "you have", "weve": "we have", "theyve": "they have",
    "ill": "i will", "youll": "you will", "theyll": "they will",
    "thats": "that is", "heres": "here is", "theres": "there is",
    "whats": "what is", "hows": "how is", "whos": "who is", "wheres": "where is",
    "im": "i am", "dont": "do not", "doesnt": "does not", "didnt": "did not",
    "btcion": "bitcoin", "bitocin": "bitcoin", "bitcoing": "bitcoin",
    "ethereuem": "ethereum", "ethereim": "ethereum", "eth": "ethereum",
    "sol": "solana", "ada": "cardano", "doge": "dogecoin", "ltc": "litecoin",
    "crypto": "cryptocurrency"
}

COIN_SYMBOLS = {
    'btc': 'bitcoin', 'eth': 'ethereum', 'ada': 'cardano',
    'sol': 'solana', 'doge': 'dogecoin', 'ltc': 'litecoin', 'xrp': 'xrp'
}

def expand_contractions(text):
    words = text.split()
    expanded = [CONTRACTIONS.get(word, word) for word in words]
    return ' '.join(expanded)

def preprocess_text(text):
    """Clean, lemmatize and filter text for high-accuracy NLP tasks."""
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = expand_contractions(text)
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Tokenization
    tokens = text.split()
    # Filter STOP words & Lemmatization
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t not in STOP_WORDS]
    return ' '.join(tokens)

def extract_entities(text):
    """Find specific coins or terms mentioned in text with strict matching."""
    text = f" {text.lower()} "
    entities = {'coins': [], 'terms': []}
    COIN_LIST = ['bitcoin', 'ethereum', 'cardano', 'solana', 'dogecoin', 'litecoin', 'xrp']
    TERM_LIST = ['blockchain', 'defi', 'nft', 'market cap', 'ath', 'atl', 'high', 'low']
    
    for coin in COIN_LIST:
        if re.search(rf'\b{coin}\b', text):
            entities['coins'].append(coin)
    for symbol, full_name in COIN_SYMBOLS.items():
        if re.search(rf'\b{symbol}\b', text) and full_name not in entities['coins']:
            entities['coins'].append(full_name)
    for term in TERM_LIST:
        if re.search(rf'\b{term}\b', text):
            entities['terms'].append(term)
    return entities
