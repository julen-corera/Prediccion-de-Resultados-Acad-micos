import sqlite3
import sys

# Evita UnicodeEncodeError al imprimir emojis en consolas Windows (cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

NOMBRE_BD = "productividad_estudiante.db"


def conectar():
    """Abre una conexion a la base de datos asegurando que la tabla existe.

    Devuelve la conexion lista para usarse. Centralizar aqui la creacion de
    la tabla evita el error 'no such table' si se ejecuta otro script antes
    de inicializar la base de datos.
    """
    conexion = sqlite3.connect(NOMBRE_BD)
    conexion.execute("PRAGMA foreign_keys = ON;")
    # Creacion de la base de datos
    conexion.execute('''
        CREATE TABLE IF NOT EXISTS sesiones_estudio(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE DEFAULT CURRENT_DATE,
            asignatura TEXT NOT NULL,
            horas_estudio REAL CHECK(horas_estudio >= 0 AND horas_estudio <= 16),
            nivel_concentracion INTEGER CHECK(nivel_concentracion BETWEEN 1 AND 10),
            horas_sueno REAL CHECK(horas_sueno >= 0 AND horas_sueno <= 24),
            hizo_ejercicio INTEGER CHECK(hizo_ejercicio IN (0, 1)),
            puntuacion_test REAL CHECK(puntuacion_test >= 0 AND puntuacion_test <= 100),
            origen TEXT DEFAULT 'manual'
        )
    ''')

    # Migracion para bases de datos creadas antes de existir la columna
    # 'origen': distingue datos sinteticos de sesiones registradas a mano.
    columnas = {fila[1] for fila in conexion.execute("PRAGMA table_info(sesiones_estudio)")}
    if "origen" not in columnas:
        conexion.execute(
            "ALTER TABLE sesiones_estudio ADD COLUMN origen TEXT DEFAULT 'manual'"
        )

    conexion.commit()
    return conexion


def inicializar_base_de_datos():
    conexion = conectar()
    conexion.close()
    print(f"✅ Base de datos '{NOMBRE_BD}' lista.")


if __name__ == "__main__":
    inicializar_base_de_datos()
