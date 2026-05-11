import os
import sys
import json
import hashlib
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader, CSVLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Add root directory to sys.path to resolve internal modules
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from use_cases.vector_agent.src.vector_engine import VectorEngine

STATE_FILE = os.path.join(os.path.dirname(__file__), 'ingestion_state.json')

def get_file_hash(file_path: str) -> str:
    """Calculates the MD5 hash of a file to detect if its content has changed."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_state() -> dict:
    """Loads the ingestion state tracking dictionary."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    """Saves the ingestion state tracking dictionary."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)


def sanitize_metadata(metadata: dict) -> dict:
    """Ensures metadata only contains types supported by ChromaDB (str, int, float, bool)."""
    sanitized = {}
    for key, value in metadata.items():
        if value is None:
            continue  # Drop null values
        if isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        else:
            sanitized[key] = str(value) # Cast complex objects (like lists) to string
    return sanitized


def process_file(file_path: str, collection_name: str, engine: VectorEngine) -> bool:
    """Loads, chunks, and ingests a document into ChromaDB in batches."""
    file_name = os.path.basename(file_path)
    print(f"\nProcessing file: {file_name}")
    
    # Delete previous vectors, prevents duplication if a file was modified.
    delete_msg = engine.delete_by_source(collection_name=collection_name, source_name=file_name)
    print(f"-> Cleanup: {delete_msg}")

    # Select loader
    if file_path.endswith('.pdf'):
        loader = PyMuPDFLoader(file_path)
    elif file_path.endswith('.csv'):
        loader = CSVLoader(file_path, encoding='utf-8')
    elif file_path.endswith('.txt'):
        loader = TextLoader(file_path, encoding='utf-8')
    else:
        print(f"Unsupported file type: {file_name}")
        return False

    # Load and split
    try:
        raw_documents = loader.load()
    except Exception as e:
        print(f"-> Error reading {file_name}: {e}")
        return False
        
    print(f"-> Extracted {len(raw_documents)} raw pages/rows.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "]
    )
    
    chunked_docs = text_splitter.split_documents(raw_documents)
    print(f"-> Split into {len(chunked_docs)} manageable chunks.")

    # Metadata standardization
    texts = [doc.page_content for doc in chunked_docs]
    metadatas = []
    
    for doc in chunked_docs:
        meta = doc.metadata.copy() 
        meta["source"] = file_name
        metadatas.append(sanitize_metadata(meta))
    
    # Batch ingestion
    batch_size = 50
    print(f"-> Sending to Azure and ChromaDB in batches of {batch_size}...")
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_metadatas = metadatas[i:i + batch_size]
        
        print(f"    Uploading batch {i//batch_size + 1} (Chunks {i} to {min(i + batch_size, len(texts))})...")
        try:
            engine.add_documents(texts=batch_texts, collection_name=collection_name, metadatas=batch_metadatas)
        except Exception as e:
            print(f"    Error in batch {i//batch_size + 1}: {e}")
            return False # Fail out to prevent false positive state saving

    print(f"Finished processing {file_name}\n")
    return True


def main():
    """Main entry point to scan data folders and trigger ingestion."""
    print("Starting Data Ingestion...\n")
    load_dotenv()
    
    try:
        engine = VectorEngine()
    except Exception as e:
        print(f"Error initializing Vector Engine: {e}")
        return

    base_data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
    
    if not os.path.exists(base_data_folder):
        print(f"Base data folder not found at: {base_data_folder}")
        return

    # Load previously processed file hashes
    state = load_state()

    for folder_name in os.listdir(base_data_folder):
        folder_path = os.path.join(base_data_folder, folder_name)
        
        if os.path.isdir(folder_path):
            collection_name = folder_name
            print(f"\n--- Scanning directory: {folder_name} ---")
            
            if collection_name not in state:
                state[collection_name] = {}
                
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                
                if os.path.isfile(file_path) and not file_name.startswith('.'):
                    
                    # Check MD5 Hash
                    current_hash = get_file_hash(file_path)
                    
                    if state[collection_name].get(file_name) == current_hash:
                        print(f"[SKIPPED] '{file_name}' (Already ingested and unmodified)")
                        continue
                        
                    # Process the file if new or modified
                    success = process_file(file_path=file_path, collection_name=collection_name, engine=engine)
                    
                    # Update state ONLY if completely successful
                    if success:
                        state[collection_name][file_name] = current_hash
                        save_state(state)


if __name__ == "__main__":
    main()