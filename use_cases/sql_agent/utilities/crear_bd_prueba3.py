import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '../data/logistica.sqlite')

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE conductores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo_licencia TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE envios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conductor_id INTEGER,
        origen TEXT NOT NULL,
        destino TEXT NOT NULL,
        estado TEXT NOT NULL,
        FOREIGN KEY (conductor_id) REFERENCES conductores (id)
    )
''')

drivers_data = [
    ('Miguel Caballero', 'Clase A'),
    ('Sara Connor', 'Clase B')
]
cursor.executemany('INSERT INTO conductores (nombre, tipo_licencia) VALUES (?, ?)', drivers_data)

shipments_data = [
    (1, 'Madrid', 'Barcelona', 'Entregado'),
    (1, 'Valencia', 'Sevilla', 'En Tránsito'),
    (2, 'Bilbao', 'Zaragoza', 'Pendiente')
]
cursor.executemany('INSERT INTO envios (conductor_id, origen, destino, estado) VALUES (?, ?, ?, ?)', shipments_data)

connection.commit()
connection.close()

print(f"Success! Logistics Database created correctly at: {DB_PATH}")