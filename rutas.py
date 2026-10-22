"""rutas.py: el mapa como grafo, Dijkstra con camino y el rider más cercano."""
import heapq
from contextlib import closing

from db import barrio_rider, get_conn, pedidos_un_restaurante


def cargar_grafo():
    """{barrio: {vecino: minutos}} a partir de la tabla tramo."""
    grafo = {}
    with closing(get_conn()) as conn:
        for t in conn.execute("SELECT origen, destino, minutos FROM tramo"):
            grafo.setdefault(t["origen"], {})[t["destino"]] = t["minutos"]
            grafo.setdefault(t["destino"], {})[t["origen"]] = t["minutos"]  # ida y vuelta
    return grafo


def dijkstra(grafo, origen):
    dist = {nodo: float("inf") for nodo in grafo}
    previo = {origen: None}              # de dónde vengo: para reconstruir la ruta
    dist[origen] = 0
    cola = [(0, origen)]
    cerrados = set()
    while cola:
        d, u = heapq.heappop(cola)       # el pivote: el más cercano sin cerrar
        if u in cerrados:
            continue
        cerrados.add(u)
        for v, peso in grafo[u].items():
            if d + peso < dist[v]:       # relajar la arista u -> v
                dist[v] = d + peso
                previo[v] = u
                heapq.heappush(cola, (dist[v], v))
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

        print(i, "|", dist, "|", pivote)

        cerrados.add(pivote)

        for vecino, peso in grafo[pivote].items():
            nueva_distancia = dist[pivote] + peso

            if vecino not in cerrados:
                if nueva_distancia < dist[vecino]:
                    dist[vecino] = nueva_distancia
                    previo[vecino] = pivote



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
