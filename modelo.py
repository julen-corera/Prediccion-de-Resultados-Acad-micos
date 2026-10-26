"""Logica del modelo de regresion lineal.

Predice la puntuacion de un test (puntuacion_test) a partir de las
caracteristicas de una sesion de estudio (horas de estudio, concentracion,
horas de sueno y si se hizo ejercicio).

Ademas de las cuatro variables se usa el cuadrado de las horas de sueno. Con
una recta, cada hora extra de sueno sumaba siempre lo mismo y el modelo
acababa diciendo que dormir 12 h es mejor que dormir 8. El termino cuadratico
le permite aprender que existe un optimo y que pasarse penaliza.
"""
import os

import joblib
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from setup_db import conectar

# Variables que el usuario introduce y que se guardan en la BD.
VARIABLES = ["horas_estudio", "nivel_concentracion", "horas_sueno", "hizo_ejercicio"]

# Variable objetivo.
OBJETIVO = "puntuacion_test"

# Features que ve el modelo, en orden. Es la unica fuente de verdad: el
# entrenamiento, la prediccion y el agente construyen la entrada con
# construir_entrada(), asi que no pueden desincronizarse.
_FEATURES = [
    ("horas_estudio", lambda p: p["horas_estudio"]),
    ("nivel_concentracion", lambda p: p["nivel_concentracion"]),
    ("horas_sueno", lambda p: p["horas_sueno"]),
    ("horas_sueno_cuadrado", lambda p: p["horas_sueno"] ** 2),
    ("hizo_ejercicio", lambda p: p["hizo_ejercicio"]),
]
FEATURES = [nombre for nombre, _ in _FEATURES]

RUTA_MODELO = "modelo_regresion.joblib"


def construir_entrada(perfil):
    """Convierte un perfil (dict con las VARIABLES) en la matriz del modelo."""
    return np.array(
        [[calculo(perfil) for _, calculo in _FEATURES]],
        dtype=float,
    )


def cargar_datos_base():
    """Lee la tabla y devuelve (X_base, y) con las variables sin transformar."""
    conexion = conectar()
    cursor = conexion.cursor()
    columnas = ", ".join(VARIABLES + [OBJETIVO])
    # 'columnas' proviene de constantes del propio modulo, no de entrada del usuario
    filas = cursor.execute(f"SELECT {columnas} FROM sesiones_estudio").fetchall()
    conexion.close()

    datos = np.array(filas, dtype=float)
    if datos.size == 0:
        raise ValueError(
            "La base de datos esta vacia. Genera datos con generar_datos.py "
            "o registra sesiones con registrar_sesion.py antes de entrenar."
        )
    return datos[:, : len(VARIABLES)], datos[:, len(VARIABLES)]


def cargar_datos():
    """Lee la tabla y devuelve (X, y) con las features que ve el modelo."""
    X_base, y = cargar_datos_base()
    X = np.vstack(
        [construir_entrada(dict(zip(VARIABLES, fila))) for fila in X_base]
    )
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
    modelo = joblib.load(ruta)

    # Evita el fallo silencioso: un modelo entrenado con otras features daria
    # predicciones mal sin avisar.
    n_features = getattr(modelo, "n_features_in_", len(FEATURES))
    if n_features != len(FEATURES):
        raise ValueError(
            f"El modelo guardado espera {n_features} features y el codigo actual "
            f"usa {len(FEATURES)}. Reentrena con 'entrenar_modelo.py'."
        )
    return modelo


def predecir(modelo, horas_estudio, nivel_concentracion, horas_sueno, hizo_ejercicio):
    """Devuelve la nota estimada (0-100) para una sesion de estudio."""
    perfil = {
        "horas_estudio": horas_estudio,
        "nivel_concentracion": nivel_concentracion,
        "horas_sueno": horas_sueno,
        "hizo_ejercicio": hizo_ejercicio,
    }
    nota = float(modelo.predict(construir_entrada(perfil))[0])
    # La nota real esta acotada entre 0 y 100, acotamos tambien la prediccion
    return max(0.0, min(100.0, nota))
