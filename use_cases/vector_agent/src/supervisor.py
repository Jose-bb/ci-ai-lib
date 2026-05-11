import os
import yaml
import operator
import json
from typing import TypedDict, Optional, Annotated, Generator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.redis import RedisSaver

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from llm_interfaces.factory import LLMFactory
from use_cases.vector_agent.src.rag_agent import RAGAgent

# Constants for anonymization to prevent reallocation in recursive calls
DANGEROUS_KEYS = {"password", "pass", "pwd", "token", "secret", "api_key", "hash"}
DANGEROUS_ENTITIES = ["IP_ADDRESS", "CREDIT_CARD", "IBAN_CODE", "ES_NIF", "ES_NIE"]


class GraphState(TypedDict):
    question: str
    selected_db: Optional[str]
    result: Optional[dict]
    error: Optional[str]
    history: Annotated[list[str], operator.add]
    stream_mode: bool


class SupervisorGraph:
    """Routes user questions to the correct vector collection and ensures data privacy."""
    
    def __init__(self, config_path: str = "use_cases/vector_agent/config/prompts.yaml", provider: str = "azure_openai"):
        """Initializes LLM, NLP engines for Presidio, Redis memory, and compiles the LangGraph."""
        self.config_path = config_path
        self.llm = LLMFactory.get_llm(provider)
        self.model_name = os.getenv("AZURE_OPENAI_MODEL")
        
        self.db_catalog = self._load_catalog()

        # Initialize Presidio NLP Engine
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "es", "model_name": "es_core_news_md"}]
        }
        nlp_provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
        nlp_engine = nlp_provider.create_engine()
        
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["es"])
        self.anonymizer = AnonymizerEngine()

        # Initialize Redis Memory
        redis_host = os.getenv("REDIS_HOST", "host.docker.internal")
        redis_url = f"redis://{redis_host}:6380/0"
        self.memory = RedisSaver(redis_url)
        self.memory.setup()
        
        self.graph = self._build_graph()

    def _load_catalog(self) -> dict:
        """Reads routing descriptions from the YAML file."""
        with open(self.config_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            return data.get("databases", {})

    def router_node(self, state: GraphState) -> dict:
        """Uses the LLM to decide which knowledge base is the best fit for the question."""
        question = state["question"]
        history_text = "\n".join(state.get("history", []))
        
        catalog_text = ""
        for db_id, db_info in self.db_catalog.items():
            catalog_text += f"- ID: {db_id} | Description: {db_info.get('description', 'No description')}\n"
            
        system_prompt = (
            "You are an expert knowledge base routing supervisor. "
            "Your task is to analyze the user's question and route it to the correct document collection.\n\n"
            "CONVERSATION HISTORY:\n"
            f"{history_text}\n\n"
            "AVAILABLE COLLECTIONS:\n"
            f"{catalog_text}\n"
            "RULES:\n"
            "1. Respond ONLY with the exact ID of the collection.\n"
            "2. Do not add any extra text, punctuation, or explanations.\n"
            "3. If the user's question is a continuation (e.g., 'and what about the other document?'), use the CONVERSATION HISTORY to understand the context.\n"
            "4. If no collection matches, respond with 'UNKNOWN'."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        selected_id = self.llm.invoke(messages=messages, model=self.model_name).strip()

        if selected_id == "UNKNOWN":
            return {"error": "UNKNOWN_DOMAIN", "selected_db": "UNKNOWN"}
            
        if selected_id not in self.db_catalog:
            return {"error": f"Routing Failure: Invalid Collection selected ({selected_id})"}
            
        return {
            "selected_db": selected_id, 
            "history": [f"User asked: {question}", f"Router selected Collection: {selected_id}"]
        }

    def execution_node(self, state: GraphState) -> dict:
        """Executes the RAG Agent using the selected collection ID."""
        if state.get("error"):
            return {}
            
        selected_db = state["selected_db"]
        question = state["question"]
        stream_mode = state.get("stream_mode", False)

        history_text = "\n".join(state.get("history", []))
        enriched_question = (
            f"HISTORIAL DE CONVERSACIÓN:\n{history_text}\n\n"
            f"PREGUNTA DEL USUARIO A RESOLVER:\n{question}"
        )
        
        try:
            agent = RAGAgent(collection_id=selected_db, config_path=self.config_path)
            result = agent.process_query(enriched_question, stream=stream_mode)
            
            # If in stream mode, data is a generator, so we can't save the full answer to history yet.
            agent_answer = result.get("data", "") if not stream_mode else "<STREAMING_RESPONSE>"
            
            return {
                "result": result,
                "history": [f"Agent answered: {agent_answer}"]
            }
            
        except Exception as e:
            return {"error": str(e)}

    def _anonymize_recursive(self, data, current_key=None):
        """Recursively traverses lists and dicts to mask specific strings and sensitive keys."""
        if current_key and any(keyword in str(current_key).lower() for keyword in DANGEROUS_KEYS):
            return "<REDACTED_SECRET>"
        
        if isinstance(data, str):
            results = self.analyzer.analyze(
                text=data, 
                language='es',
                entities=DANGEROUS_ENTITIES
            )
            anonymized = self.anonymizer.anonymize(text=data, analyzer_results=results)
            return anonymized.text
            
        elif isinstance(data, dict):
            return {key: self._anonymize_recursive(value, current_key=key) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._anonymize_recursive(item) for item in data]
        else:
            return data

    def anonymizer_node(self, state: GraphState) -> dict:
        """Masks PII in both the final answer and the retrieved context."""
        if state.get("error") or not state.get("result"):
            return {}

        agent_result = state["result"]
        stream_mode = state.get("stream_mode", False)

        # In streaming mode, data is a generator, so we cannot anonymize it here
        # without consuming the generator and breaking the stream.
        if not stream_mode and "data" in agent_result:
            agent_result["data"] = self._anonymize_recursive(agent_result["data"])

        if "context" in agent_result:
            agent_result["context"] = self._anonymize_recursive(agent_result["context"])

        return {"result": agent_result}

    def _build_graph(self):
        """Maps out the flow: START -> router -> executor -> anonymizer -> END."""
        builder = StateGraph(GraphState)
        
        builder.add_node("router", self.router_node)
        builder.add_node("executor", self.execution_node)
        builder.add_node("anonymizer", self.anonymizer_node)
        
        builder.add_edge(START, "router")
        builder.add_edge("router", "executor")
        builder.add_edge("executor", "anonymizer")
        builder.add_edge("anonymizer", END)
        
        return builder.compile(checkpointer=self.memory)

    def run(self, user_question: str, session_id: str = "default_session") -> dict:
        """Public entry point for non-streaming execution."""
        config = {"configurable": {"thread_id": session_id}}

        inputs = {
            "question": user_question,
            "error": None,
            "result": None,
            "stream_mode": False
        }
        
        return self.graph.invoke(inputs, config=config)

    def stream_run(self, user_question: str, session_id: str = "default_session") -> Generator[str, None, None]:
        """Public entry point to execute the graph and stream the LLM response."""
        config = {"configurable": {"thread_id": session_id}}

        inputs = {
            "question": user_question,
            "error": None,
            "result": None,
            "stream_mode": True
        }

        # We need to manually execute the graph nodes to intercept the generator
        try:
            # Run Router
            router_output = self.router_node(inputs)
            if "error" in router_output:
                yield json.dumps({"error": router_output["error"]})
                return
            
            inputs.update(router_output)

            # Run Executor
            executor_output = self.execution_node(inputs)
            if "error" in executor_output:
                yield json.dumps({"error": executor_output["error"]})
                return

            result = executor_output["result"]
            generator = result.get("data")
            
            # Anonymize context before sending it
            anonymized_context = self._anonymize_recursive(result.get("context", []))
            
            # Send initial metadata (routed DB and context)
            yield json.dumps({
                "type": "metadata",
                "routed_db": inputs.get("selected_db"),
                "context": anonymized_context
            }) + "\n"

            # Stream the LLM tokens
            full_response = ""
            if generator:
                for chunk in generator:
                    full_response += chunk
                    yield json.dumps({"type": "chunk", "content": chunk}) + "\n"

            # Redis
            self.graph.update_state(config, {"history": [f"Agent answered: {full_response}"]})

        except Exception as e:
            yield json.dumps({"error": f"Streaming failed: {str(e)}"})