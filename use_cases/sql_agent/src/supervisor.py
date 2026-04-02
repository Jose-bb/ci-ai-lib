import os
import yaml
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END

from llm_interfaces.factory import LLMFactory
from use_cases.sql_agent.src.base_agent import UniversalDBAgent

class GraphState(TypedDict):
    question: str
    selected_db: Optional[str]
    result: Optional[str]
    error: Optional[str]

class SupervisorGraph:
    """Acts as the brain that routes user questions to the correct database configuration."""
    
    def __init__(self, config_path: str = "config/prompts.yaml", provider: str = "azure_openai"):
        self.config_path = config_path
        self.llm = LLMFactory.get_llm(provider)
        self.model_name = os.getenv("AZURE_OPENAI_MODEL")
        
        self.db_catalog = self._load_catalog()
        self.graph = self._build_graph()

    def _load_catalog(self) -> dict:
        """Reads only the necessary routing descriptions from the YAML."""
        with open(self.config_path, 'r') as file:
            data = yaml.safe_load(file)
            return data.get("databases", {})

    def router_node(self, state: GraphState) -> dict:
        """Reads the YAML descriptions and asks the LLM to decide which database is the best fit for the user's question."""
        question = state["question"]
        
        catalog_text = ""
        for db_id, db_info in self.db_catalog.items():
            catalog_text += f"- ID: {db_id} | Description: {db_info.get('description', 'No description')}\n"
            
        system_prompt = (
            "You are an expert database routing supervisor. "
            "Your task is to analyze the user's question and route it to the correct database.\n\n"
            "AVAILABLE DATABASES:\n"
            f"{catalog_text}\n"
            "RULES:\n"
            "1. Respond ONLY with the exact ID of the database.\n"
            "2. Do not add any extra text, punctuation, or explanations.\n"
            "3. If no database matches, respond with 'UNKNOWN'."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        selected_id = self.llm.invoke(messages=messages, model=self.model_name).strip()
        
        if selected_id not in self.db_catalog:
            return {"error": f"Router failed to select a valid DB. It selected: {selected_id}"}
            
        return {"selected_db": selected_id}

    def execution_node(self, state: GraphState) -> dict:
        """Instantiates the Universal Agent using the selected DB ID and executes the query."""
        if state.get("error"):
            return {}
            
        selected_db = state["selected_db"]
        question = state["question"]
        
        try:
            agent = UniversalDBAgent(db_id=selected_db, config_path=self.config_path)
            result = agent.process_query(question)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}

    def _build_graph(self):
        """Maps out the flow: START -> Router -> Executor -> END."""
        builder = StateGraph(GraphState)
        
        builder.add_node("router", self.router_node)
        builder.add_node("executor", self.execution_node)
        
        builder.add_edge(START, "router")
        builder.add_edge("router", "executor")
        builder.add_edge("executor", END)
        
        return builder.compile()

    def run(self, user_question: str) -> dict:
        """Public entry point to throw a question into the graph."""
        initial_state = GraphState(
            question=user_question,
            selected_db=None,
            result=None,
            error=None
        )
        
        return self.graph.invoke(initial_state)