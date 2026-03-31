import sqlite3
import os
from typing import List, Dict, Any, Tuple
from llm_interfaces.factory import LLMFactory

class SQLAgent:
    """
    Agent responsible for translating natural language questions into SQL queries
    and executing them against a SQLite database.
    """

    def __init__(self, db_path: str, provider: str = "azure_openai"):
        """
        Initializes the SQLAgent with a database path and an LLM provider.
        """
        self.db_path = db_path
        self.llm = LLMFactory.get_llm(provider)
        self.model_name = "devlab-gpt-4o-mini"
        
        self.db_schema = self._extract_schema()

    def _extract_schema(self) -> str:
        """
        Private method to extract tables and columns from the SQLite database.
        """
        schema_text = "DATABASE STRUCTURE:\n"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()

                for table in tables:
                    table_name = table[0]
                    if table_name == 'sqlite_sequence': 
                        continue
                    
                    schema_text += f"\nTable: {table_name}\nColumns: "
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = [col[1] for col in cursor.fetchall()]
                    schema_text += ", ".join(columns)
                    
            return schema_text
        except sqlite3.Error as e:
            return f"Error extracting schema: {e}"

    def _execute_sql(self, query: str) -> List[Tuple]:
        """
        Private method to execute a raw SQL query and fetch results.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[Error] SQL Execution failed: {e}")
            return []

    def process_question(self, user_question: str) -> Dict[str, Any]:
        """
        Public method to process a user question, generate SQL, and fetch data.
        """
        system_prompt = f"""
        You are an expert SQL Assistant. Convert natural language questions into valid SQLite queries.
        Use ONLY the following tables and columns:
        {self.db_schema}

        IMPORTANT RULES:
        - If the user asks for a person by their first name (e.g., "Carlos"), use the SQL LIKE operator with wildcards (e.g., LIKE '%Carlos%') because the database contains full names (first and last names together).

        Respond ONLY with the raw SQL query. Do not include markdown blocks, explanations, or quotes.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ]

        generated_sql = self.llm.invoke(messages=messages, model=self.model_name).strip()
        
        results = []
        if generated_sql.upper().startswith("SELECT"):
            results = self._execute_sql(generated_sql)
        else:
            generated_sql = "INVALID OR DANGEROUS SQL"

        return {
            "question": user_question,
            "generated_sql": generated_sql,
            "data": results
        }