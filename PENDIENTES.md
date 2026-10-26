# Pendientes

Guía de las dos tareas que faltan para que el proyecto pase de "funciona" a
"demostrado". Están ordenadas: la 1 primero, porque es más barata y da
credibilidad inmediata.

Estado de partida (por si vuelves dentro de un mes):

- `modelo.py` usa 5 features: las 4 variables + `horas_sueno²`.
- Última tanda: R² 0,860 · MAE 5,11 · RMSE 5,91 con un split 80/20 (200 filas).
- Óptimo de sueño aprendido: 8,0 h/día.
- `agente_planificador.py` funciona y está validado con 224 perfiles.
- Los datos siguen siendo sintéticos: sirven para probar el pipeline, no para
  afirmar nada sobre estudiantes reales.

---

## Tarea 1 — Demostrar que `horas_sueno²` merece la pena

### Objetivo

Hoy "el cuadrado mejora el modelo" es una **afirmación**. Al terminar esta
tarea tiene que ser una **medida**: "con el cuadrado, el MAE baja de X a Y y el
R² sube de A a B, con validación cruzada de 5 folds".

### Qué hacer

1. **Añadir validación cruzada** en `modelo.py`:

   ```python
   from sklearn.model_selection import KFold, cross_validate

   def evaluar_cv(modelo, X, y, n_splits=5):
       """Metricas medias con validacion cruzada (mas fiable que un split)."""
       cv = KFold(n_splits=n_splits, shuffle=True, random_state=42)
       res = cross_validate(
           modelo, X, y, cv=cv,
           scoring={
               "mae": "neg_mean_absolute_error",
               "rmse": "neg_root_mean_squared_error",
               "r2": "r2",
           },
       )
       return {
           "mae": -res["test_mae"].mean(),
           "rmse": -res["test_rmse"].mean(),
           "r2": res["test_r2"].mean(),
           "r2_std": res["test_r2"].std(),
       }
   ```

2. **Poder elegir features**, para comparar con y sin el cuadrado. Cambia
   `construir_entrada` y `cargar_datos` para aceptar una lista de nombres:

   ```python
   def construir_entrada(perfil, features=None):
       spec = _FEATURES if features is None else [
           (n, f) for n, f in _FEATURES if n in features
       ]
       return np.array([[calculo(perfil) for _, calculo in spec]], dtype=float)
   ```

3. **Comparar las dos variantes** en un script nuevo (`comparar_modelos.py`)
   o dentro de `entrenar_modelo.py`:

   ```python
   SIN_CUADRADO = ["horas_estudio", "nivel_concentracion", "horas_sueno", "hizo_ejercicio"]
   CON_CUADRADO = None  # todas las features
   ```

4. **Opcional pero muy recomendable**: añade un tercer contendiente,
   `GradientBoostingRegressor()`, con las mismas features. Si gana por mucho,
   tienes el argumento para el siguiente paso (modelo de árboles).

### Criterio de aceptación

Una tabla como esta, con las tres filas rellenas y una conclusión escrita:

| Variante | MAE | RMSE | R² (media ± sd) |
|---|---|---|---|
| Lineal sin `sueño²` | | | |
| Lineal con `sueño²` | | | |
| GradientBoosting (opcional) | | | |

- [ ] El mismo `KFold` (mismo `random_state`) para todas las variantes.
- [ ] La conclusión está escrita en el README o en la memoria.
- [ ] Si el cuadrado **no** mejora, se documenta y se replantea (no se oculta).

### Trampas

- **No compares contra el 0,860 actual**: ese número es de un split único. Para
  comparar hay que recalcular **las dos** variantes con CV.
- No uses `cross_val_score` con datos ya transformados de forma distinta en
  cada variante.
- Con 200 filas, 5 folds son 40 de test por fold. Es aceptable, pero reporta la
  desviación (`r2_std`); si es grande, el resultado es frágil.

---

## Tarea 2 — `asignatura` y unidad de análisis

### 2.a Decidir la unidad de análisis (hazlo antes de programar)

Hoy **cada fila es un día** con una nota de test. Eso es raro. Tienes dos
opciones y hay que elegir una y dejarla escrita:

- **Opción A — la fila es una sesión/día de estudio.** Es lo que hay. Ventaja:
  no hay que tocar nada. Inconveniente: "nota del test de ese día" no existe en
  la realidad; un examen no se hace todos los días.
- **Opción B — la fila es un examen.** Cada fila es un examen, y las features
  son agregados de los días previos (media de horas de estudio, media de sueño,
  concentración media...). Es lo realista, pero obliga a rediseñar la tabla.

**Recomendación**: quédate con A mientras el proyecto sea una demo del pipeline
y **documenta la limitación**. Si el proyecto va a seguir con datos reales, la
B es el camino; mejor decidirlo ahora que rehacer la tabla después.

### 2.b Guardar metadata del modelo (prerrequisito de 2.c)

Si añades `asignatura`, necesitas saber **qué asignaturas** existían al
entrenar. Si no lo guardas, al predecir no puedes construir la misma entrada.
Cambia lo que se guarda en `guardar_modelo` / `cargar_modelo`:

```python
artefacto = {
    "modelo": modelo,
    "features": FEATURES,
    "asignaturas": ASIGNATURAS,   # orden exacto de las columnas one-hot
    "metricas": metricas,
    "fecha": datetime.now().isoformat(),
}
joblib.dump(artefacto, RUTA_MODELO)
```

Esto obliga a tocar `predecir` y `simular` (ahora reciben el artefacto). Es el
momento de hacerlo: con un modelo de 4 features no lo necesitabas, con
categóricas sí.

### 2.c Añadir `asignatura`

1. **Sacar la lista de asignaturas** de la BD (no la escribas a mano):

   ```python
   def cargar_asignaturas():
       conexion = conectar()
       filas = conexion.execute(
           "SELECT DISTINCT asignatura FROM sesiones_estudio ORDER BY asignatura"
       ).fetchall()
       conexion.close()
       return [f[0] for f in filas]
   ```

2. **One-hot manual** (sin añadir pandas). Deja la primera como categoría de
   referencia para no duplicar el intercepto:

   ```python
   def _one_hot(asignatura, asignaturas):
       return [1.0 if asignatura == a else 0.0 for a in asignaturas[1:]]
   ```

   Añade esas columnas en `construir_entrada`. Con 5 asignaturas son 4 columnas
   nuevas.

3. **Actualizar los tres sitios que construyen un perfil**:
   - `predecir.py`: preguntar la asignatura (elige de una lista, no texto libre).
   - `registrar_sesion.py`: elegir de la lista, para que no entren erratas que
     creen categorías nuevas.
   - `agente_planificador.py`: `simular` debe recibir la asignatura en el perfil.

4. **Cuidado con el agente**: `VARIABLES` son las palancas que el plan puede
   mover. `asignatura` **no** es una palanca (no eliges la asignatura), es
   contexto. No la metas en `VARIABLES` ni en `REFERENCIAS`, o el agente
   intentará "subirla".

### Criterio de aceptación

- [ ] El modelo con `asignatura` tiene métricas CV mejores o iguales que sin ella.
- [ ] Una asignatura desconocida no rompe: se trata como la categoría de
      referencia y se avisa.
- [ ] El `.joblib` guarda la lista de asignaturas y su orden.
- [ ] `predecir.py` y `agente_planificador.py` siguen funcionando de punta a punta.
- [ ] `registrar_sesion.py` solo acepta asignaturas de la lista.

### Trampas

- **One-hot fuera del pipeline y guardar solo el modelo**: al predecir no sabes
  el orden de las columnas y las predicciones salen mal en silencio. Por eso el
  punto 2.b.
- **`registrar_sesion.py` con texto libre**: "Programacion IV" y
  "programacion iv" son dos categorías distintas. Cerrado con lista.
- **Meter `asignatura` en `VARIABLES`**: rompe la lógica del agente.

---

## Checklist final

- [ ] Tarea 1 terminada y tabla de comparación en la documentación.
- [ ] Unidad de análisis decidida y escrita.
- [ ] Metadata del modelo guardada.
- [ ] `asignatura` integrada en modelo, `predecir` y agente.
- [ ] `python generar_datos.py && python entrenar_modelo.py` sigue funcionando.
- [ ] Commit.

## Después de esto (no ahora)

1. Bucle de feedback: guardar predicción/plan + nota real y medir acierto.
2. Aviso de extrapolación en `predecir.py` (hoy 16 h de sueño dan 0).
3. Tests automáticos (`unittest`) del agente y del modelo.
4. Datos reales. Es el techo del proyecto: sin ellos todo esto es una demo.
