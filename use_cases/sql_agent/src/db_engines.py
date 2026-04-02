from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
import json

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
                        return "Query executed successfully, but returned no data."
                    
                    return json.dumps([dict(row._mapping) for row in rows], default=str)
                else:
                    return "Error: Query did not return any rows. Ensure you are using a SELECT statement."
                    
        except SQLAlchemyError as e:
            return f"Database Error: {str(e)}"
        except Exception as e:
            return f"Unexpected Error: {str(e)}"

    @staticmethod
    def execute_nosql(query_dict: dict, connection_string: str, db_name: str) -> str:
        """
        [Future implementation placeholder]
        PyMongo execution logic will be implemented here for NoSQL databases.
        """
        return "NoSQL execution is not implemented yet in V2 Phase 1."