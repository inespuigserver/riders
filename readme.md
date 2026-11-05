# RiderExpress

Aplicación de comida a domicilio en Python y SQLite. Guarda usuarios, riders, platos y
pedidos, y usa algoritmos de grafos para decidir qué rider recoge cada pedido y por
dónde va. Proyecto de Estructura de Datos y Algoritmos (UAX).

## Cómo ejecutarlo

Hace falta Python 3 y dos librerías: `pip install networkx matplotlib`.

- `python app.py`: abre el menú. La primera vez crea la base de datos `delivery.db`
  a partir de `delivery.sql` y `rutas.sql`.
- `python pruebas.py`: imprime las comprobaciones de las rutas (tabla de Dijkstra,
  tiempos de entrega, Bellman-Ford, Floyd-Warshall y comparación con NetworkX).
- Para dejar la base de datos como nueva, borra `delivery.db` y vuelve a ejecutar.

## Qué hace cada fichero

| Fichero | Qué hace |
|---|---|
| `delivery.sql` y `rutas.sql` | Los datos: usuarios, riders, platos, pedidos, repartos, restaurantes y el mapa de barrios |
| `db.py` | Conexión a SQLite y consultas |
| `pedidos.py` | Crear un pedido como transacción (tarjeta rechazada) |
| `turno.py` | Algoritmo voraz: repartos del turno sin solaparse |
| `rutas.py` | El mapa como grafo: Dijkstra, Bellman-Ford, Floyd-Warshall, rider más cercano y NetworkX |
| `mapa.py` | Dibuja el mapa de barrios con NetworkX y matplotlib |
| `app.py` | El menú. Es lo único que habla con el usuario |
| `pruebas.py` | Comprobaciones para ver los resultados por pantalla |

## El menú

1. Ver la carta
2. Hacer un pedido
3. Rider para un pedido
4. Ruta entre dos barrios
5. Planificar el turno
6. Comparar algoritmos en un pedido
7. De un cliente a todas las sedes
8. Sede más cercana de cada cliente
9. Dibujar el mapa
10. Salir

## Los algoritmos, explicados sin tecnicismos

El mapa es una red: cada barrio es un punto y cada tramo entre barrios vecinos es una
línea con los minutos en moto.

- **Dijkstra**: el camino más corto desde un barrio hasta todos los demás. Cierra
  siempre el barrio más cercano que aún no está cerrado y mira si por él mejora el
  camino a sus vecinos (a eso se le llama "relajar"). Guarda de dónde se viene para
  poder reconstruir la ruta. Solo vale con tiempos positivos.
- **Bellman-Ford**: lo mismo, pero revisa todos los tramos V-1 veces (V = número de
  barrios), porque un camino sin vueltas tiene como mucho V-1 tramos. Con una pasada
  más detecta los ciclos negativos. Es más lento, pero admite tiempos negativos.
- **Floyd-Warshall**: calcula una tabla con el camino más corto entre todos los
  pares de barrios. Prueba cada barrio como parada intermedia. Se calcula una vez y
  después consultar es inmediato.
- **NetworkX**: librería que resuelve lo mismo. La usamos como control: `pruebas.py`
  comprueba que nuestras versiones dan los mismos resultados que las suyas en los 64
  pares de barrios.
- **Por qué dan lo mismo en este mapa**: todos los tiempos son positivos
  (la tabla `tramo` tiene `CHECK minutos > 0`). `pruebas.py` también muestra el caso
  con pesos negativos y la detección de un ciclo negativo.
- **Voraz frente a óptimo** (pedido de varios restaurantes): el voraz va siempre al
  restaurante más cercano; la fuerza bruta prueba todos los órdenes posibles. En el
  pedido 2 coinciden, pero no está garantizado (es el problema del viajante).

## Sesión 14: Bellman-Ford y Floyd-Warshall aplicados al reparto

- **Opción 6, ruta de un pedido hacia su cliente**: la ruta restaurante a cliente
  calculada con Dijkstra, Bellman-Ford, Floyd-Warshall y NetworkX, para comprobar que
  coinciden.
- **Opción 7, de un cliente a todas las sedes**: minutos desde el barrio del cliente
  hasta cada restaurante con los tres algoritmos, y cuál es el más cercano.
- **Opción 8, idea propia: sede más cercana de cada cliente**. Floyd-Warshall se calcula
  una sola vez y cada cliente es solo una consulta a la tabla. Con Dijkstra habría que
  repetir el algoritmo para cada cliente.
- **Opción 9, dibujar el mapa**: muestra los barrios y los minutos de cada tramo. Los
  barrios con restaurante salen en rosa y, si se indica origen y destino, la ruta más
  corta se resalta en rojo. También se puede guardar como imagen.

## Decisiones de diseño

- **Transacción en `crear_pedido`**: `with closing(...) as conn, conn`. `closing`
  cierra la conexión y `conn` hace commit si todo va bien o rollback si hay un error.
  Con tarjeta rechazada no queda guardado ni el pedido ni sus líneas.
- **Consultas con `?`**: los datos viajan aparte de la consulta, así nadie puede
  meter SQL propio (inyección SQL).
- **Precio en cada línea del pedido**: si se guarda, los pedidos antiguos no cambian
  cuando sube un plato. Se gana un historial correcto y se pierde algo de espacio
  por datos repetidos.
- **Dibujo separado de los algoritmos**: `mapa.py` es el único fichero que usa
  matplotlib, así `rutas.py` solo calcula y no abre ventanas.