import os
from sentence_transformers import SentenceTransformer

def download():
    model_name = 'all-MiniLM-L6-v2'
    local_path = os.path.join(os.path.dirname(__file__), 'models', model_name)
    print(f"Downloading {model_name} and saving to {local_path}...")
    
    # Download and save
    model = SentenceTransformer(model_name)
    model.save(local_path)
    print("Model downloaded and saved successfully!")

if __name__ == '__main__':
    download()
