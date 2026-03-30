import sqlite3
import os
from llm_interfaces.factory import LLMFactory

def obtener_esquema_db(db_path):
    """Función que extrae los nombres de tablas y columnas para la IA"""
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()
    
    esquema_texto = "ESTRUCTURA DE LA BASE DE DATOS:\n"
    
    for tabla in tablas:
        nombre_tabla = tabla[0]
        if nombre_tabla == 'sqlite_sequence': continue
        
        esquema_texto += f"\nTabla: {nombre_tabla}\nColumnas: "
        
        cursor.execute(f"PRAGMA table_info({nombre_tabla});")
        columnas = [col[1] for col in cursor.fetchall()]
        esquema_texto += ", ".join(columnas)
    
    conexion.close()
    return esquema_texto

def ejecutar_consulta_sql(db_path, sql_query):
    """Función para ejecutar el SQL generado por la IA y devolver resultados"""
    try:
        conexion = sqlite3.connect(db_path)
        cursor = conexion.cursor()
        cursor.execute(sql_query)
        resultados = cursor.fetchall()
        conexion.close()
        return resultados
    except Exception as e:
        return f"Error al ejecutar SQL: {e}"

db_archivo = "tienda_prueba.sqlite"
esquema = obtener_esquema_db(db_archivo)

pregunta_usuario = "¿Qué clientes viven en Madrid?"

prompt_sistema = f"""
Eres un experto en SQL. Tu tarea es convertir preguntas en lenguaje natural a consultas SQL válidas para SQLite.
Utiliza únicamente las tablas y columnas descritas a continuación:
{esquema}

Responde SOLO con la consulta SQL, sin explicaciones ni bloques de código markdown.
"""

print("--- ESQUEMA DETECTADO ---")
print(esquema)
print("\n--- PREGUNTA DEL USUARIO ---")
print(pregunta_usuario)