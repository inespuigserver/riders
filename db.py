"""db.py: conexión, creación de la base de datos y consultas."""
import sqlite3
from contextlib import closing
from pathlib import Path

AQUI = Path(__file__).parent
DB_PATH = AQUI / "delivery.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row            # fila["nombre"] en vez de fila[1]
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite no comprueba las FK si no se lo pides
    return conn


def init_db():
    """Crea delivery.db cargando delivery.sql y después rutas.sql."""
    with closing(get_conn()) as conn:
        for fichero in ("delivery.sql", "rutas.sql"):
            conn.executescript((AQUI / fichero).read_text(encoding="utf-8"))


def obtener_platos():
    """La carta, de más caro a más barato, como lista de textos."""
    with closing(get_conn()) as conn:
        filas = conn.execute(
            "SELECT id, nombre, restaurante, precio FROM plato ORDER BY precio DESC"
        ).fetchall()
    return [f"{f['id']}. {f['nombre']} ({f['restaurante']}) - {f['precio']} €" for f in filas]


def datos_pedido(pedido_id):
    """(cliente, restaurantes) de un pedido. cliente es None si no existe.
    El refresco ('varios') no cuenta: se recoge donde el resto del pedido."""
    with closing(get_conn()) as conn:
        cliente = conn.execute(
            "SELECT u.nombre, u.barrio FROM pedido pe "
            "JOIN usuario u ON u.id = pe.usuario_id WHERE pe.id = ?",
            (pedido_id,),
        ).fetchone()
        restaurantes = conn.execute(
            "SELECT DISTINCT r.nombre, r.barrio FROM pedido_plato pp "
            "JOIN plato p ON p.id = pp.plato_id "
            "JOIN restaurante r ON r.nombre = p.restaurante "
            "WHERE pp.pedido_id = ?",
            (pedido_id,),
        ).fetchall()
    return cliente, restaurantes


def pedidos_un_restaurante():
    """[(pedido_id, cliente, restaurante)] de los pedidos con un solo restaurante."""
    with closing(get_conn()) as conn:
        ids = [f["id"] for f in conn.execute("SELECT id FROM pedido ORDER BY id")]
    salida = []
    for pedido_id in ids:
        cliente, restaurantes = datos_pedido(pedido_id)
        if len(restaurantes) == 1:
            salida.append((pedido_id, cliente, restaurantes[0]))
    return salida


def barrio_rider(nombre):
    """Barrio donde está ahora un rider."""
    with closing(get_conn()) as conn:
        return conn.execute("SELECT barrio FROM rider WHERE nombre = ?", (nombre,)).fetchone()["barrio"]
