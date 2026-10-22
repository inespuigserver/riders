"""pedidos.py: creación de pedidos y gestión del saldo."""

import sqlite3
from contextlib import closing

from db import get_conn


def crear_pedido(usuario_id, rider_id, lineas, fecha):

    if not lineas:
        raise ValueError("El pedido debe contener al menos un plato")

    # Organizar los platos en un diccionario
    cantidades = {}

    for plato, cantidad in lineas:
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")

        cantidades[plato] = cantidades.get(plato, 0) + cantidad

    try:
        with closing(get_conn()) as conn, conn:

            # Crear el pedido
            cur = conn.execute(
                """INSERT INTO pedido
                   (fecha, usuario_id, rider_id)
                   VALUES (?, ?, ?)""",
                (fecha, usuario_id, rider_id)
            )

            pedido_id = cur.lastrowid

            # Guardar los platos y sus cantidades
            conn.executemany(
                """INSERT INTO pedido_plato
                   (pedido_id, plato_id, cantidad)
                   VALUES (?, ?, ?)""",
                [
                    (pedido_id, plato, cantidad)
                    for plato, cantidad in cantidades.items()
                ]
            )

            # Calcular el precio total
            total = conn.execute(
                """SELECT SUM(p.precio * pp.cantidad)
                   FROM pedido_plato pp
                   JOIN plato p ON p.id = pp.plato_id
                   WHERE pp.pedido_id = ?""",
                (pedido_id,)
            ).fetchone()[0]

            # Consultar el saldo del usuario
            usuario = conn.execute(
                "SELECT saldo FROM usuario WHERE id = ?",
                (usuario_id,)
            ).fetchone()

            if usuario is None:
                raise ValueError("Usuario inexistente")

            saldo = usuario["saldo"]

            # Comprobar saldo suficiente
            if total > saldo:
                raise ValueError(
                    f"Tarjeta rechazada: el pedido cuesta "
                    f"{total} € y el saldo es {saldo} €"
                )

            # Descontar el dinero
            conn.execute(
                """UPDATE usuario
                   SET saldo = saldo - ?
                   WHERE id = ?""",
                (total, usuario_id)
            )

            return pedido_id, total

    except sqlite3.IntegrityError as e:
        raise ValueError(
            "Usuario, rider o plato inexistente o inválido"
        ) from e
