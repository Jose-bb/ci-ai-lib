import requests
import json

url = "http://localhost:8002/ask-rag-stream"

# IMPORTANT: Change the "question" below to match the context of your own vector database.
# The default question assumes a Pokémon manual PDF was ingested, which is not included in this repo.
payload = {
    "question": "Actúa como el Profesor Oak. Analiza en extremo detalle a Pikachu, Raichu y Nidoran. Escribe un texto muy largo, de al menos 3 párrafos, comparando sus descripciones físicas, tipos, pesos y alturas basándote en el manual. Explayate mucho en la narrativa.",
    "session_id": "long_session_2"
}

print("Connecting to the RAG Agent (Streaming Mode)...\n")

try:
    with requests.post(url, json=payload, stream=True) as response:
        response.raise_for_status() 
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode('utf-8'))
                
                if "error" in data:
                    print(f"\n[CAPTURED SERVER ERROR]: {data['error']}")
                elif data.get("type") == "metadata":
                    print(f"[METADATA] Routed database: {data['routed_db']}")
                    print("-" * 50)
                elif data.get("type") == "chunk":
                    print(data["content"], end="", flush=True)
                    
    print("\n\n[END OF TRANSMISSION]")

except Exception as e:
    print(f"\n[ERROR] Something went wrong: {e}")