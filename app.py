"""app.py: el menú. Lo único que habla con el usuario."""
from datetime import date

from db import DB_PATH, init_db, obtener_platos, datos_pedido
from pedidos import crear_pedido
from rutas import cargar_grafo, dijkstra, camino, tiempo_entrega
from turno import planificar_turno


def pedir():
    try:
        usuario = int(input("Id del usuario: "))
        rider = int(input("Id del rider: "))
        texto = input("Platos (id:cantidad separados por comas, ej. 1:2,7:1): ")
        lineas = [tuple(int(x) for x in par.split(":")) for par in texto.split(",")]
        pedido_id, total = crear_pedido(usuario, rider, lineas, date.today().isoformat())
        print(f"Pedido {pedido_id} aceptado: {total} €")
    except ValueError as e:
        print(e)


def asignar(grafo):
    try:
        pedido_id = int(input("Id del pedido: "))
    except ValueError:
        print("Escribe un número")
        return
    cliente, restaurantes = datos_pedido(pedido_id)
    if cliente is None:
        print("Ese pedido no existe")
    elif len(restaurantes) != 1:
        print("Es un pedido de varios restaurantes: ese es el reto del viajante")
    else:
        rest = restaurantes[0]
        rider, m_rider, m_cliente, total, ruta = tiempo_entrega(grafo, rest["barrio"], cliente["barrio"])
        print(f"Lo recoge {rider}: {m_rider} min hasta {rest['nombre']} + {m_cliente} min hasta {cliente['nombre']}"
              f" = {total} min. Ruta del reparto: {' → '.join(ruta)}")


def ruta(grafo):
    print("Barrios:", ", ".join(sorted(grafo)))
    origen, destino = input("Origen: "), input("Destino: ")
    if origen not in grafo or destino not in grafo:
        print("Barrio desconocido")
        return
    dist, previo = dijkstra(grafo, origen)
    print(f"{dist[destino]} min: {' → '.join(camino(previo, destino))}")


def main():
    if not DB_PATH.exists():
        init_db()
    grafo = cargar_grafo()
    opciones = {
        "1": ("Ver la carta",           lambda: print(*obtener_platos(), sep="\n")),
        "2": ("Hacer un pedido",        lambda: pedir()),
        "3": ("Rider para un pedido",   lambda: asignar(grafo)),
        "4": ("Ruta entre dos barrios", lambda: ruta(grafo)),
        "5": ("Planificar el turno",    lambda: print(planificar_turno())),
    }
    while True:
        for k, (texto, _) in opciones.items():
            print(k, texto)
        eleccion = input("Opción (q para salir): ")
        if eleccion == "q":
            break
        opciones.get(eleccion, ("", lambda: print("No existe")))[1]()


if __name__ == "__main__":
    main()
