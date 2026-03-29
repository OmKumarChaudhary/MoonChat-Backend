import nltk
import os

def setup():
    # Define local path for NLTK data to ensure it's kept with the project on Render
    base_dir = os.path.dirname(os.path.abspath(__file__))
    nltk_data_path = os.path.join(base_dir, 'nltk_data')
    
    if not os.path.exists(nltk_data_path):
        os.makedirs(nltk_data_path)
        
    print(f"Downloading NLTK data to {nltk_data_path}...")
    nltk.download('punkt', download_dir=nltk_data_path)
    nltk.download('punkt_tab', download_dir=nltk_data_path)
    nltk.download('wordnet', download_dir=nltk_data_path)
    nltk.download('omw-1.4', download_dir=nltk_data_path)
    print("NLTK data downloaded successfully.")

if __name__ == "__main__":
    setup()
