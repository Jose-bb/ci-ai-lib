import os
import pytest
import sys
from fastapi.testclient import TestClient

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from use_cases.sql_agent.src.main import app
from use_cases.sql_agent.src.db_engines import DatabaseManager

client = TestClient(app)

def test_extract_schema_v2():
    """Test 1: Verifies that DatabaseManager correctly extracts the schema from SQLite."""
    conn_string = "sqlite:///use_cases/sql_agent/data/tienda_prueba.sqlite"
    schema = DatabaseManager.get_sql_schema(conn_string)
    
    assert schema is not None
    assert "clientes" in schema.lower()
    assert "ventas" in schema.lower()

def test_tienda_routing_and_execution():
    """Test 2: Verifies full LangGraph flow (Router -> Agent -> DB) for the Store."""
    response = client.post("/ask-db", json={"question": "¿Qué clientes viven en Madrid?"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["routed_db"] == "tienda_sql"
    assert data["error"] is None
    
    assert "SELECT" in data["query"].upper()
    assert "Ana" in str(data["data"])

def test_hr_routing_accuracy():
    """Test 3: Verifies LangGraph correctly routes Human Resources questions."""
    response = client.post("/ask-db", json={"question": "¿Cuál es el salario de Elena García?"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["routed_db"] == "recursos_humanos_sql"
    assert data["error"] is None

def test_router_out_of_domain_handling():
    """Test 4: Verifies the Router rejects questions outside of its configured domains (Anti-Hallucination)."""
    response = client.post("/ask-db", json={"question": "¿Cuál es la capital de Australia?"})
    
    assert response.status_code == 400
    assert "UNKNOWN" in response.json()["detail"]

def test_security_restriction_blocks_non_select():
    """Test 5: Verifies the DatabaseManager physically blocks destructive queries at the Python engine level."""
    conn_string = "sqlite:///use_cases/sql_agent/data/tienda_prueba.sqlite"
    malicious_query = "DROP TABLE clientes;"
    
    result = DatabaseManager.execute_sql(malicious_query, conn_string)
        
    assert isinstance(result, str)
    error_message = result.lower()
    assert "select" in error_message or "error" in error_message or "with" in error_message

def test_extract_nosql_schema():
    """Test 6: Verifies that DatabaseManager correctly extracts a sample document from MongoDB."""
    conn_string = "mongodb://host.docker.internal:27017/"
    db_name = "company_logs"
    collection_name = "server_logs"
    
    schema = DatabaseManager.get_nosql_schema(conn_string, db_name, collection_name)
    
    assert schema is not None
    assert "Collection: server_logs" in schema
    assert "Sample Document Structure" in schema

def test_nosql_routing_and_execution():
    """Test 7: Verifies LangGraph correctly routes NoSQL questions and returns a valid Mongo dictionary."""
    response = client.post("/ask-db", json={"question": "Muestra los logs que hayan dado un error de tipo CRITICAL"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["routed_db"] == "logs_nosql"
    assert data["error"] is None
    
    assert "{" in data["query"] and "}" in data["query"]
    assert "CRITICAL" in data["query"]
    
    assert isinstance(data["data"], list)