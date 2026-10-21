"""turno.py: el voraz de repartos sin solapar (selección de actividades)."""
from contextlib import closing

from db import get_conn


def planificar_turno():
    """Zonas de los repartos elegidos: siempre el que termina antes de los que caben."""
    with closing(get_conn()) as conn:
        repartos = conn.execute(
            "SELECT zona, inicio, fin FROM reparto ORDER BY fin"   # 'HH:MM' ordena bien como texto
        ).fetchall()
    elegidos, ultimo_fin = [], ""
    for r in repartos:
        if r["inicio"] >= ultimo_fin:
            elegidos.append(r["zona"])
            ultimo_fin = r["fin"]
    return elegidos
