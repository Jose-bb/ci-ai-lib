import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '../data/tienda_prueba.sqlite')

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        ciudad TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        producto TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        precio_unidad REAL NOT NULL,
        FOREIGN KEY (cliente_id) REFERENCES clientes (id)
    )
''')

clients_data = [
    ('Ana García', 'Madrid'),
    ('Carlos López', 'Barcelona'),
    ('María Rodríguez', 'Valencia')
]
cursor.executemany('INSERT INTO clientes (nombre, ciudad) VALUES (?, ?)', clients_data)

sales_data = [
    (1, 'Ordenador Portátil', 1, 1200.50),
    (1, 'Ratón Inalámbrico', 2, 25.00),
    (2, 'Monitor 27"', 1, 300.00),
    (3, 'Teclado Mecánico', 1, 85.99)
]
cursor.executemany('INSERT INTO ventas (cliente_id, producto, cantidad, precio_unidad) VALUES (?, ?, ?, ?)', sales_data)

connection.commit()
connection.close()

print(f"Success! store Database created correctly at: {DB_PATH}")