import os
import pytest
import sys
from unittest.mock import patch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(ROOT_DIR)

from use_cases.sql_agent.src.sql_agent import SQLAgent

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/tienda_prueba.sqlite'))

def test_extract_schema():
    """Test 1: Verifies that the agent correctly reads the database schema upon initialization without making external LLM calls."""
    agent = SQLAgent(db_path=DB_PATH)

    assert agent.db_schema is not None
    assert "Table: clientes" in agent.db_schema
    assert "Columns: id, nombre, ciudad" in agent.db_schema

def test_process_question_structure():
    """Test 2: Verifies that the agent returns the expected JSON structure when asked a simple natural language question"""
    agent = SQLAgent(db_path=DB_PATH)
    
    question = "How many customers are there?"
    response = agent.process_question(question)
    
    assert "question" in response
    assert "generated_sql" in response
    assert "data" in response
    
    assert "SELECT" in response["generated_sql"].upper()
    assert isinstance(response["data"], list)

def test_security_restriction_blocks_non_select():
    """Test 3: Verifies that the agent blocks any SQL query that doesn't start with SELECT. We simulate the LLM returning a malicious DELETE query."""
    agent = SQLAgent(db_path=DB_PATH)

    with patch.object(agent.llm, 'invoke', return_value="DELETE FROM clientes;"):
        response = agent.process_question("Delete all customers")
        
        assert response["generated_sql"] == "INVALID OR DANGEROUS SQL"
        assert response["data"] == []
        assert "error" in response
        assert "Security restriction" in response["error"]

def test_sql_execution_error_handling():
    """Test 4: Verifies that if the SQL is syntactically wrong or queries a non-existent table, the error is caught and returned gracefully in the JSON."""
    agent = SQLAgent(db_path=DB_PATH)

    with patch.object(agent.llm, 'invoke', return_value="SELECT * FROM unicorns;"):
        response = agent.process_question("Show me the unicorns")
        
        assert response["data"] == []
        assert "error" in response
        assert "no such table" in response["error"].lower()