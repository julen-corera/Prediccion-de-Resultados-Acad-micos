# Prediccion-de-Resultados-Acad-micos
Programa de predicción de resultados en diversas asignaturas mediante algoritmos de machine learning.

## Requisitos
- Python 3 (probado con Python 3.12).
- `scikit-learn` (se instala con `pip`; incluye `numpy` y `joblib`):

  ```bash
  pip install -r requirements.txt
  ```

## Uso

1. Inicializar la base de datos (crea `productividad_estudiante.db`):

   ```bash
   python setup_db.py
   ```

2. (Opcional) Generar datos sintéticos de ejemplo:

   ```bash
   python generar_datos.py
   ```

3. Registrar una sesión de estudio manualmente:

   ```bash
   python registrar_sesion.py
   ```

4. Entrenar el modelo de regresión lineal (guarda `modelo_regresion.joblib`):

   ```bash
   python entrenar_modelo.py
   ```

5. Predecir la puntuación de un test:

   ```bash
   python predecir.py
   ```

La tabla `sesiones_estudio` se crea automáticamente al usar cualquier script,
por lo que no es imprescindible ejecutar `setup_db.py` antes.

## Estructura
- `setup_db.py`: conexión y creación de la tabla `sesiones_estudio`.
- `generar_datos.py`: genera observaciones sintéticas con cierta correlación.
- `registrar_sesion.py`: registro interactivo de una sesión de estudio.
- `modelo.py`: lógica del modelo (carga de datos, entrenamiento, predicción).
- `entrenar_modelo.py`: entrena la regresión lineal y muestra sus métricas.
- `predecir.py`: predice la nota a partir de datos introducidos por el usuario.

## Modelo
Regresión lineal que predice `puntuacion_test` a partir de `horas_estudio`,
`nivel_concentracion`, `horas_sueno` y `hizo_ejercicio`. Se evalúa con MAE,
RMSE y R².

## Próximos pasos
- Incluir `asignatura` como variable categórica (OneHotEncoder).
- Probar otros modelos (árboles, gradient boosting) y comparar métricas.
- Añadir un agente de IA que sugiera mejoras a partir de las predicciones.
