"""Logica del modelo de regresion lineal.

Predice la puntuacion de un test (puntuacion_test) a partir de las
caracteristicas de una sesion de estudio (horas de estudio, concentracion,
horas de sueno y si se hizo ejercicio).
"""
import os

import joblib
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from setup_db import conectar

# Variables de entrada (X) y variable objetivo (y)
FEATURES = ["horas_estudio", "nivel_concentracion", "horas_sueno", "hizo_ejercicio"]
OBJETIVO = "puntuacion_test"

RUTA_MODELO = "modelo_regresion.joblib"


def cargar_datos():
    """Lee la tabla sesiones_estudio y devuelve (X, y) como arrays de numpy."""
    conexion = conectar()
    cursor = conexion.cursor()
    columnas = ", ".join(FEATURES + [OBJETIVO])
    # 'columnas' proviene de constantes del propio modulo, no de entrada del usuario
    filas = cursor.execute(f"SELECT {columnas} FROM sesiones_estudio").fetchall()
    conexion.close()

    if not filas:
        raise ValueError(
            "La base de datos esta vacia. Genera datos con generar_datos.py "
            "o registra sesiones con registrar_sesion.py antes de entrenar."
        )

    datos = np.array(filas, dtype=float)
    X = datos[:, :len(FEATURES)]
    y = datos[:, len(FEATURES)]
    return X, y


def entrenar(test_size=0.2, random_state=42):
    """Entrena una regresion lineal y devuelve (modelo, metricas)."""
    X, y = cargar_datos()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    modelo = LinearRegression()
    modelo.fit(X_train, y_train)

    predicciones = modelo.predict(X_test)
    metricas = {
        "n_muestras": len(y),
        "n_entrenamiento": len(y_train),
        "n_prueba": len(y_test),
        "mae": mean_absolute_error(y_test, predicciones),
        "rmse": mean_squared_error(y_test, predicciones) ** 0.5,
        "r2": r2_score(y_test, predicciones),
    }
    return modelo, metricas


def guardar_modelo(modelo, ruta=RUTA_MODELO):
    joblib.dump(modelo, ruta)


def cargar_modelo(ruta=RUTA_MODELO):
    if not os.path.exists(ruta):
        raise FileNotFoundError(
            f"No se encontro el modelo '{ruta}'. Entrena primero con 'entrenar_modelo.py'."
        )
    return joblib.load(ruta)


def predecir(modelo, horas_estudio, nivel_concentracion, horas_sueno, hizo_ejercicio):
    """Devuelve la nota estimada (0-100) para una sesion de estudio."""
    entrada = np.array(
        [[horas_estudio, nivel_concentracion, horas_sueno, hizo_ejercicio]], dtype=float
    )
    nota = float(modelo.predict(entrada)[0])
    # La nota real esta acotada entre 0 y 100, acotamos tambien la prediccion
    return max(0.0, min(100.0, nota))
