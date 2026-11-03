"""app.py: menú de RiderExpress. Solo habla con el usuario: pide datos y llama a los demás."""
from datetime import date

from db import DB_PATH, init_db, obtener_platos, datos_pedido, barrio_rider
from pedidos import crear_pedido
from rutas import cargar_grafo, ruta_entre, tiempo_entrega, ruta_voraz, ruta_fuerza_bruta
from turno import planificar_turno


def leer_entero(texto):
    while True:
        try:
            return int(input(texto))
        except ValueError:
            print("Debes introducir un número")


def pedir():
    usuario = leer_entero("Id del usuario: ")
    rider = leer_entero("Id del rider: ")

    lineas = []
    while True:
        plato = leer_entero("Id del plato: ")
        cantidad = leer_entero("Cantidad: ")
        lineas.append((plato, cantidad))
        if input("¿Añadir otro plato? (s/n): ").lower() != "s":
            break

    fecha = input("Fecha (AAAA-MM-DD, enter = hoy): ") or date.today().isoformat()

    try:
        pedido_id, total = crear_pedido(usuario, rider, lineas, fecha)
    except ValueError as e:
        print("No se pudo crear el pedido:", e)
        return
    print(f"Pedido {pedido_id} aceptado. Total: {total} €")


def asignar(grafo):
    pedido_id = leer_entero("Id del pedido: ")
    cliente, restaurantes = datos_pedido(pedido_id)

    if cliente is None:
        print("Ese pedido no existe")
        return
    if not restaurantes:
        print("El pedido no tiene platos de ningún restaurante")
        return

    if len(restaurantes) == 1:
        rider, m_rider, m_cliente, total, recorrido = tiempo_entrega(
            grafo, restaurantes[0]["barrio"], cliente["barrio"]
        )
        print(f"Lo recoge {rider}: {m_rider} min hasta el restaurante + {m_cliente} min hasta el cliente")
        print(f"Tiempo total: {total} min")
        print("Ruta:", " → ".join(recorrido))
        return

    # Pedido de varios restaurantes: voraz frente a fuerza bruta
    paradas = [r["barrio"] for r in restaurantes]
    try:
        inicio = barrio_rider(input("Nombre del rider: "))
    except ValueError as e:
        print(e)
        return
    destino = cliente["barrio"]
    t_voraz, o_voraz = ruta_voraz(grafo, inicio, paradas, destino)
    t_mejor, o_mejor = ruta_fuerza_bruta(grafo, inicio, paradas, destino)
    print("Voraz: ", " → ".join([inicio] + o_voraz + [destino]), f"({t_voraz} min)")
    print("Óptimo:", " → ".join([inicio] + o_mejor + [destino]), f"({t_mejor} min)")


def ruta(grafo):
    print("Barrios:", ", ".join(grafo))
    origen = input("Origen: ")
    destino = input("Destino: ")
    if origen not in grafo or destino not in grafo:
        print("Barrio desconocido")
        return
    minutos, recorrido = ruta_entre(grafo, origen, destino)
    print(" → ".join(recorrido), f"({minutos} min)")


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
        "6": ("Salir", lambda: print("Saliendo del programa...")),
    }

    eleccion = ""
    while eleccion != "6":
        print("\n--- RIDEREXPRESS ---")
        for clave, (texto, _) in opciones.items():
            print(clave, texto)
        eleccion = input("Elige una opción: ")
        opciones.get(eleccion, ("", lambda: print("Opción no válida")))[1]()

main()