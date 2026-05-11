import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv

from llm_interfaces.factory import LLMFactory
from use_cases.vector_agent.src.vector_engine import VectorEngine

load_dotenv()

class RAGAgent:
    """Agent that performs Retrieval-Augmented Generation based on prompts.yaml config."""
    
    def __init__(self, collection_id: str, config_path: str = "use_cases/vector_agent/config/prompts.yaml", provider: str = "azure_openai"):
        """Initializes the agent, loading specific config and setting up the Vector Engine."""
        self.collection_id = collection_id
        self.llm = LLMFactory.get_llm(provider)
        self.model_name = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o-mini")

        self.config = self._load_config(config_path, collection_id)
        self.vector_engine = VectorEngine()

    def _load_config(self, path: str, collection_id: str) -> Dict[str, Any]:
        """Extracts the configuration for the requested collection_id from the YAML."""
        with open(path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            
            if collection_id not in data.get("databases", {}):
                raise ValueError(f"Configuration Error: Collection ID '{collection_id}' not found in {path}")
                
            return data["databases"][collection_id]

    def process_query(self, user_question: str) -> dict:
        """Retrieves context, injects it into the prompt, and generates an LLM answer."""
        collection_name = self.config.get("collection_name", self.collection_id)
        
        # Retrieve Context
        search_results = self.vector_engine.search_similarity(
            query=user_question, 
            collection_name=collection_name, 
            k=4
        )

        if isinstance(search_results, str):
            return {"error": search_results}

        # Format Context
        context_texts = [f"- {item['content']}" for item in search_results]
        formatted_context = "\n".join(context_texts) if context_texts else "No relevant information found in the knowledge base."

        # Inject Context into Prompt Safely
        raw_system_prompt = self.config["system_prompt"]
        if "{context}" in raw_system_prompt:
            formatted_system_prompt = raw_system_prompt.replace("{context}", formatted_context)
        else:
            # Fallback if {context} placeholder is missing in YAML
            formatted_system_prompt = f"{raw_system_prompt}\n\nRETRIEVED CONTEXT:\n{formatted_context}"
        
        # Generate Answer
        messages = [
            {"role": "system", "content": formatted_system_prompt},
            {"role": "user", "content": user_question}
        ]

        generated_answer = self.llm.invoke(messages=messages, model=self.model_name)

        return {
            "context": search_results,
            "data": generated_answer
        }