import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '../data/recursos_humanos.sqlite')

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE departamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        ubicacion TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE empleados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        departamento_id INTEGER,
        nombre TEXT NOT NULL,
        salario REAL NOT NULL,
        FOREIGN KEY (departamento_id) REFERENCES departamentos (id)
    )
''')

departments_data = [
    ('Ingeniería', 'Edificio A'),
    ('Recursos Humanos', 'Edificio B'),
    ('Ventas', 'Edificio C')
]
cursor.executemany('INSERT INTO departamentos (nombre, ubicacion) VALUES (?, ?)', departments_data)

employees_data = [
    (1, 'Juan Pérez', 75000.50),
    (1, 'Elena García', 120000.00),
    (2, 'María Rodríguez', 65000.00),
    (3, 'Carlos López', 55000.00)
]
cursor.executemany('INSERT INTO empleados (departamento_id, nombre, salario) VALUES (?, ?, ?)', employees_data)

connection.commit()
connection.close()

print(f"Success! Human Resources Database created correctly at: {DB_PATH}")