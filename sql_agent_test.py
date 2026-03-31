from dotenv import load_dotenv
from use_cases.sql_agent.sql_agent import SQLAgent

load_dotenv()

agent = SQLAgent(db_path="tienda_prueba.sqlite")

respuesta = agent.process_question("Which customers live in Madrid?")

print(respuesta)