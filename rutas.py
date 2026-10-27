"""rutas.py: el mapa como grafo, Dijkstra con camino y el rider más cercano."""
import heapq
from contextlib import closing

from db import barrio_rider, get_conn, pedidos_un_restaurante


def cargar_grafo():
    grafo = {}

    with closing(get_conn()) as conn:
        for tramo in conn.execute(
            "SELECT origen, destino, minutos FROM tramo"
        ):
            origen = tramo["origen"]
            destino = tramo["destino"]
            minutos = tramo["minutos"]

            grafo.setdefault(origen, {})[destino] = minutos
            grafo.setdefault(destino, {})[origen] = minutos

    return grafo


def dijkstra(grafo, origen):
    if origen not in grafo:
        raise ValueError("Barrio de origen desconocido")

    dist = {nodo: float("inf") for nodo in grafo}
    previo = {origen: None}

    dist[origen] = 0
    cola = [(0, origen)]
    cerrados = set()

    while cola:
        distancia, actual = heapq.heappop(cola)

        if actual in cerrados:
            continue

        cerrados.add(actual)

        for vecino, peso in grafo[actual].items():
            nueva_distancia = distancia + peso

            if nueva_distancia < dist[vecino]:
                dist[vecino] = nueva_distancia
                previo[vecino] = actual

                heapq.heappush(
                    cola, (nueva_distancia, vecino)
                )

    return dist, previo


def camino(previo, destino):
    ruta = []
    while destino is not None:
        ruta.append(destino)
        destino = previo[destino]
    return ruta[::-1]


def rider_mas_cercano(grafo, barrio_restaurante):
    """(minutos, nombre) del rider que antes llega al restaurante."""
    dist, _ = dijkstra(grafo, barrio_restaurante)
    with closing(get_conn()) as conn:
        riders = conn.execute(
            "SELECT nombre, barrio FROM rider WHERE barrio IS NOT NULL"
        ).fetchall()
    return min((dist[r["barrio"]], r["nombre"]) for r in riders)


def tiempo_entrega(grafo, barrio_restaurante, barrio_cliente):
    """(rider, min rider->restaurante, min restaurante->cliente, total, ruta completa).
    La ruta completa es rider -> restaurante -> cliente."""
    m_rider, rider = rider_mas_cercano(grafo, barrio_restaurante)
    dist, previo = dijkstra(grafo, barrio_restaurante)   # un solo Dijkstra desde el restaurante
    m_cliente = dist[barrio_cliente]
    ida = camino(previo, barrio_rider(rider))[::-1]      # rider -> restaurante (el grafo es no dirigido)
    vuelta = camino(previo, barrio_cliente)              # restaurante -> cliente
    return rider, m_rider, m_cliente, m_rider + m_cliente, ida + vuelta[1:]



def tabla_iteraciones(grafo, origen):
    nodos = list(grafo.keys())
    dist = {}
    previo = {}
    cerrados = set()

    for nodo in nodos:
        dist[nodo] = float("inf")
        previo[nodo] = None

    dist[origen] = 0

    print("Iteracion | Distancias | Pivote")

    for i in range(len(nodos)):
        pivote = None
        menor = float("inf")

        for nodo in nodos:
            if nodo not in cerrados and dist[nodo] < menor:
                menor = dist[nodo]
                pivote = nodo

        if pivote is None:
            break

        distancias = {nodo: -1 if dist[nodo] == float("inf") else dist[nodo] for nodo in nodos}

        print(i, "|", distancias, "|", pivote)

        cerrados.add(pivote)

        for vecino, peso in grafo[pivote].items():
            nueva_distancia = dist[pivote] + peso

            if vecino not in cerrados:
                if nueva_distancia < dist[vecino]:
                    dist[vecino] = nueva_distancia
                    previo[vecino] = pivote



def bellman_ford(grafo, origen):
    if origen not in grafo:
        raise ValueError("Barrio de origen desconocido")

    dist = {nodo: float("inf") for nodo in grafo}
    previo = {origen: None}

    dist[origen] = 0

    # Relajar las aristas V-1 veces
    for i in range(len(grafo) - 1):
        cambiado = False

        for actual in grafo:
            if dist[actual] == float("inf"):
                continue

            for vecino, peso in grafo[actual].items():
                nueva_distancia = dist[actual] + peso

                if nueva_distancia < dist[vecino]:
                    dist[vecino] = nueva_distancia
                    previo[vecino] = actual
                    cambiado = True

        if not cambiado:
            break

    # Comprobar ciclos negativos
    for actual in grafo:
        if dist[actual] == float("inf"):
            continue

        for vecino, peso in grafo[actual].items():
            if dist[actual] + peso < dist[vecino]:
                raise ValueError("Ciclo negativo detectado")

    return dist, previo


def floyd_warshall(grafo):
    nodos = list(grafo)
    infinito = float("inf")

    dist = {}
    siguiente = {}

    # Inicializar distancias
    for i in nodos:
        dist[i] = {}
        siguiente[i] = {}

        for j in nodos:
            if i == j:
                dist[i][j] = 0
                siguiente[i][j] = j

            elif j in grafo[i]:
                dist[i][j] = grafo[i][j]
                siguiente[i][j] = j

            else:
                dist[i][j] = infinito
                siguiente[i][j] = None

    # Buscar caminos mínimos
    for k in nodos:
        for i in nodos:
            for j in nodos:
                nueva = dist[i][k] + dist[k][j]

                if nueva < dist[i][j]:
                    dist[i][j] = nueva
                    siguiente[i][j] = siguiente[i][k]

    # Detectar ciclos negativos
    for nodo in nodos:
        if dist[nodo][nodo] < 0:
            raise ValueError("Ciclo negativo detectado")

    return dist, siguiente


def camino_floyd(siguiente, origen, destino):
    if origen not in siguiente:
        raise ValueError("Barrio de origen desconocido")

    if destino not in siguiente[origen]:
        raise ValueError("Barrio de destino desconocido")

    if siguiente[origen][destino] is None:
        return []

    ruta = [origen]

    while origen != destino:
        origen = siguiente[origen][destino]
        ruta.append(origen)

    return ruta


if __name__ == "__main__":
    grafo = cargar_grafo()
    print("Vecinos de Chamberí:", grafo["Chamberí"])
    dist, previo = dijkstra(grafo, "Chamberí")
    print("Chamberí → Carabanchel:", dist["Carabanchel"], "min", camino(previo, "Carabanchel"))
    print()
    tabla_iteraciones(grafo, "Chamberí")
    print()
    for pedido, cliente, rest in pedidos_un_restaurante():
        rider, m_rider, m_cliente, total, ruta = tiempo_entrega(grafo, rest["barrio"], cliente["barrio"])
        print(f"Pedido {pedido}: {rest['nombre']} ({rest['barrio']}) → {cliente['nombre']} ({cliente['barrio']})"
              f" | {rider}: {m_rider} + {m_cliente} = {total} min | {' → '.join(ruta)}")
