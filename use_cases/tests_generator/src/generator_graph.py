import os
from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, START, END

from llm_interfaces.factory import LLMFactory
from use_cases.tests_generator.utilities.parser import CodeParser
from use_cases.tests_generator.src.prompts import QA_PLANNER_PROMPT, TEST_CODER_PROMPT

class GraphState(TypedDict):
    """Defines the state passed between LangGraph nodes."""
    source_code: str
    code_structure: Optional[Dict[str, Any]]
    test_plan: Optional[str]
    generated_tests: Optional[str]
    error: Optional[str]

class QAGeneratorGraph:
    """Encapsulates the LangGraph architecture for the Tests Generator."""

    def __init__(self, provider: str = "azure_openai"):
        self.llm = LLMFactory.get_llm(provider)
        self.model_name = os.getenv("AZURE_OPENAI_MODEL")
        self.graph = self._build_graph()


    def parser_node(self, state: GraphState) -> dict:
        """Extracts the AST structure from the source code."""
        source = state["source_code"]
        structure = CodeParser.extract_structure(source)
        
        # Capture critical syntax errors early to prevent downstream LLM hallucinations
        if "error" in structure:
            return {"error": structure["error"]}
            
        return {"code_structure": structure}


    def qa_planner_node(self, state: GraphState) -> dict:
        """Drafts the Test Plan in Markdown based on the code structure."""
        # Fallback safeguard in case conditional routing is bypassed
        if state.get("error"):
            return {}

        system_prompt = QA_PLANNER_PROMPT.format(
            code_structure=str(state["code_structure"]),
            source_code=state["source_code"]
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please generate the Test Plan."}
        ]
        
        response = self.llm.invoke(messages=messages, model=self.model_name)
        return {"test_plan": response.strip()}


    def test_coder_node(self, state: GraphState) -> dict:
        """Generates the pytest executable code based on the Test Plan."""
        if state.get("error"):
            return {}

        system_prompt = TEST_CODER_PROMPT.format(
            source_code=state["source_code"],
            test_plan=state["test_plan"]
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please generate the pytest suite."}
        ]
        
        response = self.llm.invoke(messages=messages, model=self.model_name)
        
        # Strip markdown boundaries to ensure the payload is pure, executable Python code
        cleaned_code = response.replace("```python", "").replace("```", "").strip()
        
        return {"generated_tests": cleaned_code}


    def _build_graph(self):
        """Compiles the LangGraph architecture."""
        builder = StateGraph(GraphState)
        
        builder.add_node("parser", self.parser_node)
        builder.add_node("qa_planner", self.qa_planner_node)
        builder.add_node("test_coder", self.test_coder_node)
        
        builder.add_edge(START, "parser")
        builder.add_edge("parser", "qa_planner")
        builder.add_edge("qa_planner", "test_coder")
        builder.add_edge("test_coder", END)
        
        return builder.compile()


    def run(self, source_code: str) -> dict:
        """Entry point to execute the graph."""
        inputs = {
            "source_code": source_code,
            "code_structure": None,
            "test_plan": None,
            "generated_tests": None,
            "error": None
        }
        
        return self.graph.invoke(inputs)