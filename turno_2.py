
"""turno.py: el voraz de repartos sin solapar (selección de actividades)."""
from contextlib import closing

from db import get_conn


def planificar_turno():
    """Zonas de los repartos elegidos: siempre el que termina antes de los que caben."""
    with closing(get_conn()) as conn:
        repartos = conn.execute(
            "SELECT zona, inicio, fin FROM reparto ORDER BY fin"
        ).fetchall()

    elegidos, ultimo_fin = [], ""

    for r in repartos:
        if r["inicio"] >= ultimo_fin:
            elegidos.append(r["zona"])
            ultimo_fin = r["fin"]

    return elegidos

if __name__ == "__main__":
    print("Repartos seleccionados:")
    for zona in planificar_turno():
        print(f"- {zona}")

