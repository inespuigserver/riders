"""pedidos.py: crear_pedido como transacción (tarjeta rechazada)."""
import sqlite3
from contextlib import closing

from db import get_conn


def crear_pedido(usuario_id, rider_id, lineas, fecha):
    """lineas = [(plato_id, cantidad), ...]. Devuelve (pedido_id, total).
    Si el total supera el saldo lanza ValueError y no queda nada guardado."""
    try:
        with closing(get_conn()) as conn, conn:   # closing cierra; with conn: commit o rollback
            cur = conn.execute(
                "INSERT INTO pedido (fecha, usuario_id, rider_id) VALUES (?, ?, ?)",
                (fecha, usuario_id, rider_id),
            )
            pedido_id = cur.lastrowid
            conn.executemany(
                "INSERT INTO pedido_plato (pedido_id, plato_id, cantidad) VALUES (?, ?, ?)",
                [(pedido_id, plato, cantidad) for plato, cantidad in lineas],
            )
            total = conn.execute(
                "SELECT SUM(p.precio * pp.cantidad) FROM pedido_plato pp "
                "JOIN plato p ON p.id = pp.plato_id WHERE pp.pedido_id = ?",
                (pedido_id,),
            ).fetchone()[0]
            saldo = conn.execute(
                "SELECT saldo FROM usuario WHERE id = ?", (usuario_id,)
            ).fetchone()["saldo"]
            if total > saldo:
                raise ValueError(f"Tarjeta rechazada: el pedido cuesta {total} € y el saldo es {saldo} €")
            conn.execute("UPDATE usuario SET saldo = saldo - ? WHERE id = ?", (total, usuario_id))
    except sqlite3.IntegrityError:
        raise ValueError("Usuario, rider o plato inexistente")
    return pedido_id, total
