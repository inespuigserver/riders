"""pruebas.py: comprobaciones de la Parte 6. Se ejecuta con: python pruebas.py"""
from db import DB_PATH, init_db, pedidos_un_restaurante
from rutas import cargar_grafo, ruta_entre, tabla_iteraciones, tiempo_entrega

if not DB_PATH.exists():
    init_db()

grafo = cargar_grafo()
print("Vecinos de Chamberí:", grafo["Chamberí"])

minutos, ruta = ruta_entre(grafo, "Chamberí", "Carabanchel")
print("Chamberí → Carabanchel:", minutos, "min", ruta)

print()
tabla_iteraciones(grafo, "Chamberí")

print()
for pedido, cliente, rest in pedidos_un_restaurante():
    rider, m_rider, m_cliente, total, ruta = tiempo_entrega(grafo, rest["barrio"], cliente["barrio"])
    print(f"Pedido {pedido}: {rest['nombre']} ({rest['barrio']}) → {cliente['nombre']} ({cliente['barrio']})"
          f" | {rider}: {m_rider} + {m_cliente} = {total} min | {' → '.join(ruta)}")

# ---------------------------------------------------------------------------
# SESIÓN 14: Bellman-Ford y Floyd-Warshall
# ---------------------------------------------------------------------------
from rutas import bellman_ford, floyd_warshall, camino_floyd, dijkstra

print()
print("--- Bellman-Ford desde Chamberí (tiene que dar lo mismo que Dijkstra) ---")
dist_b, _, ciclo = bellman_ford(grafo, "Chamberí")
print(dist_b, "| ciclo negativo:", ciclo)
print("Igual que Dijkstra:", dist_b == dijkstra(grafo, "Chamberí")[0])

print()
print("--- Floyd-Warshall: matriz entera, comparada con Dijkstra desde cada barrio ---")
dist_f, siguiente = floyd_warshall(grafo)
print("Fila de Chamberí:", dist_f["Chamberí"])
print("Ruta Chamberí → Carabanchel:", camino_floyd(siguiente, "Chamberí", "Carabanchel"))
print("Igual que Dijkstra en todos los pares:",
      all(dist_f[o] == dijkstra(grafo, o)[0] for o in grafo))

print()
print("--- Pesos negativos (el ejemplo de las diapositivas: A→B 2, B→C -4, C→A 1) ---")
ejemplo = {"A": {"B": 2}, "B": {"C": -4}, "C": {"A": 1}}
print("Ciclo negativo detectado:", bellman_ford(ejemplo, "A")[2])

print("Con un peso negativo pero SIN ciclo (A→B 4, A→C 2, C→B -1):")
sin_ciclo = {"A": {"B": 4, "C": 2}, "B": {}, "C": {"B": -1}}
dist_n, _, ciclo_n = bellman_ford(sin_ciclo, "A")
print("   distancias:", dist_n, "| ciclo negativo:", ciclo_n)