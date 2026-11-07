"""pedidos.py: crear un pedido como transacción."""
import sqlite3
from contextlib import closing

from db import get_conn


def crear_pedido(usuario_id, rider_id, lineas, fecha):
    """lineas = [(plato_id, cantidad), ...]. Devuelve (pedido_id, total).
    Si no hay saldo lanza ValueError y no queda nada guardado."""
    # Comprobaciones previas (antes de tocar la base de datos)
    if not lineas:
        raise ValueError("El pedido debe tener al menos un plato")

    cantidades = {}                                   # une platos repetidos: [(3,1),(3,2)] -> {3: 3}
    for plato, cantidad in lineas:
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        cantidades[plato] = cantidades.get(plato, 0) + cantidad

    try:
        # POR QUÉ UNA TRANSACCIÓN: un pedido son varias operaciones (crear el pedido,
        # sus líneas y descontar el saldo). O se hacen TODAS o no se hace NINGUNA;
        # si no, podría quedar un pedido sin cobrar o un cobro sin pedido.
        #   closing(...) -> cierra la conexión al salir, pase lo que pase.
        #   conn         -> si el bloque acaba bien hace COMMIT; si salta un error, ROLLBACK.
        with closing(get_conn()) as conn, conn:
            # 1. Leemos el saldo del usuario (y de paso comprobamos que existe)
            usuario = conn.execute(
                "SELECT saldo FROM usuario WHERE id = ?", (usuario_id,)   # ? = el dato viaja aparte (sin inyección SQL)
            ).fetchone()
            if usuario is None:
                raise ValueError("Usuario inexistente")

            # 2. Insertamos el pedido y recuperamos el id que SQLite le ha dado
            cur = conn.execute(
                "INSERT INTO pedido (fecha, usuario_id, rider_id) VALUES (?, ?, ?)",
                (fecha, usuario_id, rider_id),
            )
            pedido_id = cur.lastrowid

            # 3. Insertamos todas las líneas (plato y cantidad) de una vez
            conn.executemany(
                "INSERT INTO pedido_plato (pedido_id, plato_id, cantidad) VALUES (?, ?, ?)",
                [(pedido_id, plato, cant) for plato, cant in cantidades.items()],
            )

            # 4. Calculamos el total con los precios de la carta: suma de precio x cantidad
            total = conn.execute(
                """SELECT SUM(p.precio * pp.cantidad)
                   FROM pedido_plato pp JOIN plato p ON p.id = pp.plato_id
                   WHERE pp.pedido_id = ?""",
                (pedido_id,),
            ).fetchone()[0]

            # 5. Si no hay saldo suficiente, lanzamos el error. Al salir del bloque por un
            #    error se hace ROLLBACK: el pedido y sus líneas (pasos 2 y 3) se deshacen.
            if total > usuario["saldo"]:
                raise ValueError(
                    f"Tarjeta rechazada: el pedido cuesta {total} € "
                    f"y el saldo es {usuario['saldo']} €"
                )

            # 6. Hay saldo: lo descontamos. Al acabar el bloque bien se hace COMMIT de todo.
            conn.execute(
                "UPDATE usuario SET saldo = saldo - ? WHERE id = ?", (total, usuario_id)
            )
            return pedido_id, total
    except sqlite3.IntegrityError as e:               # rider o plato que no existen (clave ajena)
        raise ValueError("Rider o plato inexistente") from e