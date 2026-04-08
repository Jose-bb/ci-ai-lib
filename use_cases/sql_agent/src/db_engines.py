from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
import json
from pymongo import MongoClient
from typing import Any

class DatabaseManager:
    """
    Class responsible for executing real queries against databases.
    Supports multiple database engines via SQLAlchemy.
    """

    @staticmethod
    def get_sql_schema(connection_string: str) -> str:
        """Extracts the database schema (tables and columns)."""
        try:
            engine = create_engine(connection_string)
            inspector = inspect(engine)
            schema_info = []
            
            # Iterate through all tables in the database
            for table_name in inspector.get_table_names():
                columns = inspector.get_columns(table_name)
                col_details = [f"{col['name']} ({col['type']})" for col in columns]
                schema_info.append(f"Table: {table_name} | Columns: {', '.join(col_details)}")
                
            return "\n".join(schema_info)
        except Exception as e:
            return f"Error reading SQL schema: {str(e)}"

    @staticmethod
    def execute_sql(query: str, connection_string: str) -> str:
        """Executes the AI-generated SQL query and returns the results as a JSON string."""
        try:
            safe_query = query.strip().upper()

            if not (safe_query.startswith("SELECT") or safe_query.startswith("WITH")):
                return "Security Error: Only SELECT queries are allowed. Destructive commands are blocked by the system."

            engine = create_engine(connection_string)
            
            with engine.connect() as connection:
                result = connection.execute(text(query))
                
                # Process SELECT queries
                if result.returns_rows:
                    rows = result.fetchall()
                    if not rows:
                        return []
                    
                    # Convert non-standard types (such as dates) to strings, but retain the list of dictionaries
                    return [{k: str(v) if not isinstance(v, (int, float, str, bool, type(None))) else v for k, v in dict(row._mapping).items()} for row in rows]
                else:
                    return "Error: Query did not return any rows. Ensure you are using a SELECT statement."
                    
        except SQLAlchemyError as e:
            return f"Database Error: {str(e)}"
        except Exception as e:
            return f"Unexpected Error: {str(e)}"

    @staticmethod
    def get_nosql_schema(connection_string: str, db_name: str, collection_name: str) -> str:
        """Infers the NoSQL schema by extracting a sample document."""
        try:
            client = MongoClient(connection_string)
            db = client[db_name]
            collection = db[collection_name]
            
            sample_doc = collection.find_one()
            if not sample_doc:
                return "No data available to infer schema."
            
            sample_doc.pop("_id", None)
            
            schema_info = [
                f"Collection: {collection_name}",
                "Sample Document Structure (JSON):",
                json.dumps(sample_doc, indent=2, default=str)
            ]
            
            return "\n".join(schema_info)
        except Exception as e:
            return f"Error reading NoSQL schema: {str(e)}"

    @staticmethod
    def execute_nosql(query_payload: str, connection_string: str, db_name: str, collection_name: str) -> Any:
        """Executes a JSON payload query against MongoDB."""
        try:
            client = MongoClient(connection_string)
            db = client[db_name]
            collection = db[collection_name]
            
            clean_payload = query_payload.strip()
            if clean_payload.startswith("```json"):
                clean_payload = clean_payload[7:-3].strip()
            elif clean_payload.startswith("```"):
                clean_payload = clean_payload[3:-3].strip()
            
            query_dict = json.loads(clean_payload)
            
            cursor = collection.find(query_dict).limit(50)
            results = list(cursor)
            
            if not results:
                return []
                
            for doc in results:
                doc["_id"] = str(doc["_id"])
                
            return [{k: str(v) if not isinstance(v, (int, float, str, bool, type(None), list, dict)) else v for k, v in doc.items()} for doc in results]
            
        except json.JSONDecodeError:
            return {"error": "El LLM no devolvió un JSON/Diccionario válido.", "raw_output": query_payload}
        except Exception as e:
            return f"Database Error: {str(e)}"