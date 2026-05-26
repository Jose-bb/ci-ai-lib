import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Este es el payload calcado que falló en la V3
mensajes_v3 = [
    {'role': 'system', 'content': 'You are an expert QA Lead specializing in Python applications.\nYour task is to analyze the provided Python project files, its global structural map, AND the project\'s context metadata (like README, requirements, or .env files), then design a comprehensive Global Test Plan in Markdown format.\n\nThe Test Plan MUST include:\n1. Executive Summary: Brief description of the project architecture, its core business logic (derived from README or context files), and primary dependencies.\n2. Test Cases: For the critical modules, complex classes, and core business methods identified during your analysis, define:\n   - Happy paths (standard execution).\n   - Edge cases (boundary values, empty inputs, unexpected types).\n   - Exception handling (verifying that errors are correctly raised and caught, including missing environment variables if applicable).\n3. Integration Context: Briefly map out how the different modules interact with each other and with external services mentioned in the context files.\n\nCRITICAL RULES:\n- First, thoroughly read any files marked as \'context_file\' (e.g., README.md, .env.example) to understand what the application does before looking at the Python code.\n- Do NOT generate any Python code in this step. Only output the Markdown document.\n- APPLY RISK-BASED QA: Do not attempt to cover 100% of the files. Prioritize core business logic, complex algorithms, public APIs, and error-prone functions. \n- IGNORE TRIVIAL CODE: Skip simple data classes, empty initializations, basic getters/setters, and boilerplate code to keep the test plan highly focused and prevent token exhaustion.\n- Output ONLY the Markdown text. Do not wrap the whole response in markdown code blocks.\n\nPROJECT STRUCTURE MAP:\n{\'proyecto_prueba/calculadora.py\': {\'type\': \'python_module\', \'classes\': {}, \'standalone_functions\': [{\'name\': \'sumar\', \'has_docstring\': True}, {\'name\': \'restar\', \'has_docstring\': True}, {\'name\': \'dividir\', \'has_docstring\': True}]}, \'proyecto_prueba/saludos.py\': {\'type\': \'python_module\', \'classes\': {}, \'standalone_functions\': [{\'name\': \'saludar\', \'has_docstring\': True}]}}\n\nPROJECT FILES CONTEXT:\n--- File: proyecto_prueba/calculadora.py ---\ndef sumar(a: float, b: float) -> float:\n    """Devuelve la suma de dos números."""\n    return a + b\n\ndef restar(a: float, b: float) -> float:\n    """Devuelve la resta de dos números."""\n    return a - b\n\ndef dividir(a: float, b: float) -> float:\n    """Devuelve la división de dos números. Lanza error si el divisor es 0."""\n    if b == 0:\n        raise ValueError("No se puede dividir por cero.")\n    return a / b\n\n--- File: proyecto_prueba/saludos.py ---\ndef saludar(nombre: str) -> str:\n    """Devuelve un saludo personalizado. Maneja strings vacíos."""\n    if not nombre.strip():\n        return "¡Hola, desconocido!"\n    return f"¡Hola, {nombre}!"\n\n'}, 
    {'role': 'user', 'content': 'Please generate the global Test Plan for the project.'}
]

print("Atacando a Azure con el prompt exacto de la V3...")
try:
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL"),
        messages=mensajes_v3
    )
    print("\n¡Milagro! Ha respondido:\n", response.choices[0].message.content)
except Exception as e:
    print(f"\nExplosión detectada: {e}")