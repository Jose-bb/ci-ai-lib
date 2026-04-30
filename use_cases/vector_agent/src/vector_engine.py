import os
from typing import List, Dict, Any, Union
import chromadb
from chromadb.config import Settings
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma

class VectorEngine:
    """
    Class responsible for executing real vector queries against ChromaDB.
    Supports semantic search and document ingestion via Azure OpenAI Embeddings.
    """

    def __init__(self):
        """Initializes the connection to ChromaDB and loads the heavy embedding model once."""
        host_url = os.getenv("CHROMADB_HOST", "http://host.docker.internal:8000")
        
        # We clean the host string to separate the IP and the port for the Chroma client
        host_clean = host_url.replace("http://", "").split(":")[0]
        port_clean = int(host_url.split(":")[-1])
        
        self.client = chromadb.HttpClient(
            host=host_clean,
            port=port_clean,
            settings=Settings(allow_reset=True)
        )

        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            check_embedding_ctx_length=False
        )

    def _get_collection(self, collection_name: str) -> Chroma:
        """Internal helper to retrieve or create a collection instance."""
        return Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings
        )

    def search_similarity(self, query: str, collection_name: str, k: int = 4) -> Union[List[Dict[str, Any]], str]:
        """
        Executes a semantic search query and returns the top 'k' results.
        Returns a list of dictionaries with content and metadata, or an error string.
        """
        try:
            safe_query = query.strip()
            if not safe_query:
                return "Query Error: The search query cannot be empty."

            vector_db = self._get_collection(collection_name)
            
            # Perform similarity search with confidence scores
            docs = vector_db.similarity_search_with_relevance_scores(safe_query, k=k)
            
            if not docs:
                return []

            # Format the output matching the style of the SQL agent (list of dictionaries)
            results = []
            for doc, score in docs:
                results.append({
                    "content": str(doc.page_content),
                    "metadata": doc.metadata if isinstance(doc.metadata, dict) else {},
                    "relevance_score": float(score)
                })
                
            return results

        except Exception as e:
            return f"Vector Database Error: {str(e)}"

    def add_documents(self, texts: List[str], collection_name: str, metadatas: List[Dict] = None) -> str:
        """
        Ingests a list of texts, converts them to embeddings, and stores them in ChromaDB.
        """
        try:
            if not texts:
                return "Ingestion Error: No texts provided for embedding."

            vector_db = self._get_collection(collection_name)
            vector_db.add_texts(texts=texts, metadatas=metadatas)
            
            return f"Success: Added {len(texts)} documents to '{collection_name}'."
            
        except Exception as e:
            return f"Ingestion Error: {str(e)}"