
"""db.py: conexión y consultas de RiderExpress."""

import sqlite3
from pathlib import Path
from contextlib import closing

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "delivery.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with closing(get_conn()) as conn:
        for archivo in ("delivery.sql", "rutas.sql"):
            sql = (BASE_DIR / archivo).read_text(encoding="utf-8")
            conn.executescript(sql)


def obtener_platos():
    with closing(get_conn()) as conn:
        filas = conn.execute(
            """SELECT id, nombre, restaurante, precio
               FROM plato
               ORDER BY precio DESC"""
        ).fetchall()

    return [
        f"{f['id']}. {f['nombre']} "
        f"({f['restaurante']}) - {f['precio']} €"
        for f in filas
    ]


def datos_pedido(pedido_id):
    with closing(get_conn()) as conn:
        cliente = conn.execute(
            """SELECT u.nombre, u.barrio
               FROM pedido pe
               JOIN usuario u
               ON u.id = pe.usuario_id
               WHERE pe.id = ?""",
            (pedido_id,)
        ).fetchone()

        restaurantes = conn.execute(
            """SELECT DISTINCT r.nombre, r.barrio
               FROM pedido_plato dp
               JOIN plato p
               ON p.id = dp.plato_id
               JOIN restaurante r
               ON r.nombre = p.restaurante
               WHERE dp.pedido_id = ?""",
            (pedido_id,)
        ).fetchall()

    return cliente, restaurantes


def pedidos_un_restaurante():
    with closing(get_conn()) as conn:
        filas = conn.execute(
            "SELECT id FROM pedido ORDER BY id"
        ).fetchall()

    salida = []

    for f in filas:
        pedido_id = f["id"]
        cliente, restaurantes = datos_pedido(pedido_id)

        if cliente is not None and len(restaurantes) == 1:
            salida.append(
                (pedido_id, cliente, restaurantes[0])
            )

    return salida


def barrio_rider(nombre):
    with closing(get_conn()) as conn:
        fila = conn.execute(
            "SELECT barrio FROM rider WHERE nombre = ?",
            (nombre,)
        ).fetchone()

    if fila is None:
        raise ValueError(f"Rider no encontrado: {nombre}")

    return fila["barrio"]
