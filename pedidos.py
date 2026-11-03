"""pedidos.py: crear un pedido como transacción."""
import sqlite3
from contextlib import closing

from db import get_conn


def crear_pedido(usuario_id, rider_id, lineas, fecha):
    """lineas = [(plato_id, cantidad), ...]. Devuelve (pedido_id, total).
    Si no hay saldo lanza ValueError y no queda nada guardado."""
    if not lineas:
        raise ValueError("El pedido debe tener al menos un plato")

    cantidades = {}                                   # une platos repetidos
    for plato, cantidad in lineas:
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        cantidades[plato] = cantidades.get(plato, 0) + cantidad

    try:
        with closing(get_conn()) as conn, conn:       # closing cierra; conn hace commit/rollback
            usuario = conn.execute(
                "SELECT saldo FROM usuario WHERE id = ?", (usuario_id,)
            ).fetchone()
            if usuario is None:
                raise ValueError("Usuario inexistente")

            cur = conn.execute(
                "INSERT INTO pedido (fecha, usuario_id, rider_id) VALUES (?, ?, ?)",
                (fecha, usuario_id, rider_id),
            )
            pedido_id = cur.lastrowid

            conn.executemany(
                "INSERT INTO pedido_plato (pedido_id, plato_id, cantidad) VALUES (?, ?, ?)",
                [(pedido_id, plato, cant) for plato, cant in cantidades.items()],
            )

            total = conn.execute(
                """SELECT SUM(p.precio * pp.cantidad)
                   FROM pedido_plato pp JOIN plato p ON p.id = pp.plato_id
                   WHERE pp.pedido_id = ?""",
                (pedido_id,),
            ).fetchone()[0]

            if total > usuario["saldo"]:
                raise ValueError(
                    f"Tarjeta rechazada: el pedido cuesta {total} € "
                    f"y el saldo es {usuario['saldo']} €"
                )

            conn.execute(
                "UPDATE usuario SET saldo = saldo - ? WHERE id = ?", (total, usuario_id)
            )
            return pedido_id, total
    except sqlite3.IntegrityError as e:               # rider o plato que no existen
        raise ValueError("Rider o plato inexistente") from e