import os
import sys
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader, CSVLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Add root directory to sys.path to resolve internal modules
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from use_cases.vector_agent.src.vector_engine import VectorEngine


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


def process_file(file_path: str, collection_name: str, engine: VectorEngine):
    """Loads, chunks, and ingests a document into ChromaDB in batches."""
    print(f"\nProcessing file: {file_path}")
    
    # Select the appropriate loader
    if file_path.endswith('.pdf'):
        loader = PyMuPDFLoader(file_path)
    elif file_path.endswith('.csv'):
        loader = CSVLoader(file_path, encoding='utf-8')
    elif file_path.endswith('.txt'):
        loader = TextLoader(file_path, encoding='utf-8')
    else:
        print(f"Unsupported file type: {file_path}")
        return

    # Load and split the document
    raw_documents = loader.load()
    print(f"-> Extracted {len(raw_documents)} raw pages/rows.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "]
    )
    
    chunked_docs = text_splitter.split_documents(raw_documents)
    print(f"-> Split into {len(chunked_docs)} manageable chunks.")

    # Extract texts and sanitize metadata
    texts = [doc.page_content for doc in chunked_docs]
    metadatas = []
    
    for doc in chunked_docs:
        meta = doc.metadata.copy() # Prevent mutating the original reference
        meta["source_file"] = os.path.basename(file_path)
        metadatas.append(sanitize_metadata(meta))
    
    # Batch ingestion to avoid API rate limits/payload errors
    batch_size = 50
    print(f"-> Sending to Azure and ChromaDB in batches of {batch_size}...")
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_metadatas = metadatas[i:i + batch_size]
        
        print(f"Uploading batch {i//batch_size + 1} (Chunks {i} to {min(i + batch_size, len(texts))})...")
        try:
            engine.add_documents(texts=batch_texts, collection_name=collection_name, metadatas=batch_metadatas)
        except Exception as e:
            print(f"Error in batch {i//batch_size + 1}: {e}")

    print(f"Finished processing {file_path}\n")


def main():
    """Main entry point to scan data folders and trigger ingestion."""
    print("Starting Data Ingestion...\n")
    load_dotenv()
    
    try:
        engine = VectorEngine()
    except Exception as e:
        print(f"Error initializing Vector Engine: {e}")
        return

    # Ensure robust absolute path resolution
    base_data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
    
    if not os.path.exists(base_data_folder):
        print(f"Base data folder not found at: {base_data_folder}")
        return

    # Iterate dynamically over each subfolder
    for folder_name in os.listdir(base_data_folder):
        folder_path = os.path.join(base_data_folder, folder_name)
        
        # Only process if it is actually a directory
        if os.path.isdir(folder_path):
            collection_name = folder_name
            print(f"Scanning directory: {folder_name}")
            
            # Iterate over all files inside this specific subfolder
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                
                # Process valid files only
                if os.path.isfile(file_path) and not file_name.startswith('.'):
                    process_file(file_path=file_path, collection_name=collection_name, engine=engine)


if __name__ == "__main__":
    main()