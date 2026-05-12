import requests

url = "http://localhost:8002/ask-rag"

# IMPORTANT: Change the "question" below to match the context of your own vector database.
# The default question assumes a Pokémon manual PDF was ingested, which is not included in this repo.
payload = {
    "question": "Actúa como el Profesor Oak. Analiza en extremo detalle a Pikachu, Raichu y Nidoran. Escribe un texto muy largo, de al menos 3 párrafos, comparando sus descripciones físicas, tipos, pesos y alturas basándote en el manual. Explayate mucho en la narrativa.",
    "session_id": "long_session_2"
}

print("Connecting to the RAG Agent (Classic Mode)...\n")
print("Waiting for the complete response (the terminal will appear frozen)...\n")

try:
    # Make the standard request (without stream=True)
    response = requests.post(url, json=payload)
    response.raise_for_status()
    
    data = response.json()
    
    print("-" * 50)
    
    # New error handling logic
    if "error" in data and data["error"]:
        print(f"[CAPTURED SERVER ERROR]: {data['error']}")
    else:
        print(data.get("data", "Error in the response"))

except Exception as e:
    print(f"\n[ERROR] Something went wrong: {e}")