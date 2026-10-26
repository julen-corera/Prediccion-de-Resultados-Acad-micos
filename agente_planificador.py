"""Agente 2: planificador de mejoras academicas.

Convierte el diagnostico del modelo de regresion lineal en un plan de accion
concreto, priorizado y verificado contra el propio modelo.

Reparto de responsabilidades:
  - El modelo pone los numeros: cuanto vale cada variable (sus coeficientes).
  - Este agente pone el conocimiento de *que hacer* (catalogo de acciones) y
    comprueba el resultado simulando el plan con el modelo.

Regla de oro: el agente no inventa cifras. Cada accion se valora volviendo a
predecir con el modelo, asi que las cifras son siempre coherentes con el.

Uso:
    python agente_planificador.py          # plan en texto
    python agente_planificador.py --json   # plan en JSON (para otra capa/UI)
"""
import contextlib
import json
import sys

from modelo import VARIABLES, construir_entrada, cargar_datos_base, cargar_modelo
from predecir import pedir_valor

# Rango realista/saludable de cada variable. No usamos el maximo legal de la
# base de datos (p.ej. 16 h de estudio) porque el modelo es lineal y saturaria:
# dormir 11 h o estudiar 12 h no mejora nada en la vida real.
REFERENCIAS = {
    "horas_estudio": {"objetivo": 4.0, "max": 6.0, "unidad": "h/dia"},
    "nivel_concentracion": {"objetivo": 8.0, "max": 10.0, "unidad": "/10"},
    "horas_sueno": {"objetivo": 8.0, "max": 9.0, "unidad": "h/dia"},
    "hizo_ejercicio": {"objetivo": 1.0, "max": 1.0, "unidad": "0/1"},
}

# Nombre legible de cada variable, para los textos del plan.
ETIQUETAS = {
    "horas_estudio": "horas de estudio",
    "nivel_concentracion": "nivel de concentracion",
    "horas_sueno": "horas de sueno",
    "hizo_ejercicio": "ejercicio",
}

# Catalogo de acciones por variable, de mas a menos prioritaria dentro de cada
# una. 'delta' es cuanto sube la variable; 'efectos' son efectos secundarios
# asumidos (documentados en 'detalle'); 'coste' es esfuerzo percibido 1-5.
ACCIONES = {
    "horas_estudio": [
        {
            "id": "estudio_bloques",
            "titulo": "Estudio activo en bloques de 50 min",
            "delta": 1.0,
            "coste": 3,
            "plazo": "2 semanas",
            "detalle": (
                "Cambia releer por recuperacion activa: cierra los apuntes y "
                "explicita el tema en voz alta o hazte preguntas. 3 bloques de "
                "50 min con 10 de descanso rinden mas que 3 h seguidas."
            ),
            "efectos": {},
        },
        {
            "id": "estudio_espaciado",
            "titulo": "Repaso espaciado (3 toques por tema)",
            "delta": 0.5,
            "coste": 2,
            "plazo": "3-4 semanas",
            "detalle": (
                "Reparte cada tema en 3 repasos cortos (hoy, a los 2 dias y a "
                "la semana) en vez de un repaso largo la vispera. Es la tecnica "
                "con mas evidencia para retener a largo plazo."
            ),
            "efectos": {},
        },
        {
            "id": "estudio_sin_movil",
            "titulo": "Sesiones sin movil ni pestanas",
            "delta": 0.5,
            "coste": 2,
            "plazo": "1 semana",
            "detalle": (
                "Deja el movil en otra habitacion durante los bloques. Cada "
                "interrupcion cuesta unos 20 min recuperar el foco, asi que "
                "quitar 4-5 interrupciones ya es media hora ganada."
            ),
            "efectos": {},
        },
    ],
    "horas_sueno": [
        {
            "id": "sueno_horario",
            "titulo": "Horario de sueno constante",
            "delta": 1.0,
            "coste": 2,
            "plazo": "2 semanas",
            "detalle": (
                "Acuestate y levantate a la misma hora (tambien el finde) y "
                "adelanta 30-45 min la hora de acostarte. Dormir bien es la "
                "palanca mas barata para concentrarte: por eso este cambio "
                "tambien sube la concentracion (+1)."
            ),
            "efectos": {"nivel_concentracion": 1.0},
        },
        {
            "id": "sueno_pantallas",
            "titulo": "Sin pantallas la ultima hora",
            "delta": 0.5,
            "coste": 1,
            "plazo": "1 semana",
            "detalle": (
                "Baja la luz y deja las pantallas 60 min antes de dormir: la "
                "luz azul retrasa la melatonina y te cuesta mas conciliar el "
                "sueno."
            ),
            "efectos": {},
        },
    ],
    "hizo_ejercicio": [
        {
            "id": "ejercicio_aerobico",
            "titulo": "20-30 min de ejercicio aerobico, 3 veces por semana",
            "delta": 1.0,
            "coste": 2,
            "plazo": "3 semanas",
            "detalle": (
                "Caminar rapido, correr o bici 3 veces por semana. Mejora el "
                "sueno y el estado de animo, y por eso tambien aporta algo de "
                "concentracion (+0.5) de forma indirecta."
            ),
            "efectos": {"nivel_concentracion": 0.5},
        },
    ],
    "nivel_concentracion": [
        {
            "id": "concentracion_entorno",
            "titulo": "Entorno y notificaciones a cero",
            "delta": 2.0,
            "coste": 3,
            "plazo": "1 semana",
            "detalle": (
                "Modo avion, notificaciones silenciadas y mesa despejada. Antes "
                "de empezar, escribe en un papel la unica tarea del bloque."
            ),
            "efectos": {},
        },
        {
            "id": "concentracion_pomodoro",
            "titulo": "Pomodoro 25/5",
            "delta": 1.0,
            "coste": 2,
            "plazo": "1 semana",
            "detalle": (
                "25 min de foco total y 5 de descanso real (sin pantallas). "
                "Cada 4 bloques, descanso largo de 20 min."
            ),
            "efectos": {},
        },
    ],
}


def simular(modelo, perfil):
    """Predice la nota de un perfil, acotada a 0-100 (igual que modelo.predecir)."""
    nota = float(modelo.predict(construir_entrada(perfil))[0])
    return max(0.0, min(100.0, nota))


def medias_entrenamiento():
    """Perfil medio de los datos de entrenamiento (referencia del diagnostico)."""
    X_base, _ = cargar_datos_base()
    return {v: float(X_base[:, i].mean()) for i, v in enumerate(VARIABLES)}


def _capacidad(perfil, variable):
    """Cuanto puede moverse la variable hacia su objetivo.

    Positivo si esta por debajo (hay que subir). Negativo solo si se pasa del
    maximo realista (hay que bajar). Cero si ya esta en un valor aceptable.
    """
    ref = REFERENCIAS[variable]
    hueco = ref["objetivo"] - perfil[variable]
    if hueco < 0 and perfil[variable] > ref["max"]:
        return hueco
    return max(0.0, hueco)


def diagnostico(modelo, perfil, referencia=None):
    """Descompone la nota y calcula el margen de mejora de cada variable.

    La prediccion se parte en 'nivel base' (perfil de referencia) + la
    contribucion de cada variable. Cada contribucion se obtiene simulando el
    modelo con esa variable cambiada, asi el diagnostico sigue siendo correcto
    aunque el modelo tenga terminos cuadraticos.
    """
    if referencia is None:
        referencia = medias_entrenamiento()

    base = simular(modelo, referencia)
    nota = simular(modelo, perfil)

    contribuciones = {}
    for variable in VARIABLES:
        perfil_var = dict(referencia)
        perfil_var[variable] = perfil[variable]
        contribuciones[variable] = simular(modelo, perfil_var) - base

    huecos = []
    for variable in VARIABLES:
        ref = REFERENCIAS[variable]
        capacidad = _capacidad(perfil, variable)
        if abs(capacidad) < 1e-9:
            puntos = 0.0
        else:
            perfil_objetivo = dict(perfil)
            perfil_objetivo[variable] = perfil[variable] + capacidad
            puntos = simular(modelo, perfil_objetivo) - nota
        huecos.append(
            {
                "variable": variable,
                "actual": perfil[variable],
                "objetivo": ref["objetivo"],
                "capacidad": capacidad,
                "puntos": puntos,
                "unidad": ref["unidad"],
            }
        )
    huecos.sort(key=lambda h: h["puntos"], reverse=True)

    return {
        "nota": nota,
        "base": base,
        "referencia": dict(referencia),
        "contribuciones": contribuciones,
        "huecos": huecos,
    }


def _aplicar(perfil, variable, accion):
    """Aplica una accion (y sus efectos secundarios) respetando los topes."""
    tope = REFERENCIAS[variable]["max"]
    perfil[variable] = max(0.0, min(tope, perfil[variable] + accion["delta"]))
    for otra, delta in accion["efectos"].items():
        tope_otra = REFERENCIAS[otra]["max"]
        perfil[otra] = max(0.0, min(tope_otra, perfil[otra] + delta))


def _techo_realista(modelo):
    """Mejor nota si las cuatro variables estuvieran en su objetivo saludable.

    Es el escenario "todo bien hecho" que el plan puede proponer; no usamos los
    maximos legales porque el plan tampoco los recomienda.
    """
    perfil_objetivo = {v: REFERENCIAS[v]["objetivo"] for v in VARIABLES}
    return simular(modelo, perfil_objetivo)


def _siguiente_accion(variable, aplicadas, capacidad):
    """Siguiente paso para acercar la variable a su objetivo.

    Si se pasa del rango saludable (capacidad negativa) devuelve un ajuste que
    la devuelve al objetivo; si no, el siguiente escalon del catalogo.
    """
    if capacidad < 0:
        ref = REFERENCIAS[variable]
        return {
            "id": f"ajuste_{variable}",
            "titulo": (
                f"Ajusta {ETIQUETAS[variable]} a ~{ref['objetivo']:g} "
                f"{ref['unidad']}"
            ),
            "delta": capacidad,
            "coste": 2,
            "plazo": "2 semanas",
            "detalle": (
                "Estas por encima del rango saludable y el modelo estima que "
                "volver a ese rango mejora la nota (rendimiento decreciente)."
            ),
            "efectos": {},
        }
    for accion in ACCIONES.get(variable, []):
        if accion["id"] in aplicadas:
            continue
        if 0 < accion["delta"] <= capacidad:
            return accion
    return None


def construir_plan(modelo, perfil, objetivo, max_acciones=3, referencia=None):
    """Construye el plan eligiendo en cada paso la accion mas eficiente.

    Prioridad = puntos ganados / esfuerzo percibido. Despues de cada accion se
    vuelve a simular con el modelo, asi que los efectos secundarios y la
    saturacion se tienen en cuenta automaticamente. Se para al llegar al
    objetivo (no recomienda de mas) o al agotar el presupuesto de acciones.
    """
    diag = diagnostico(modelo, perfil, referencia)
    actual = dict(perfil)
    acciones = []
    aplicadas = set()

    while len(acciones) < max_acciones and simular(modelo, actual) < objetivo:
        nota_actual = simular(modelo, actual)
        mejor = None

        for variable in VARIABLES:
            capacidad = _capacidad(actual, variable)
            if abs(capacidad) < 1e-9:
                continue

            accion = _siguiente_accion(variable, aplicadas, capacidad)
            if accion is None:
                continue

            prueba = dict(actual)
            _aplicar(prueba, variable, accion)
            ganancia = simular(modelo, prueba) - nota_actual
            if ganancia <= 0:
                continue

            prioridad = ganancia / max(1, accion["coste"])
            if mejor is None or prioridad > mejor[0]:
                mejor = (prioridad, variable, accion, ganancia)

        if mejor is None:
            break  # no queda ninguna accion util

        _, variable, accion, ganancia = mejor
        _aplicar(actual, variable, accion)
        aplicadas.add(accion["id"])
        acciones.append(
            {
                **accion,
                "variable": variable,
                "puntos": ganancia,
                "nota_tras": simular(modelo, actual),
            }
        )

    nota_final = simular(modelo, actual)
    avisos = []
    techo = _techo_realista(modelo)

    if diag["nota"] >= objetivo:
        avisos.append(
            f"Tu nota estimada ({diag['nota']:.1f}) ya alcanza el objetivo "
            f"({objetivo:.1f}): no hay acciones que anadir."
        )
    elif not acciones:
        avisos.append(
            "El modelo no ve margen de mejora con estas variables: ya estas en "
            "los rangos que el considera buenos (o los coeficientes no ayudan)."
        )
    if nota_final < objetivo and acciones:
        if techo < objetivo:
            avisos.append(
                f"Con estas 4 variables el techo realista es {techo:.1f}/100. "
                f"Para llegar a {objetivo:.1f} necesitas variables nuevas "
                "(asignatura, tipo de estudio, asistencia, nota previa...), no "
                "mas de lo mismo."
            )
        else:
            avisos.append(
                f"El objetivo es alcanzable con estas variables, pero no con "
                f"{len(acciones)} acciones: te quedas en {nota_final:.1f}. Sube "
                "el numero de acciones o el margen por accion."
            )

    # Coherencia: avisar si el plan anade mas horas de las que caben en el dia.
    horas_extra = (actual["horas_estudio"] - perfil["horas_estudio"]) + (
        actual["horas_sueno"] - perfil["horas_sueno"]
    )
    if horas_extra > 2:
        avisos.append(
            f"El plan anade {horas_extra:.1f} h/dia a tu rutina: revisa si te "
            "caben con clases y desplazamientos. Mejor pocas acciones que puedas "
            "mantener que muchas que abandonaras."
        )

    # Aviso si alguna variable con margen apenas aporta: mejor no gastar
    # esfuerzo ahi (suele pasar por multicolinealidad con otra variable).
    for hueco in diag["huecos"]:
        if 0.05 < hueco["puntos"] < 1.5:
            avisos.append(
                f"{hueco['variable']} apenas mueve la nota: llegar a "
                f"{hueco['objetivo']:g} {hueco['unidad']} solo vale "
                f"+{hueco['puntos']:.1f} pts. Prioriza lo que mas suma."
            )

    return {
        "perfil_inicial": dict(perfil),
        "nota_inicial": diag["nota"],
        "objetivo": objetivo,
        "diagnostico": diag,
        "acciones": acciones,
        "perfil_final": actual,
        "nota_final": nota_final,
        "alcanzado": nota_final >= objetivo,
        "techo": techo,
        "avisos": avisos,
    }


def formatear_plan(plan):
    """Plan en texto legible para consola."""
    diag = plan["diagnostico"]
    lineas = []

    lineas.append("=" * 62)
    lineas.append(f"DIAGNOSTICO  (nota estimada: {plan['nota_inicial']:.1f}/100)")
    lineas.append("=" * 62)
    lineas.append(f"Alumno medio de tus datos: {diag['base']:.1f}/100")
    lineas.append("")
    lineas.append("De donde viene tu nota:")
    for variable in VARIABLES:
        valor = plan["perfil_inicial"][variable]
        contrib = diag["contribuciones"][variable]
        media = diag["referencia"][variable]
        lineas.append(
            f"  {variable:20s} {valor:6.2f}  ->  {contrib:+6.1f} pts   "
            f"(media {media:.2f})"
        )
    lineas.append("")
    lineas.append("Margen de mejora por variable (objetivo saludable):")
    for h in diag["huecos"]:
        if h["puntos"] <= 0.05:
            continue
        lineas.append(
            f"  {h['variable']:20s} {h['actual']:6.2f} -> {h['objetivo']:5.2f} "
            f"{h['unidad']:8s}  +{h['puntos']:5.1f} pts posibles"
        )
    lineas.append("")

    lineas.append("=" * 62)
    lineas.append(f"PLAN  (objetivo: {plan['objetivo']:.1f}/100)")
    lineas.append("=" * 62)
    if not plan["acciones"]:
        lineas.append("  (no se proponen acciones)")
    for i, a in enumerate(plan["acciones"], 1):
        lineas.append(f"{i}. {a['titulo']}")
        lineas.append(
            f"   {a['variable']} {a['delta']:+g}  ->  {a['puntos']:+5.1f} pts   "
            f"esfuerzo {a['coste']}/5   plazo {a['plazo']}"
        )
        lineas.append(f"   {a['detalle']}")
        lineas.append("")

    lineas.append("=" * 62)
    lineas.append("SIMULACION")
    lineas.append("=" * 62)
    lineas.append(
        f"Nota inicial : {plan['nota_inicial']:5.1f}/100"
    )
    lineas.append(
        f"Nota con plan: {plan['nota_final']:5.1f}/100   "
        f"(+{plan['nota_final'] - plan['nota_inicial']:.1f} pts)"
    )
    estado = "objetivo alcanzado" if plan["alcanzado"] else "objetivo NO alcanzado"
    lineas.append(f"Objetivo     : {plan['objetivo']:5.1f}/100  ->  {estado}")

    if plan["avisos"]:
        lineas.append("")
        for aviso in plan["avisos"]:
            lineas.append(f"! {aviso}")

    return "\n".join(lineas)


def a_json(plan):
    """Version JSON del plan (para enchufar una capa LLM, una web o guardarlo)."""
    return json.dumps(plan, ensure_ascii=False, indent=2, default=float)


def main():
    modo_json = "--json" in sys.argv
    # En modo JSON todo lo conversacional va a stderr para que stdout sea JSON
    # limpio (consumible por una web, otra capa o un test).
    salida = sys.stderr if modo_json else sys.stdout

    with contextlib.redirect_stdout(salida):
        print("--- Planificador de mejoras ---")
        try:
            modelo = cargar_modelo()
        except (FileNotFoundError, ValueError) as e:
            print(f"✗ {e}")
            return

        perfil = {
            "horas_estudio": pedir_valor("Horas de estudio al dia (0-16): ", 0, 16),
            "nivel_concentracion": pedir_valor(
                "Nivel de concentracion (1-10): ", 1, 10, entero=True
            ),
            "horas_sueno": pedir_valor("Horas de sueno (0-24): ", 0, 24),
            "hizo_ejercicio": pedir_valor(
                "¿Haces ejercicio? (1 Si / 0 No): ", 0, 1, entero=True
            ),
        }
        objetivo = pedir_valor("Nota objetivo (0-100): ", 0, 100)

    plan = construir_plan(modelo, perfil, objetivo)

    if modo_json:
        print(a_json(plan))
    else:
        print()
        print(formatear_plan(plan))


if __name__ == "__main__":
    main()
