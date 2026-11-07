"""turno.py: el voraz de repartos sin solapar (selección de actividades)."""
from contextlib import closing

from db import get_conn


def planificar_turno():
    """Zonas de los repartos elegidos: siempre el que termina antes de los que caben."""
    with closing(get_conn()) as conn:
        # Ordenamos por hora de FIN. Las horas 'HH:MM' son texto, pero se ordenan bien porque
        # tienen siempre el mismo formato (dos dígitos): comparar letra a letra es comparar horas.
        repartos = conn.execute(
            "SELECT zona, inicio, fin FROM reparto ORDER BY fin"
        ).fetchall()

    # Voraz: nos quedamos con el que termina antes entre los que caben. Terminar pronto deja
    # el máximo tiempo libre para los siguientes. Es óptimo (argumento de intercambio): si
    # existiera una solución mejor, podríamos cambiar su primera entrega por la que acaba
    # antes, sin solaparse con ninguna otra, y seguiría teniendo el mismo número de entregas.
    elegidos, ultimo_fin = [], ""
    for r in repartos:
        if r["inicio"] >= ultimo_fin:                 # cabe: empieza cuando ya terminó el último
            elegidos.append(r["zona"])
            ultimo_fin = r["fin"]
    return elegidos


def planificar_turno_ingenuo():
    """Estrategia ingenua para comparar: coger primero el reparto que EMPIEZA antes."""
    with closing(get_conn()) as conn:
        repartos = conn.execute(
            "SELECT zona, inicio, fin FROM reparto ORDER BY inicio"   # aquí ordenamos por INICIO
        ).fetchall()

    # Mismo bucle que el voraz, pero el orden es otro. El primero que empieza (Centro, 09:00-10:30)
    # ocupa mucho rato y bloquea a otros dos que cabrían: por eso se queda corta.
    elegidos, ultimo_fin = [], ""
    for r in repartos:
        if r["inicio"] >= ultimo_fin:
            elegidos.append(r["zona"])
            ultimo_fin = r["fin"]
    return elegidos