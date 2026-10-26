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

6. Generar un plan de mejora personalizado (agente planificador):

   ```bash
   python agente_planificador.py
   python agente_planificador.py --json   # mismo plan en JSON (para otra capa/UI)
   ```

La tabla `sesiones_estudio` se crea automáticamente al usar cualquier script,
por lo que no es imprescindible ejecutar `setup_db.py` antes.

## Estructura
- `setup_db.py`: conexión y creación de la tabla `sesiones_estudio`.
- `generar_datos.py`: genera observaciones sintéticas con reglas realistas.
- `registrar_sesion.py`: registro interactivo de una sesión de estudio.
- `modelo.py`: lógica del modelo (features, carga de datos, entrenamiento, predicción).
- `entrenar_modelo.py`: entrena la regresión, muestra métricas y el óptimo de sueño.
- `predecir.py`: predice la nota a partir de datos introducidos por el usuario.
- `agente_planificador.py`: diagnóstico de la nota y plan de acciones priorizado.

## Modelo
Regresión lineal que predice `puntuacion_test` a partir de `horas_estudio`,
`nivel_concentracion`, `horas_sueno` y `hizo_ejercicio`, **más el cuadrado de
las horas de sueño**. Se evalúa con MAE, RMSE y R².

El término `horas_sueno²` es lo que le permite aprender que el sueño tiene un
óptimo: con una recta, cada hora extra sumaba siempre lo mismo y el modelo
acababa diciendo que dormir 12 h era mejor que dormir 8. Con los datos
actuales el óptimo estimado es **8,0 h/día**, y a partir de ahí cada hora resta.

> Los coeficientes de un polinomio no se interpretan por separado (dependen
> unos de otros). Lo interpretable es el **óptimo** y el **efecto marginal**
> (`coef_sueño + 2 · coef_sueño² · horas_sueno`), que es lo que usa el agente.

## Datos sintéticos
`generar_datos.py` genera 200 sesiones con reglas realistas: el sueño sube
hasta ~8 h y luego penaliza, la concentración está correlacionada con el sueño
pero ya no es una copia suya, y el estudio y el ejercicio suman de forma
lineal. Cada fila se marca con `origen = 'sintetico'`, así que volver a
ejecutar el script **solo reemplaza los datos sintéticos** y respeta las
sesiones registradas a mano con `registrar_sesion.py`.

Métricas actuales (200 filas, split 80/20): MAE 5,1 puntos · RMSE 5,9 ·
R² 0,860. Son peores que las de la versión anterior (R² 0,894) y es lo
esperado: los datos viejos eran una recta perfecta y el modelo se limitaba a
copiarla.

## Agente planificador
`agente_planificador.py` convierte la predicción en un plan concreto:

1. **Diagnóstico**: descompone la nota en `nivel base` (alumno medio) +
   contribución de cada variable, y calcula el margen de mejora de cada una.
2. **Plan**: elige acciones de un catálogo (estudio activo, sueño, ejercicio,
   concentración) priorizando **puntos ganados / esfuerzo**. Tras cada acción
   vuelve a simular con el modelo, y se detiene al alcanzar el objetivo o al
   agotar el presupuesto de acciones.
3. **Verificación**: muestra la nota estimada tras el plan y avisa con
   honestidad si el objetivo no es alcanzable con estas cuatro variables.

El agente **no inventa cifras**: cada acción se valora con el modelo, así que
los puntos que muestra son siempre coherentes con él. La salida `--json` está
pensada para enchufar después una capa de redacción (LLM) o una interfaz.

El plan puede subir o bajar una variable. Si alguien duerme 11 h, el agente
recomienda **ajustar el sueño a ~8 h** (y lo valora con el modelo), no "dormir
más". Si duerme 9 h — dentro del rango sano — no dice nada.

> Aviso: los datos son sintéticos, así que las cifras ilustran el
> funcionamiento, no son una estimación real.

## Próximos pasos
- Añadir `horas_estudio²` (o pasar a un modelo de árboles) para que el estudio
  también tenga rendimiento decreciente sin depender de una regla del agente.
- Incluir `asignatura` como variable categórica (OneHotEncoder).
- Usar validación cruzada (KFold) en vez de un único split 80/20.
- Guardar con el modelo su metadata (features, métricas y fecha de entrenamiento).
- Registrar lo que predice el agente y la nota real para reentrenar (bucle de
  mejora) y medir si las recomendaciones funcionan.
- Añadir una capa opcional de redacción (LLM) sobre la salida `--json` del
  planificador; el cálculo de puntos se queda siempre en el modelo.
