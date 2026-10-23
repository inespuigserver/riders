"""app.py: menú principal de RiderExpress."""
from db import DB_PATH, init_db, obtener_platos, datos_pedido
from pedidos import crear_pedido
from rutas import cargar_grafo, dijkstra, camino, tiempo_entrega
from turno import planificar_turno
from datetime import date


def pedir():
    usuario = int(input("Id del usuario: "))
    rider = int(input("Id del rider: "))

    lineas = []
    continuar = "s"

    while continuar == "s":
        plato = int(input("Id del plato: "))
        cantidad = int(input("Cantidad: "))

        lineas.append((plato, cantidad))

        continuar = input("¿Quieres añadir otro plato?: ")

    fecha = input("Introduce la fecha (AAAA-MM-DD): ")

    try:
        pedido_id, total = crear_pedido(
            usuario, rider, lineas, fecha
        )

        print("Pedido aceptado:", pedido_id)
        print("Total:", total, "€")

    except ValueError as e:
        print("Error al crear el pedido:", e)


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
        print("No se ha encontrado un restaurante")
        return

    if len(restaurantes) > 1:
        print("Pedido de varios restaurantes: pendiente")
        return

    restaurante = restaurantes[0]

    try:
        rider, m_rider, m_cliente, total, recorrido = tiempo_entrega(
            grafo,
            restaurante["barrio"],
            cliente["barrio"]
        )

        print("Rider recomendado:", rider)
        print("Tiempo hasta restaurante:", m_rider, "min")
        print("Tiempo hasta cliente:", m_cliente, "min")
        print("Tiempo total:", total, "min")
        print("Ruta:")
        for barrio in recorrido:
            print(barrio)

    except (ValueError, KeyError) as e:
        print("No se pudo calcular el reparto:", e)


def ruta(grafo):
    print("Barrios disponibles:")

    for barrio in grafo:
        print(barrio)

    origen = input("Origen: ")
    destino = input("Destino: ")

    if origen not in grafo or destino not in grafo:
        print("Barrio desconocido")
        return

    dist, previo = dijkstra(grafo, origen)

    if dist[destino] == float("inf"):
        print("No existe una ruta entre esos barrios")
        return

    recorrido = camino(previo, destino)

    print("Distancia:", dist[destino], "min")
    print("Ruta:")
    for barrio in recorrido:
        print(barrio)


def main():

    if not DB_PATH.exists():
        init_db()

    grafo = cargar_grafo()

    opcion = ""

    while opcion != "6":

        print("\n--- RIDEREXPRESS ---")
        print("1. Ver la carta")
        print("2. Hacer un pedido")
        print("3. Rider para un pedido")
        print("4. Ruta entre dos barrios")
        print("5. Planificar el turno")
        print("6. Salir")

        opcion = input("Elige una opción: ")

        if opcion == "1":
            platos = obtener_platos()

            for plato in platos:
                print(plato)

        elif opcion == "2":
            pedir()

        elif opcion == "3":
            asignar(grafo)

        elif opcion == "4":
            ruta(grafo)

        elif opcion == "5":
            print(planificar_turno())

        elif opcion == "6":
            print("Saliendo del programa...")

        else:
            print("Opción no válida")


if __name__ == "__main__":
    main()
    