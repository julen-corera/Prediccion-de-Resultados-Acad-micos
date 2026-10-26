"""Genera un conjunto de datos sintetico de sesiones de estudio.

Los datos son inventados, pero siguen reglas realistas:

- El sueno tiene un optimo (~8 h). Dormir menos penaliza, y pasarse tampoco
  ayuda: a partir de 9 h cada hora extra resta. Asi el modelo puede aprender
  una curva en vez de una recta que siempre sube.
- La concentracion esta relacionada con el sueno, pero ya no es una copia
  suya: si lo fuera, el modelo no podria distinguir el efecto de cada una.
- El estudio y el ejercicio suman de forma lineal. Se deja el estudio lineal a
  proposito: el modelo solo tiene el cuadrado del sueno, y meter una curva en
  el estudio sin poder representarla lo dejaria mal especificado.

Uso:  python generar_datos.py
"""
import random
from datetime import datetime, timedelta

from setup_db import conectar

ASIGNATURAS = [
    "Estadistica Avanzada",
    "Visualizacion de datos",
    "Requisitos del Software",
    "Programacion IV",
    "Ciencia de datos",
]

SUENO_OPTIMO = 8.0
SUENO_MINIMO_SANO = 6.0
SUENO_MAXIMO_SANO = 9.0


def _rendimiento_sueno(horas_sueno):
    """Horas de sueno 'utiles': suben hasta el optimo y penalizan pasarse."""
    util = min(horas_sueno, SUENO_OPTIMO)
    if horas_sueno < SUENO_MINIMO_SANO:
        util -= 3.0 * (SUENO_MINIMO_SANO - horas_sueno)
    elif horas_sueno > SUENO_MAXIMO_SANO:
        util -= 2.5 * (horas_sueno - SUENO_MAXIMO_SANO)
    return util


def generar_datos_sintetico(n_dias=200, eliminar_previos=True):
    """Genera n_dias sesiones sinteticas (una por dia).

    Con eliminar_previos=True solo borra las filas marcadas como sinteticas:
    las sesiones registradas a mano con registrar_sesion.py no se tocan.
    """
    random.seed(42)  # reproducible: los mismos datos en cada ejecucion

    conexion = conectar()
    cursor = conexion.cursor()

    if eliminar_previos:
        borradas = cursor.execute(
            "DELETE FROM sesiones_estudio WHERE origen = 'sintetico'"
        ).rowcount
        if borradas:
            print(f"  (se han borrado {borradas} sesiones sinteticas anteriores)")

    fecha_inicio = datetime.now() - timedelta(days=n_dias)
    for i in range(n_dias):
        # Cubre los ultimos n_dias dias, terminando en la fecha de hoy
        fecha = (fecha_inicio + timedelta(days=i + 1)).date().isoformat()
        asignatura = random.choice(ASIGNATURAS)

        # Sueno realista: la mayoria duerme 6-9 h, pocos se van a los extremos
        sueno = round(min(11.0, max(4.0, random.gauss(7.5, 2.0))), 2)

        # El estudio se mueve en un rango normal (sin maratones de 14 h)
        horas_estudio = round(random.uniform(1, 6), 2)

        ejercicio = 1 if random.random() > 0.55 else 0

        # La concentracion depende del sueno, pero con ruido propio (correlacion
        # moderada, no una copia) para que el modelo pueda separar los efectos
        concentracion = 6.5 + 0.45 * (sueno - 7.5) + random.gauss(0, 1.6)
        concentracion = int(max(1, min(10, round(concentracion))))

        # Formula "real" que el modelo intentara descubrir
        nota_base = (
            7.0 * horas_estudio
            + 4.6 * _rendimiento_sueno(sueno)
            + 0.8 * concentracion
            + 6.0 * ejercicio
        )
        puntuacion = min(100, max(0, nota_base + random.uniform(-10, 10)))

        cursor.execute(
            """INSERT INTO sesiones_estudio
               (fecha, asignatura, horas_estudio, nivel_concentracion,
                horas_sueno, hizo_ejercicio, puntuacion_test, origen)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'sintetico')""",
            (
                fecha,
                asignatura,
                horas_estudio,
                concentracion,
                sueno,
                ejercicio,
                round(puntuacion, 2),
            ),
        )

    conexion.commit()
    conexion.close()
    print(f"✅ {n_dias} sesiones sinteticas generadas.")


if __name__ == "__main__":
    generar_datos_sintetico()
