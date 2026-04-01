import sqlite3
import os

db_name = "tienda_prueba.sqlite"

if os.path.exists(db_name):
    os.remove(db_name)

conexion = sqlite3.connect(db_name)
cursor = conexion.cursor()

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

clientes_data = [
    ('Ana García', 'Madrid'),
    ('Carlos López', 'Barcelona'),
    ('María Rodríguez', 'Valencia')
]
cursor.executemany('INSERT INTO clientes (nombre, ciudad) VALUES (?, ?)', clientes_data)

ventas_data = [
    (1, 'Ordenador Portátil', 1, 1200.50),
    (1, 'Ratón Inalámbrico', 2, 25.00),
    (2, 'Monitor 27"', 1, 300.00),
    (3, 'Teclado Mecánico', 1, 85.99)
]
cursor.executemany('INSERT INTO ventas (cliente_id, producto, cantidad, precio_unidad) VALUES (?, ?, ?, ?)', ventas_data)

conexion.commit()
conexion.close()

print(f"¡Éxito! Base de datos '{db_name}' creada correctamente con datos de prueba.")