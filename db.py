
"""db.py: conexión y consultas de RiderExpress."""

import sqlite3
from contextlib import closing

DB_PATH = "delivery.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with closing(get_conn()) as conn:
        with open("esquemas.sql", encoding="utf-8") as f:
            conn.executescript(f.read())

        with open("datos.sql", encoding="utf-8") as f:
            conn.executescript(f.read())

        with open("rutas.sql", encoding="utf-8") as f:
            conn.executescript(f.read())


def obtener_platos():
    with closing(get_conn()) as conn:
        filas = conn.execute(
            """SELECT p.id_plato, p.nombre,
                      r.nombre AS restaurante, p.precio
               FROM platos p
               JOIN restaurantes r
               ON p.id_restaurante = r.id_restaurante
               ORDER BY p.precio DESC"""
        ).fetchall()

    return [
        f"{f['id_plato']}. {f['nombre']} "
        f"({f['restaurante']}) - {f['precio']} €"
        for f in filas
    ]


def datos_pedido(pedido_id):
    with closing(get_conn()) as conn:
        cliente = conn.execute(
            """SELECT u.nombre, u.barrio
               FROM pedidos pe
               JOIN usuarios u
               ON u.id_usuario = pe.id_usuario
               WHERE pe.id_pedido = ?""",
            (pedido_id,)
        ).fetchone()

        restaurantes = conn.execute(
            """SELECT DISTINCT r.nombre, r.barrio
               FROM detalle_pedido dp
               JOIN platos p
               ON p.id_plato = dp.id_plato
               JOIN restaurantes r
               ON r.id_restaurante = p.id_restaurante
               WHERE dp.id_pedido = ?""",
            (pedido_id,)
        ).fetchall()

    return cliente, restaurantes


def pedidos_un_restaurante():
    with closing(get_conn()) as conn:
        filas = conn.execute(
            "SELECT id_pedido FROM pedidos ORDER BY id_pedido"
        ).fetchall()

    salida = []

    for f in filas:
        pedido_id = f["id_pedido"]
        cliente, restaurantes = datos_pedido(pedido_id)

        if len(restaurantes) == 1:
            salida.append(
                (pedido_id, cliente, restaurantes[0])
            )

    return salida


def barrio_rider(nombre):
    with closing(get_conn()) as conn:
        fila = conn.execute(
            "SELECT barrio FROM riders WHERE nombre = ?",
            (nombre,)
        ).fetchone()

    return fila["barrio"]
