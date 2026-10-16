import random
from datetime import datetime, timedelta

from setup_db import conectar

'''Este código está hecho con ayuda de inteligencia artificial generativa, su propósito 
es crear un conjunto de datos (observaciones) de manera manual, sin la necesidad de tener que 
registrarlo personalmente. La generacion de estos datos mantiene una correlacion a la hora de calcular
el resultado (nota)
'''


def generar_datos_sintetico(n_dias=60):
    # Asegura que la tabla existe antes de insertar
    conexion = conectar()
    cursor = conexion.cursor()

    asignaturas = ['Estadistica Avanzada', 'Visualizacion de datos',
                   'Requisitos del Software', 'Programacion IV', 'Ciencia de datos']
    fecha_inicio = datetime.now() - timedelta(days=n_dias)
    for i in range(n_dias):
        # Cubre los ultimos n_dias dias, terminando en la fecha de hoy
        fecha = (fecha_inicio + timedelta(days=i + 1)).date().isoformat()
        asig = random.choice(asignaturas)

        #Lógica con correlacion (para que el modelo tenga sentido)
        sueno = random.uniform(4, 9)  # 4-9 horas
        ejercicio = 1 if random.random() > 0.6 else 0

        #Las horas de estudio dependen de la asignatura
        horas_estudio = random.uniform(1, 6)

        #La concentracion dependera de las horas de sueno
        concentracion = int(min(10, (sueno * 1.1) + random.randint(-2, 1)))
        concentracion = max(1, concentracion)

        #La nota depende del estudio, las horas de sueno y el ejercicio, mas algo de azar
        #Esta es la "formula" que luego nuestro modelo (IA) intentara descubrir luego
        nota_base = (horas_estudio * 10) + (sueno * 5) + (ejercicio * 10)
        puntuacion = min(100, max(0, nota_base + random.randint(-10, 10)))  # Minimo entre 100 y la nota base mas algo de ruido (o 0 si la nota es negativa)

        sql = ('''
            INSERT INTO sesiones_estudio
            (fecha, asignatura, horas_estudio, nivel_concentracion, horas_sueno, hizo_ejercicio, puntuacion_test)
            VALUES (?, ?, ?, ?, ?, ?, ?)''')
        cursor.execute(sql, (fecha, asig, round(horas_estudio, 2), concentracion,
                             round(sueno, 2), ejercicio, round(puntuacion, 2)))
    conexion.commit()
    conexion.close()
    print(f"✅ Se han generado {n_dias} días de datos realistas.")


if __name__ == "__main__":
    generar_datos_sintetico()
