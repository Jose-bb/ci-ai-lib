import os
from typing import TypedDict, Optional, Dict, Any, Callable
from langgraph.graph import StateGraph, START, END

from llm_interfaces.factory import LLMFactory
from use_cases.tests_generator.utilities.parser import CodeParser
from use_cases.tests_generator.src.prompts import QA_PLANNER_PROMPT, TEST_CODER_PROMPT

class GraphState(TypedDict):
    """Defines the state passed between LangGraph nodes for a full project."""
    project_files: Dict[str, str]
    code_structure: Optional[Dict[str, Any]]
    test_plan: Optional[str]
    generated_tests: Optional[str]
    error: Optional[str]
    # Optional callback to report progress (percentage, message)
    progress_callback: Optional[Callable[[int, str], None]]

class QAGeneratorGraph:
    """Encapsulates the LangGraph architecture for the Tests Generator (V3)."""

    def __init__(self, provider: str = "azure_openai"):
        self.llm = LLMFactory.get_llm(provider)
        self.model_name = os.getenv("AZURE_OPENAI_MODEL")
        self.graph = self._build_graph()


    def parser_node(self, state: GraphState) -> dict:
        """Extracts the AST structure from all project files."""
        cb = state.get("progress_callback")
        if cb: cb(15, "Extracting the structure and validating the syntax of the code...")

        files = state["project_files"]
        structure = CodeParser.extract_project_structure(files)
        
        # Capture critical syntax errors early to prevent downstream LLM hallucinations
        if "error" in structure:
            if cb: cb(100, "Error detected. Process aborted.")
            return {"error": structure["error"]}
            
        if cb: cb(25, "Syntax validated. Preparing the context...")
        return {"code_structure": structure}


    def qa_planner_node(self, state: GraphState) -> dict:
        """Drafts the Global Test Plan in Markdown based on the project structure."""
        if state.get("error"):
            return {}

        cb = state.get("progress_callback")
        if cb: cb(30, "AI planning the QA strategy (Generating Markdown)...")

        # Convert dictionary of files to a readable string format for the LLM context
        project_context = "\n".join(
            [f"--- File: {path} ---\n{code}\n" for path, code in state["project_files"].items()]
        )

        system_prompt = QA_PLANNER_PROMPT.format(
            code_structure=str(state["code_structure"]),
            project_context=project_context
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please generate the global Test Plan for the project."}
        ]
        
        response = self.llm.invoke(messages=messages, model=self.model_name)
        
        if cb: cb(50, "QA plan generated. Starting to write code...")
        return {"test_plan": response.strip()}


    def test_coder_node(self, state: GraphState) -> dict:
        """Generates the global pytest executable code based on the Test Plan."""
        if state.get("error"):
            return {}

        cb = state.get("progress_callback")
        if cb: cb(60, "AI isolating dependencies and setting up the Pytest suite...")

        project_context = "\n".join(
            [f"--- File: {path} ---\n{code}\n" for path, code in state["project_files"].items()]
        )

        system_prompt = TEST_CODER_PROMPT.format(
            project_context=project_context,
            test_plan=state["test_plan"]
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please generate the global pytest suite."}
        ]
        
        response = self.llm.invoke(messages=messages, model=self.model_name)
        
        # Strip markdown boundaries to ensure the payload is pure, executable Python code
        cleaned_code = response.replace("```python", "").replace("```", "").strip()
        
        if cb: cb(90, "Code generated successfully. Packaging results...")
        return {"generated_tests": cleaned_code}


    def _route_after_parser(self, state: GraphState) -> str:
        """Conditional routing: goes to END immediately if there's a syntax error."""
        if state.get("error"):
            return END
        return "qa_planner"


    def _build_graph(self):
        """Compiles the LangGraph architecture."""
        builder = StateGraph(GraphState)
        
        builder.add_node("parser", self.parser_node)
        builder.add_node("qa_planner", self.qa_planner_node)
        builder.add_node("test_coder", self.test_coder_node)
        
        builder.add_edge(START, "parser")
        
        # Implementation of the short-circuiting logic to save tokens
        builder.add_conditional_edges("parser", self._route_after_parser)
        
        builder.add_edge("qa_planner", "test_coder")
        builder.add_edge("test_coder", END)
        
        return builder.compile()

    def run(self, project_files: Dict[str, str], progress_callback: Optional[Callable[[int, str], None]] = None) -> dict:
        """Entry point to execute the graph."""
        if progress_callback:
            progress_callback(10, "Initialising LangGraph and preparing files...")

        inputs = {
            "project_files": project_files,
            "code_structure": None,
            "test_plan": None,
            "generated_tests": None,
            "error": None,
            "progress_callback": progress_callback
        }
        
        result = self.graph.invoke(inputs)
        
        if progress_callback and not result.get("error"):
            progress_callback(100, "Process completed successfully!")
            
        return result