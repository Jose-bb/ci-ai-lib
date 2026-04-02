import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv

from llm_interfaces.factory import LLMFactory
from use_cases.sql_agent.src.db_engines import DatabaseManager

load_dotenv()

class UniversalDBAgent:
    """Configuration-driven agent that adapts its behavior based on prompts.yaml."""
    
    def __init__(self, db_id: str, config_path: str = "config/prompts.yaml", provider: str = "azure_openai"):
        """Initializes the agent by reading its specific configuration from the YAML file"""
        self.db_id = db_id
        self.llm = LLMFactory.get_llm(provider)
        self.model_name = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o-mini")

        self.config = self._load_config(config_path, db_id)

    def _load_config(self, path: str, db_id: str) -> Dict[str, Any]:
        """Reads the YAML file and extracts the configuration for the requested db_id."""
        with open(path, 'r') as file:
            data = yaml.safe_load(file)
            
            if db_id not in data.get("databases", {}):
                raise ValueError(f"Configuration Error: Database ID '{db_id}' not found in {path}")
                
            return data["databases"][db_id]

    def process_query(self, user_question: str) -> str:
        """Gets the DB schema, injects the schema into the YAML prompt, asks the LLM to generate the query and executes the query safely using DatabaseManager."""

        conn_string = self.config["connection_string"]
        db_type = self.config["db_type"]
        
        if db_type == "sql":
            schema = DatabaseManager.get_sql_schema(conn_string)
        elif db_type == "nosql":
            schema = "NoSQL schema extraction not implemented yet."
        else:
            return "Error: Unknown db_type in configuration."

        raw_system_prompt = self.config["system_prompt"]
        formatted_system_prompt = raw_system_prompt.format(schema=schema)
        
        messages = [
            {"role": "system", "content": formatted_system_prompt},
            {"role": "user", "content": user_question}
        ]

        generated_query = self.llm.invoke(messages=messages, model=self.model_name)

        if db_type == "sql":
            execution_result = DatabaseManager.execute_sql(generated_query, conn_string)
        else:
            # Placeholder for future MongoDB execution
            execution_result = DatabaseManager.execute_nosql(
                {"query": generated_query}, 
                conn_string, 
                self.config.get("database_name")
            )

        return f"--- GENERATED QUERY ---\n{generated_query}\n\n--- EXECUTION RESULT ---\n{execution_result}"