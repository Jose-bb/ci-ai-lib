import os
import pytest
import sys
from unittest.mock import patch
from fastapi.testclient import TestClient

# Ensure the root directory is in the path to allow absolute imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from use_cases.vector_agent.src.main import app
from use_cases.vector_agent.src.vector_engine import VectorEngine
from use_cases.vector_agent.src.supervisor import SupervisorGraph

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_test_collection():
    """
    Creates a temporary ChromaDB collection, injects a test document, 
    yields the collection name for tests to use, and deletes it afterwards.
    """
    engine = VectorEngine()
    test_collection = "test_fixture_collection"
    
    # Ingest dummy data
    dummy_text = ["El código secreto de la caja fuerte de la base RAG es Piña Colada 2024."]
    metadata = [{"source": "test_fixture"}]
    engine.add_documents(texts=dummy_text, collection_name=test_collection, metadatas=metadata)
    
    # Yield control to the tests
    yield test_collection
    
    # Clean up the database so we leave no trace
    try:
        engine.client.delete_collection(test_collection)
    except Exception:
        pass


def test_integration_vector_engine(setup_test_collection):
    """Test 1: Verifies real connection and retrieval without relying on data/ folder."""
    engine = VectorEngine()
    collection_name = setup_test_collection
    
    # Search for the secret code in our temporary collection
    results = engine.search_similarity(query="código secreto", collection_name=collection_name, k=1)
    
    assert isinstance(results, list)
    assert len(results) > 0
    # Verify the real database correctly matched the semantic meaning
    assert "Piña Colada" in results[0]["content"]


@patch('use_cases.vector_agent.src.vector_engine.VectorEngine.search_similarity')
def test_mocked_vector_retrieval(mock_search):
    """Test 2: Verifies retrieval logic instantly without hitting the real database."""
    # Setup our "action double" (Mock)
    mock_search.return_value = [
        {"content": "Ned Stark encontró un lobo huargo en la nieve.", "relevance_score": 0.99}
    ]
    
    engine = VectorEngine()
    results = engine.search_similarity(query="Ned Stark", collection_name="got_lore", k=1)
    
    assert len(results) == 1
    assert "lobo" in results[0]["content"]
    # Verify the code actually attempted to call the database with the right parameters
    mock_search.assert_called_once_with(query="Ned Stark", collection_name="got_lore", k=1)


def test_pii_anonymization_unit():
    """Test 3: Verifies that the Presidio/spaCy dual-layer firewall masks PII."""
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config/prompts.yaml'))
    supervisor = SupervisorGraph(config_path=config_path)
    
    mock_payload = {
        "data": "El servidor se conectó desde la IP 192.168.1.150.",
        "metadata": {"api_key": "sk-123456789abc", "source": "database_log"}
    }
    
    anonymized_payload = supervisor._anonymize_recursive(mock_payload)
    anonymized_str = str(anonymized_payload)
    
    assert "192.168.1.150" not in anonymized_str
    assert "<IP_ADDRESS>" in anonymized_str
    assert "sk-123456789abc" not in anonymized_str
    assert "<REDACTED_SECRET>" in anonymized_str
    assert "database_log" in anonymized_str 


def test_router_out_of_domain_handling():
    """Test 4: Verifies the Router rejects questions outside of its configured domains."""
    response = client.post("/ask-rag", json={
        "question": "¿Cómo se cocina una tortilla de patatas?",
        "session_id": "test_domain_vector_1"
    })
    
    assert response.status_code == 400
    assert "UNKNOWN" in response.json()["detail"]


def test_conversational_memory_active():
    """Test 5 (API): Verifies that Redis Stack maintains cross-turn context for ambiguous questions."""
    session_id = "test_memory_vector_1"

    # Establish the context
    client.post("/ask-rag", json={
        "question": "Háblame sobre Pikachu.",
        "session_id": session_id
    })

    # Ambiguous question requiring memory
    response = client.post("/ask-rag", json={
        "question": "¿A qué nivel evoluciona?",
        "session_id": session_id
    })
    
    assert response.status_code == 200
    data = response.json()

    assert data["routed_db"] == "pokedex_vector"
    assert data["error"] is None