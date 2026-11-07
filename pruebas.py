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

# ---------------------------------------------------------------------------
# PARTE 5.2: CRUD de usuarios (crea uno de prueba y lo borra, la BD queda igual)
# ---------------------------------------------------------------------------
from db import crear_usuario, listar_usuarios, recargar_saldo, borrar_usuario

print()
print("--- CRUD de usuarios ---")
nuevo = crear_usuario("Prueba", "Centro", 10)
print("Creado con id", nuevo)
recargar_saldo(nuevo, 25)
print("Tras recargar 25 €:", [tuple(f) for f in listar_usuarios() if f["id"] == nuevo])
borrar_usuario(nuevo)
print("Tras borrarlo, usuarios:", len(listar_usuarios()))

try:
    borrar_usuario(1)                      # Carlos tiene pedidos
except ValueError as e:
    print("Borrar a Carlos ->", e)

# ---------------------------------------------------------------------------
# PARTE 3: ejecuta todas las consultas de consultas.sql y enseña el resultado
# ---------------------------------------------------------------------------
from contextlib import closing
from db import BASE_DIR, get_conn

print()
print("=" * 70)
print("CONSULTAS DE LA PARTE 3")
print("=" * 70)
with closing(get_conn()) as conn:
    for trozo in (BASE_DIR / "consultas.sql").read_text(encoding="utf-8").split(";"):
        lineas = trozo.strip().splitlines()
        titulo = next((l for l in lineas if l.startswith("-- ") and l[3].isdigit() or l.startswith("-- RETO")), "")
        sql = "\n".join(l for l in lineas if not l.startswith("--")).strip()
        if not sql:
            continue
        print()
        print(titulo.replace("-- ", "", 1))
        for fila in conn.execute(sql).fetchall():
            print("   ", tuple(fila))

# ---------------------------------------------------------------------------
# PARTE 4.3: voraz frente a la estrategia ingenua
# ---------------------------------------------------------------------------
from turno import planificar_turno, planificar_turno_ingenuo

print()
print("--- Turno: voraz (el que termina antes) frente a ingenua (el que empieza antes) ---")
voraz = planificar_turno()
ingenua = planificar_turno_ingenuo()
print("Voraz  :", len(voraz), "repartos ->", voraz)
print("Ingenua:", len(ingenua), "repartos ->", ingenua)
print("¿Sale lo mismo?", voraz == ingenua)

# ---------------------------------------------------------------------------
# RETO 6.5: el pedido 2 (Raúl, en Latina, pide en Napolitana, SakuraGo y Estambul)
# ---------------------------------------------------------------------------
from itertools import permutations
from db import barrio_rider, obtener_sedes
from rutas import ruta_voraz, ruta_fuerza_bruta

print()
print("--- Reto 6.5: pedido 2, Latina, pasando por Napolitana, SakuraGo y Estambul ---")
sedes = dict(obtener_sedes())
paradas = [sedes["Napolitana"], sedes["SakuraGo"], sedes["Estambul"]]
print("Paradas (barrios):", paradas, "| destino: Latina")


def sin_repetidos(ruta):
    """Quita barrios repetidos seguidos (si el rider ya está en la primera parada)."""
    return [b for i, b in enumerate(ruta) if i == 0 or b != ruta[i - 1]]


for rider in ("Samu", "Óscar", "Leire"):
    inicio = barrio_rider(rider)
    min_voraz, orden_voraz = ruta_voraz(grafo, inicio, paradas, "Latina")
    min_mejor, orden_mejor = ruta_fuerza_bruta(grafo, inicio, paradas, "Latina")
    print(f"Sale {rider} desde {inicio}:")
    print(f"   voraz         {min_voraz:>2} min  {' → '.join(sin_repetidos([inicio] + orden_voraz + ['Latina']))}")
    print(f"   fuerza bruta  {min_mejor:>2} min  {' → '.join(sin_repetidos([inicio] + orden_mejor + ['Latina']))}")
    print("   ¿El voraz ha dado el mejor?", min_voraz == min_mejor)

print()
print("Los 3! = 6 órdenes posibles saliendo de Tetuán (Óscar):")
distancias = {b: dijkstra(grafo, b)[0] for b in grafo}
resultados = []
for orden in permutations(paradas):
    total, pos = 0, "Tetuán"
    for barrio in orden:
        total += distancias[pos][barrio]
        pos = barrio
    total += distancias[pos]["Latina"]
    resultados.append((total, orden))
for total, orden in sorted(resultados):
    print(f"   {total:>2} min  Tetuán → {' → '.join(orden)} → Latina")

# ---------------------------------------------------------------------------
# PARTE 5.3: crear_pedido como transacción (sobre una COPIA, tus datos no se tocan)
# ---------------------------------------------------------------------------
import shutil
import tempfile
from pathlib import Path

import db
from pedidos import crear_pedido


def cuenta_pedidos_y_lineas():
    with closing(get_conn()) as conn:
        return (conn.execute("SELECT COUNT(*) FROM pedido").fetchone()[0],
                conn.execute("SELECT COUNT(*) FROM pedido_plato").fetchone()[0])


def saldo_de(usuario_id):
    with closing(get_conn()) as conn:
        return conn.execute("SELECT saldo FROM usuario WHERE id = ?", (usuario_id,)).fetchone()[0]


print()
print("--- crear_pedido (sobre una copia de la base de datos) ---")
base_original = db.DB_PATH
copia = Path(tempfile.mkdtemp()) / "copia.db"
shutil.copy(base_original, copia)
db.DB_PATH = copia                            # a partir de aquí get_conn() abre la COPIA
try:
    pedidos_antes, lineas_antes = cuenta_pedidos_y_lineas()
    saldo_antes = saldo_de(5)

    # A mano: Raúl pide 1 pizza margarita (11 €) y tiene 250 € -> cabe, quedan 239 €
    pedido_id, total = crear_pedido(5, 1, [(3, 1)], "2026-11-06")
    print("Pedido que cabe: aceptado, total", total, "€ (a mano: 11 €) | saldo",
          saldo_antes, "->", saldo_de(5), "| pedidos y líneas:",
          (pedidos_antes, lineas_antes), "->", cuenta_pedidos_y_lineas())

    # A mano: Dani pide 1 pizza (11 €) + 1 sushi (14 €) = 25 € y solo tiene 15 € -> rechazada
    antes = cuenta_pedidos_y_lineas()
    saldo_dani = saldo_de(3)
    try:
        crear_pedido(3, 1, [(3, 1), (5, 1)], "2026-11-06")
        print("¡ERROR! Debería haberse rechazado")
    except ValueError as e:
        print("Pedido que no cabe:", e)
    print("   Tras el rechazo, pedidos y líneas iguales:", cuenta_pedidos_y_lineas() == antes,
          "| saldo de Dani igual:", saldo_de(3) == saldo_dani)
finally:
    db.DB_PATH = base_original                # volvemos a tu base de datos de verdad