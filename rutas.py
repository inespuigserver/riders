"""rutas.py: el mapa como grafo, Dijkstra con camino, rider más cercano y pedidos de varios restaurantes."""
# ---------------------------------------------------------------------------
#
#   - Dijkstra: el camino más corto desde UN barrio hasta todos los demás.
#       Es rápido, pero solo funciona si todos los tiempos son positivos.
#   - Bellman-Ford: lo mismo, pero más lento y más general: admite tiempos
#       negativos (descuentos) y avisa si hay un "ciclo negativo" (una vuelta
#       que ahorraría tiempo sin límite, algo imposible en la realidad).
#   - Floyd-Warshall: calcula de una vez el camino más corto entre TODOS los
#       pares de barrios y lo guarda en una tabla para consultarla después.
#
# En este mapa todos los tiempos son positivos, así que los tres dan el mismo
# resultado.
# ---------------------------------------------------------------------------

import heapq
from contextlib import closing
from itertools import permutations
import networkx as nx
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

    # dist[barrio] = los minutos más cortos que conocemos desde el origen hasta ese barrio.
    # Al empezar no sabemos llegar a ninguno, así que todos valen infinito...
    dist = {nodo: float("inf") for nodo in grafo}
    # previo[barrio] = desde qué barrio se llega a él por el camino más corto.
    # Sirve después para reconstruir la ruta yendo hacia atrás (función camino).
    previo = {origen: None}
    dist[origen] = 0                         # ...menos el origen: ya estamos en él (0 minutos)

    # cola = barrios pendientes de visitar, como (minutos, barrio). heapq la mantiene
    # de forma que heappop saca siempre el que tiene MENOS minutos.
    cola = [(0, origen)]
    # cerrados = barrios cuya distancia ya es definitiva: no se puede mejorar.
    cerrados = set()

    while cola:                              # mientras queden barrios por visitar
        d, u = heapq.heappop(cola)           # el pivote: el barrio más cercano sin cerrar
        if u in cerrados:                    # entrada antigua (peor) de un barrio ya cerrado: se ignora
            continue
        cerrados.add(u)                      # lo cerramos: d ya es su mejor distancia posible
        for v, peso in grafo[u].items():     # miramos cada vecino v de u (peso = minutos del tramo)
            if d + peso < dist[v]:           # RELAJAR: ¿ir a v pasando por u es más corto que lo que sabíamos?
                dist[v] = d + peso           # sí: apuntamos la nueva mejor distancia a v
                previo[v] = u                # ...y que se llega a v desde u
                heapq.heappush(cola, (dist[v], v))   # v entra en la cola con su nueva distancia
    # Por qué funciona: con tiempos positivos, el barrio más cercano sin cerrar no puede
    # mejorarse dando un rodeo (cualquier rodeo suma más minutos), así que se puede cerrar.
    return dist, previo


def camino(previo, destino):
    """Reconstruye la ruta origen -> destino yendo hacia atrás con previo."""
    ruta = []
    while destino is not None:
        ruta.append(destino)
        destino = previo[destino]
    return ruta[::-1]


def ruta_entre(grafo, origen, destino):
    if destino not in grafo:
        raise ValueError("Barrio de destino desconocido")
    dist, previo = dijkstra(grafo, origen)
    if dist[destino] == float("inf"):
        raise ValueError("No existe una ruta entre esos barrios")
    return dist[destino], camino(previo, destino)


def rider_mas_cercano(grafo, barrio_restaurante):
    dist, _ = dijkstra(grafo, barrio_restaurante)

    with closing(get_conn()) as conn:
        riders = conn.execute(
            "SELECT nombre, barrio FROM rider WHERE barrio IS NOT NULL"
        ).fetchall()
    disponibles = []
    for r in riders:
        barrio = r["barrio"]

        if barrio in dist and dist[barrio] != float("inf"):
            disponibles.append((dist[barrio], r["nombre"]))
    if not disponibles:
        raise ValueError("No hay riders disponibles")
    return min(disponibles)


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

# ---------------------------------------------------------------------------
# SESIÓN 14: Bellman-Ford y Floyd-Warshall
# ---------------------------------------------------------------------------

def bellman_ford(grafo, origen):
    """Camino mínimo desde origen a todos los barrios. Admite pesos negativos.
    Devuelve (dist, previo, ciclo_negativo)."""
    if origen not in grafo:
        raise ValueError(f"Barrio desconocido: {origen}")

    # Bellman-Ford trabaja con una LISTA DE ARISTAS, no con el diccionario de vecinos.
    # Pasamos {u: {v: peso}} a [(u, v, peso), ...]. Como el grafo guarda las dos
    # direcciones de cada tramo, cada calle aparece dos veces (ida y vuelta).
    aristas = [(u, v, peso) for u in grafo for v, peso in grafo[u].items()]

    # Paso 1: inicialización. Origen a 0 y el resto a infinito (igual que en Dijkstra).
    dist = {nodo: float("inf") for nodo in grafo}
    previo = {origen: None}              # para reconstruir la ruta con camino()
    dist[origen] = 0

    # Paso 2: relajar TODAS las aristas V-1 veces. Un camino mínimo sin ciclos tiene
    # como mucho V-1 aristas, y cada pasada asegura una arista más del camino.
    for _ in range(len(grafo) - 1):
        hubo_cambio = False
        for u, v, peso in aristas:
            if dist[u] + peso < dist[v]:     # relajar: ¿pasar por u mejora el camino a v?
                dist[v] = dist[u] + peso
                previo[v] = u
                hubo_cambio = True
        if not hubo_cambio:                  # si una pasada no mejora nada, ya hemos acabado
            break

    # Paso 3: una pasada más. Si TODAVÍA se puede mejorar algo, hay un ciclo negativo
    # (se podría dar vueltas rebajando el coste sin parar) y no existe un camino mínimo.
    ciclo_negativo = any(dist[u] + peso < dist[v] for u, v, peso in aristas)
    return dist, previo, ciclo_negativo


def floyd_warshall(grafo):
    """Distancias mínimas entre TODOS los pares de barrios.
    Devuelve (dist, siguiente): dist[i][j] = minutos y siguiente[i][j] = primer paso de i hacia j."""
    nodos = list(grafo)

    # La "matriz" son diccionarios de diccionarios para poder usar los nombres de barrio.
    # Empieza en infinito, con 0 de un barrio a sí mismo y el peso de cada tramo directo.
    dist = {i: {j: float("inf") for j in nodos} for i in nodos}
    siguiente = {i: {j: None for j in nodos} for i in nodos}
    for i in nodos:
        dist[i][i] = 0
        for j, peso in grafo[i].items():
            dist[i][j] = peso
            siguiente[i][j] = j              # de i a j, el primer paso es ir directo a j

    # Idea: probar cada barrio k como PARADA INTERMEDIA. Si ir de i a j pasando por k
    # es más corto que lo que ya teníamos, nos quedamos con ese camino.
    # El bucle de k tiene que ser el de fuera: así, al llegar a k, ya se han probado
    # todos los caminos que usan solo los barrios anteriores como paradas.
    for k in nodos:
        for i in nodos:
            for j in nodos:
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    siguiente[i][j] = siguiente[i][k]   # para ir a j, empiezo yendo hacia k
    return dist, siguiente


def camino_floyd(siguiente, origen, destino):
    """Reconstruye la ruta con la tabla siguiente (como camino(), pero hacia delante)."""
    if origen != destino and siguiente[origen][destino] is None:
        return []                            # no hay ruta entre esos dos barrios
    ruta = [origen]
    while origen != destino:
        origen = siguiente[origen][destino]  # damos el primer paso y repetimos desde ahí
        ruta.append(origen)
    return ruta


def comparar_algoritmos(grafo, origen, destino):
    """CASO 1: la misma ruta calculada con los tres algoritmos.
    Devuelve {algoritmo: (minutos, ruta)}."""
    dist_d, previo_d = dijkstra(grafo, origen)
    dist_b, previo_b, _ = bellman_ford(grafo, origen)
    dist_f, siguiente_f = floyd_warshall(grafo)
    return {
        "Dijkstra": (dist_d[destino], camino(previo_d, destino)),
        "Bellman-Ford": (dist_b[destino], camino(previo_b, destino)),
        "Floyd-Warshall": (dist_f[origen][destino], camino_floyd(siguiente_f, origen, destino)),
    }


def minutos_a_sedes(grafo, barrio_cliente, sedes):
    """CASO 2: minutos desde el barrio de un cliente hasta cada sede, con los tres algoritmos.
    sedes = [(nombre, barrio)]. Devuelve {algoritmo: {sede: minutos}}."""
    # Como el grafo no es dirigido, UN solo Dijkstra (o Bellman-Ford) desde el cliente
    # da la distancia a todas las sedes a la vez. Floyd ya las tiene todas calculadas.
    dist_d, _ = dijkstra(grafo, barrio_cliente)
    dist_b, _, _ = bellman_ford(grafo, barrio_cliente)
    dist_f, _ = floyd_warshall(grafo)
    return {
        "Dijkstra": {nombre: dist_d[barrio] for nombre, barrio in sedes},
        "Bellman-Ford": {nombre: dist_b[barrio] for nombre, barrio in sedes},
        "Floyd-Warshall": {nombre: dist_f[barrio_cliente][barrio] for nombre, barrio in sedes},
    }


def sede_mas_cercana_a_cada_cliente(grafo, clientes, sedes):
    """CASO 3 (idea propia): la sede más cercana de TODOS los clientes de golpe.
    clientes y sedes = [(nombre, barrio)]. Devuelve [(cliente, sede, min_floyd, min_dijkstra)]."""
    # Floyd se calcula UNA vez y después cada cliente es solo una consulta a la matriz.
    # Con Dijkstra hay que repetir el algoritmo para cada cliente.
    dist_f, _ = floyd_warshall(grafo)
    resultado = []
    for cliente, barrio_cliente in clientes:
        min_f, sede = min((dist_f[barrio_cliente][barrio], nombre) for nombre, barrio in sedes)
        dist_d, _ = dijkstra(grafo, barrio_cliente)
        min_d, _ = min((dist_d[barrio], nombre) for nombre, barrio in sedes)
        resultado.append((cliente, sede, min_f, min_d))
    return resultado

def cargar_grafo_nx():
    """El mismo mapa de barrios, pero como grafo de NetworkX. No dibuja nada."""
    G = nx.Graph()                       # Graph = no dirigido: cada tramo vale en los dos sentidos
    with closing(get_conn()) as conn:
        for t in conn.execute("SELECT origen, destino, minutos FROM tramo"):
            G.add_edge(t["origen"], t["destino"], weight=t["minutos"])   # weight = minutos del tramo
    return G