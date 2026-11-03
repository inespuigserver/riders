"""rutas.py: el mapa como grafo, Dijkstra con camino, rider más cercano y pedidos de varios restaurantes."""
import heapq
from contextlib import closing
from itertools import permutations
from db import barrio_rider, get_conn


def cargar_grafo():
    """{barrio: {vecino: minutos}} a partir de la tabla tramo (doble sentido)."""
    grafo = {}
    with closing(get_conn()) as conn:
        for t in conn.execute("SELECT origen, destino, minutos FROM tramo"):
            grafo.setdefault(t["origen"], {})[t["destino"]] = t["minutos"]
            grafo.setdefault(t["destino"], {})[t["origen"]] = t["minutos"]
    return grafo


def dijkstra(grafo, origen):
    """Devuelve (dist, previo): minutos mínimos desde origen y de dónde se llega a cada barrio."""
    if origen not in grafo:
        raise ValueError(f"Barrio desconocido: {origen}")

    dist = {nodo: float("inf") for nodo in grafo}
    previo = {origen: None}
    dist[origen] = 0
    cola = [(0, origen)]
    cerrados = set()

    while cola:
        d, u = heapq.heappop(cola)           # el pivote: el más cercano sin cerrar
        if u in cerrados:
            continue
        cerrados.add(u)
        for v, peso in grafo[u].items():
            if d + peso < dist[v]:           # relajar la arista u -> v
                dist[v] = d + peso
                previo[v] = u
                heapq.heappush(cola, (dist[v], v))
    return dist, previo


def camino(previo, destino):
    """Reconstruye la ruta origen -> destino yendo hacia atrás con previo."""
    ruta = []
    while destino is not None:
        ruta.append(destino)
        destino = previo[destino]
    return ruta[::-1]


def ruta_entre(grafo, origen, destino):
    """(minutos, ruta) entre dos barrios."""
    dist, previo = dijkstra(grafo, origen)
    return dist[destino], camino(previo, destino)


def rider_mas_cercano(grafo, barrio_restaurante):
    """(minutos, nombre) del rider que antes llega al restaurante."""
    dist, _ = dijkstra(grafo, barrio_restaurante)   # un solo Dijkstra: el grafo no es dirigido
    with closing(get_conn()) as conn:
        riders = conn.execute(
            "SELECT nombre, barrio FROM rider WHERE barrio IS NOT NULL"
        ).fetchall()
    return min((dist[r["barrio"]], r["nombre"]) for r in riders)


def tiempo_entrega(grafo, barrio_restaurante, barrio_cliente):
    """(rider, min hasta restaurante, min hasta cliente, total, ruta rider -> restaurante -> cliente)."""
    m_rider, rider = rider_mas_cercano(grafo, barrio_restaurante)
    dist, previo = dijkstra(grafo, barrio_restaurante)
    ida = camino(previo, barrio_rider(rider))[::-1]
    vuelta = camino(previo, barrio_cliente)
    return rider, m_rider, dist[barrio_cliente], m_rider + dist[barrio_cliente], ida + vuelta[1:]


def ruta_voraz(grafo, inicio, paradas, fin):
    """Desde donde estés, ve a la parada más cercana que te falte. Devuelve (minutos, orden)."""
    pos, falta, orden, total = inicio, set(paradas), [], 0
    while falta:
        dist, _ = dijkstra(grafo, pos)
        sig = min(falta, key=lambda b: (dist[b], b))
        total += dist[sig]
        orden.append(sig)
        falta.remove(sig)
        pos = sig
    return total + dijkstra(grafo, pos)[0][fin], orden


def ruta_fuerza_bruta(grafo, inicio, paradas, fin):
    """Prueba los n! órdenes posibles. Devuelve (minutos, orden) del mejor."""
    dist = {b: dijkstra(grafo, b)[0] for b in grafo}

    def coste(orden):
        total, pos = 0, inicio
        for b in orden:
            total += dist[pos][b]
            pos = b
        return total + dist[pos][fin]

    return min((coste(o), list(o)) for o in permutations(paradas))


def tabla_iteraciones(grafo, origen):
    """Imprime la tabla de Dijkstra (una fila por iteración, -1 = infinito) para compararla con la hecha a mano."""
    nodos = list(grafo)
    dist = {n: float("inf") for n in nodos}
    dist[origen] = 0
    cerrados = set()

    print("Iteración | Distancias | Pivote")
    for i in range(len(nodos)):
        abiertos = [n for n in nodos if n not in cerrados and dist[n] < float("inf")]
        if not abiertos:
            break
        pivote = min(abiertos, key=lambda n: dist[n])
        print(i, "|", {n: (-1 if dist[n] == float("inf") else dist[n]) for n in nodos}, "|", pivote)
        cerrados.add(pivote)
        for vecino, peso in grafo[pivote].items():
            if vecino not in cerrados and dist[pivote] + peso < dist[vecino]:
                dist[vecino] = dist[pivote] + peso
