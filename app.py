
"""app.py: menú principal de RiderExpress."""

from datetime import date
import networkx as nx

from db import DB_PATH, init_db, obtener_platos, datos_pedido
from pedidos import crear_pedido
from rutas import cargar_grafo, dijkstra, camino, tiempo_entrega
from turno import planificar_turno


def pedir():
    try:
        usuario = int(input("Id del usuario: "))
        rider = int(input("Id del rider: "))

        texto = input(
            "Platos (id:cantidad separados por comas, ej. 1:2,7:1): "
        )

        lineas = [
            tuple(int(x) for x in par.strip().split(":"))
            for par in texto.split(",")
        ]

        pedido_id, total = crear_pedido(
            usuario, rider, lineas, date.today().isoformat()
        )

        print(f"Pedido {pedido_id} aceptado: {total} €")

    except ValueError as e:
        print(f"Error al crear el pedido: {e}")


def asignar(grafo):
    try:
        pedido_id = int(input("Id del pedido: "))
    except ValueError:
        print("Debes introducir un número")
        return

    cliente, restaurantes = datos_pedido(pedido_id)

    if cliente is None:
        print("Ese pedido no existe")
        return

    if len(restaurantes) == 0:
        print("No se ha encontrado un restaurante para el pedido")
        return

    if len(restaurantes) > 1:
        print("Pedido de varios restaurantes: pendiente de resolver")
        return

    rest = restaurantes[0]

    try:
        rider, m_rider, m_cliente, total, recorrido = tiempo_entrega(
            grafo,
            rest["barrio"],
            cliente["barrio"]
        )

        print(f"Rider asignado: {rider}")
        print(f"Tiempo hasta restaurante: {m_rider} min")
        print(f"Tiempo hasta cliente: {m_cliente} min")
        print(f"Tiempo total: {total} min")
        print(f"Ruta: {' → '.join(recorrido)}")

    except (ValueError, KeyError, nx.NetworkXException) as e:
        print(f"No se pudo calcular el reparto: {e}")


def ruta(grafo):
    print("Barrios:", ", ".join(sorted(grafo)))

    origen = input("Origen: ").strip()
    destino = input("Destino: ").strip()

    if origen not in grafo or destino not in grafo:
        print("Barrio desconocido")
        return

    dist, previo = dijkstra(grafo, origen)

    if dist[destino] == float("inf"):
        print("No existe una ruta entre esos barrios")
        return

    recorrido = camino(previo, destino)

    print(f"Distancia: {dist[destino]} min")
    print(f"Ruta: {' → '.join(recorrido)}")


def main():
    if not DB_PATH.exists():
        init_db()

    grafo = cargar_grafo()

    opciones = {
        "1": ("Ver la carta", lambda: print(*obtener_platos(), sep="\n")),
        "2": ("Hacer un pedido", pedir),
        "3": ("Rider para un pedido", lambda: asignar(grafo)),
        "4": ("Ruta entre dos barrios", lambda: ruta(grafo)),
        "5": ("Planificar el turno", lambda: print(planificar_turno())),
    }

    while True:
        print("\n--- RIDEREXPRESS ---")

        for numero, (descripcion, _) in opciones.items():
            print(f"{numero}. {descripcion}")

        eleccion = input("Opción (q para salir): ").strip()

        if eleccion.lower() == "q":
            print("Saliendo del programa...")
            break

        if eleccion in opciones:
            opciones[eleccion][1]()
        else:
            print("Opción no válida")


if __name__ == "__main__":
    main()
