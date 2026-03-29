import nltk

def setup():
    print("Downloading NLTK data...")
    nltk.download('punkt')
    nltk.download('punkt_tab')
    nltk.download('wordnet')
    nltk.download('omw-1.4')
    print("NLTK data downloaded successfully.")

if __name__ == "__main__":
    setup()
