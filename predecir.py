"""Predice la puntuacion de un test a partir de datos introducidos por el usuario.

Uso:  python predecir.py   (requiere haber entrenado antes con entrenar_modelo.py)
"""
from modelo import cargar_modelo, predecir


def pedir_valor(mensaje, minimo, maximo, entero=False):
    while True:
        try:
            valor = float(input(mensaje))
        except ValueError:
            print("  Introduce un numero valido.")
            continue
        if not (minimo <= valor <= maximo):
            print(f"  El valor debe estar entre {minimo} y {maximo}.")
            continue
        return int(valor) if entero else valor


def main():
    print("--- Prediccion de la puntuacion de un test ---")
    try:
        modelo = cargar_modelo()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return

    horas_estudio = pedir_valor("Horas de estudio (0-16): ", 0, 16)
    nivel_conc = pedir_valor("Nivel de concentracion (1-10): ", 1, 10, entero=True)
    horas_sueno = pedir_valor("Horas de sueno (0-24): ", 0, 24)
    hizo_ejercicio = pedir_valor("¿Has hecho ejercicio? (1 Si / 0 No): ", 0, 1, entero=True)

    nota = predecir(modelo, horas_estudio, nivel_conc, horas_sueno, hizo_ejercicio)
    print(f"\n📈 Puntuacion estimada del test: {nota:.1f} / 100")


if __name__ == "__main__":
    main()
