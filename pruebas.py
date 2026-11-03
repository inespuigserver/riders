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