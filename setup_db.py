import sqlite3

def inicializar_base_de_datos():
    conexion = sqlite3.connect("productividad_estudiante.db")
    conexion.execute("PRAGMA foreign_keys = ON;")
    cursor = conexion.cursor()
    #Creacion de la base de datos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sesiones_estudio(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE DEFAULT CURRENT_DATE,
            asignatura VARCHAR(10) NOT NULL,
            horas_estudio REAL CHECK(horas_estudio>=0 AND horas_estudio<=16),
            nivel_concentracion INTEGER CHECK(nivel_concentracion BETWEEN 1 AND 10),
            horas_sueno REAL CHECK(horas_sueno >= 0 AND horas_sueno <= 24),
            hizo_ejercicio INT CHECK(hizo_ejercicio IN (0,1));
            puntuacion_test REAL CHECK(puntuacion_test >= 0 AND puntuacion_test <=100);
        )
    ''')