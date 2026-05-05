import os
from urllib.parse import urlparse
from typing import List, Dict, Any, Union, Optional
import chromadb
from chromadb.config import Settings
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma

class VectorEngine:
    """Manages ChromaDB interactions: semantic search and document ingestion."""

    def __init__(self):
        """Initializes the connection to ChromaDB and loads the heavy embedding model."""
        host_url = os.getenv("CHROMADB_HOST", "http://host.docker.internal:8000")
        
        # Parse URL safely to extract hostname and port
        parsed_url = urlparse(host_url)
        host_clean = parsed_url.hostname or "host.docker.internal"
        port_clean = parsed_url.port or 8000
        
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
        """Retrieves or creates a LangChain Chroma collection instance."""
        return Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings
        )


    def search_similarity(self, query: str, collection_name: str, k: int = 4) -> Union[List[Dict[str, Any]], str]:
        """Executes a semantic search and returns the top 'k' results or an error string."""
        try:
            safe_query = query.strip()
            if not safe_query:
                return "Query Error: The search query cannot be empty."

            vector_db = self._get_collection(collection_name)
            
            # Perform similarity search returning confidence scores
            docs = vector_db.similarity_search_with_relevance_scores(safe_query, k=k)
            
            if not docs:
                return []

            # Format output as a list of dictionaries
            return [
                {
                    "content": str(doc.page_content),
                    "metadata": doc.metadata if isinstance(doc.metadata, dict) else {},
                    "relevance_score": float(score)
                }
                for doc, score in docs
            ]

        except Exception as e:
            return f"Vector Database Error: {str(e)}"


    def add_documents(self, texts: List[str], collection_name: str, metadatas: Optional[List[Dict[str, Any]]] = None) -> str:
        """Embeds and stores a list of texts in the specified ChromaDB collection."""
        try:
            if not texts:
                return "Ingestion Error: No texts provided for embedding."

            vector_db = self._get_collection(collection_name)
            vector_db.add_texts(texts=texts, metadatas=metadatas)
            
            return f"Success: Added {len(texts)} documents to '{collection_name}'."
            
        except Exception as e:
            return f"Ingestion Error: {str(e)}"


    def delete_by_source(self, collection_name: str, source_name: str) -> str:
        """Deletes all document chunks originating from a specific source file."""
        try:
            collection = self.client.get_collection(collection_name)
            collection.delete(where={"source": source_name})
            return f"Success: Old records from '{source_name}' deleted from '{collection_name}'."
        except ValueError:
            # If the collection doesn't exist yet, Chroma raises a ValueError.
            return f"Skipped: Collection '{collection_name}' does not exist yet."
        except Exception as e:
            return f"Deletion Error: {str(e)}"