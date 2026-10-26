"""Entrena el modelo de regresion lineal y guarda el resultado en disco.

Uso:  python entrenar_modelo.py
"""
from modelo import FEATURES, OBJETIVO, entrenar, guardar_modelo


def main():
    print(f"Entrenando modelo para predecir '{OBJETIVO}'...")
    try:
        modelo, metricas = entrenar()
    except ValueError as e:
        print(f"❌ {e}")
        return

    print("\n--- Metricas (sobre el conjunto de prueba) ---")
    print(f"Muestras totales        : {metricas['n_muestras']}")
    print(f"  - entrenamiento       : {metricas['n_entrenamiento']}")
    print(f"  - prueba              : {metricas['n_prueba']}")
    print(f"MAE  (error medio)      : {metricas['mae']:.2f} puntos")
    print(f"RMSE (error tipico)     : {metricas['rmse']:.2f} puntos")
    print(f"R2   (bondad de ajuste) : {metricas['r2']:.3f}")

    print("\n--- Coeficientes aprendidos ---")
    print(f"Intercepto: {modelo.intercept_:+.2f}")
    coefs = dict(zip(FEATURES, modelo.coef_))
    for nombre in FEATURES:
        print(f"  {nombre:22s}: {coefs[nombre]:+.3f}")

    pendiente = coefs.get("horas_sueno")
    curvatura = coefs.get("horas_sueno_cuadrado")
    if pendiente is not None and curvatura is not None and curvatura < 0:
        optimo = -pendiente / (2 * curvatura)
        print(f"\nOptimo estimado de sueno: {optimo:.1f} h/dia")
        print("(a partir de ahi, cada hora extra de sueno resta nota)")

    guardar_modelo(modelo)
    print("\n✅ Modelo guardado en 'modelo_regresion.joblib'")


if __name__ == "__main__":
    main()
