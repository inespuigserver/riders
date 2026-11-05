"""app.py: menú de RiderExpress. Solo habla con el usuario: pide datos y llama a los demás."""
from datetime import date

from mapa import dibujar_mapa
from turno import planificar_turno
from db import (DB_PATH, init_db, obtener_platos, datos_pedido, barrio_rider,
                barrio_usuario, obtener_clientes, obtener_sedes)
from pedidos import crear_pedido
from rutas import (cargar_grafo, ruta_entre, tiempo_entrega, ruta_voraz, ruta_fuerza_bruta,
                   comparar_algoritmos, minutos_a_sedes, sede_mas_cercana_a_cada_cliente)


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


def comparar_ruta(grafo):
    # CASO 1: la ruta restaurante -> cliente de un pedido, calculada con los 3 algoritmos
    pedido_id = leer_entero("Id del pedido: ")
    cliente, restaurantes = datos_pedido(pedido_id)

    if cliente is None:
        print("Ese pedido no existe")
        return
    if len(restaurantes) != 1:
        print("Esta opción es para pedidos de un solo restaurante")
        return

    origen = restaurantes[0]["barrio"]
    destino = cliente["barrio"]
    resultados = comparar_algoritmos(grafo, origen, destino)

    print(f"Restaurante ({origen}) -> cliente ({destino})")
    for algoritmo, (minutos, recorrido) in resultados.items():
        print(f"{algoritmo:<15} {minutos:>3} min   {' -> '.join(recorrido)}")

    # Los tres tienen que dar los mismos minutos (aquí no hay pesos negativos)
    tiempos = {minutos for minutos, _ in resultados.values()}
    print("Los tres algoritmos coinciden" if len(tiempos) == 1 else "¡Los minutos no coinciden!")


def cliente_a_sedes(grafo):
    # CASO 2: de un cliente a TODAS las sedes (restaurantes)
    nombre = input("Nombre del cliente: ")
    try:
        barrio = barrio_usuario(nombre)
    except ValueError as e:
        print(e)
        return

    sedes = obtener_sedes()
    tabla = minutos_a_sedes(grafo, barrio, sedes)

    print(f"\nMinutos desde {nombre} ({barrio}) hasta cada sede:")
    print(f"{'Sede':<12}{'Dijkstra':>10}{'Bellman-F':>11}{'Floyd':>7}")
    for sede, _ in sedes:
        print(f"{sede:<12}{tabla['Dijkstra'][sede]:>10}{tabla['Bellman-Ford'][sede]:>11}"
              f"{tabla['Floyd-Warshall'][sede]:>7}")

    # La sede más cercana y la ruta hasta ella (desempata el nombre)
    minutos, sede = min((tabla["Dijkstra"][nombre_sede], nombre_sede) for nombre_sede, _ in sedes)
    barrio_sede = dict(sedes)[sede]
    _, recorrido = ruta_entre(grafo, barrio, barrio_sede)
    print(f"La más cercana: {sede} ({minutos} min): {' -> '.join(recorrido)}")


def sedes_para_todos(grafo):
    # CASO 3 (idea propia): sede más cercana de cada cliente, con Floyd calculado una sola vez
    print(f"{'Cliente':<8}{'Barrio':<13}{'Sede más cercana':<18}{'Floyd':>6}{'Dijkstra':>9}")
    clientes = obtener_clientes()
    barrios = dict(clientes)
    for cliente, sede, min_f, min_d in sede_mas_cercana_a_cada_cliente(
            grafo, clientes, obtener_sedes()):
        print(f"{cliente:<8}{barrios[cliente]:<13}{sede:<18}{min_f:>6}{min_d:>9}")

def dibujar(grafo):
    # Dibuja el mapa con NetworkX y matplotlib; si se da origen y destino, resalta la ruta
    print("Barrios:", ", ".join(grafo))
    origen = input("Origen (enter = solo el mapa): ")

    recorrido = []
    if origen:
        destino = input("Destino: ")
        if origen not in grafo or destino not in grafo:
            print("Barrio desconocido")
            return
        minutos, recorrido = ruta_entre(grafo, origen, destino)
        print(" -> ".join(recorrido), f"({minutos} min)")

    archivo = input("Guardar como imagen, por ejemplo mapa.png (enter = no): ")
    dibujar_mapa(recorrido, archivo or None)

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
        "6": ("Comparar algoritmos en un pedido", lambda: comparar_ruta(grafo)),
        "7": ("De un cliente a todas las sedes", lambda: cliente_a_sedes(grafo)),
        "8": ("Sede más cercana de cada cliente", lambda: sedes_para_todos(grafo)),
        "9": ("Dibujar el mapa", lambda: dibujar(grafo)),
        "10": ("Salir", lambda: print("Saliendo del programa...")),
    }

    eleccion = ""
    while eleccion != "10":
        print("\n--- RIDEREXPRESS ---")
        for clave, (texto, _) in opciones.items():
            print(clave, texto)
        eleccion = input("Elige una opción: ")
        opciones.get(eleccion, ("", lambda: print("Opción no válida")))[1]()

main()