# siempre ejecuto este primero porque hay que crear la base de datos
import sqlite3
from contextlib import closing
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "delivery.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row                
    conn.execute("PRAGMA foreign_keys = ON")      
    return conn


def init_db():
    """Crea la base de datos: primero delivery.sql y después rutas.sql."""
    with closing(get_conn()) as conn:
         for archivo in ("esquema.sql", "datos.sql"):
            conn.executescript((BASE_DIR / archivo).read_text(encoding="utf-8"))


def obtener_platos():
    """La carta, de más caro a más barato, como lista de textos."""
    with closing(get_conn()) as conn:
        filas = conn.execute(
            "SELECT id, nombre, restaurante, precio FROM plato ORDER BY precio DESC"
        ).fetchall()
    return [f"{f['id']}. {f['nombre']} ({f['restaurante']}) - {f['precio']} €" for f in filas]


def datos_pedido(pedido_id):
    """(cliente, restaurantes) de un pedido. cliente es None si el pedido no existe."""
    with closing(get_conn()) as conn:
        cliente = conn.execute(
            """SELECT u.nombre, u.barrio
               FROM pedido pe JOIN usuario u ON u.id = pe.usuario_id
               WHERE pe.id = ?""",
            (pedido_id,),
        ).fetchone()
        restaurantes = conn.execute(
            """SELECT DISTINCT r.nombre, r.barrio
               FROM pedido_plato pp
               JOIN plato p ON p.id = pp.plato_id
               JOIN restaurante r ON r.nombre = p.restaurante
               WHERE pp.pedido_id = ?""",
            (pedido_id,),
        ).fetchall()
    return cliente, restaurantes


def pedidos_un_restaurante():
    """[(id_pedido, cliente, restaurante)] de los pedidos con platos de un solo restaurante."""
    with closing(get_conn()) as conn:
        ids = [f["id"] for f in conn.execute("SELECT id FROM pedido ORDER BY id")]
    salida = []
    for pedido_id in ids:
        cliente, restaurantes = datos_pedido(pedido_id)
        if cliente is not None and len(restaurantes) == 1:
            salida.append((pedido_id, cliente, restaurantes[0]))
    return salida


def barrio_rider(nombre):
    """Barrio donde está ahora un rider."""
    with closing(get_conn()) as conn:
        fila = conn.execute("SELECT barrio FROM rider WHERE nombre = ?", (nombre,)).fetchone()
    if fila is None:
        raise ValueError(f"Rider no encontrado: {nombre}")
    return fila["barrio"]

# ---------------------------------------------------------------------------
# SESIÓN 14: consultas que necesitan los nuevos casos de uso
# ---------------------------------------------------------------------------

def obtener_sedes():
    """[(nombre, barrio)] de todos los restaurantes (las sedes)."""
    with closing(get_conn()) as conn:
        filas = conn.execute("SELECT nombre, barrio FROM restaurante ORDER BY nombre").fetchall()
    return [(f["nombre"], f["barrio"]) for f in filas]


def obtener_clientes():
    """[(nombre, barrio)] de todos los usuarios."""
    with closing(get_conn()) as conn:
        filas = conn.execute("SELECT nombre, barrio FROM usuario ORDER BY id").fetchall()
    return [(f["nombre"], f["barrio"]) for f in filas]


def barrio_usuario(nombre):
    """Barrio donde vive un usuario."""
    with closing(get_conn()) as conn:
        fila = conn.execute("SELECT barrio FROM usuario WHERE nombre = ?", (nombre,)).fetchone()
    if fila is None:
        raise ValueError(f"Cliente no encontrado: {nombre}")
    return fila["barrio"]

# ---------------------------------------------------------------------------
# CRUD de usuarios (Parte 5.2): crear, listar, recargar saldo y borrar
# Los datos van SIEMPRE con ? y nunca pegados en el texto (así no hay inyección SQL).
# ---------------------------------------------------------------------------

def crear_usuario(nombre, barrio, saldo):
    """Crea un usuario y devuelve su id."""
    with closing(get_conn()) as conn, conn:       # closing cierra; conn hace commit o rollback
        cur = conn.execute(
            "INSERT INTO usuario (nombre, barrio, saldo) VALUES (?, ?, ?)",
            (nombre, barrio, saldo),
        )
        return cur.lastrowid                      # el id que SQLite le ha dado


def listar_usuarios():
    """Todos los usuarios, como lista de filas (id, nombre, barrio, saldo)."""
    with closing(get_conn()) as conn:
        return conn.execute(
            "SELECT id, nombre, barrio, saldo FROM usuario ORDER BY id"
        ).fetchall()


def recargar_saldo(usuario_id, euros):
    """Suma euros al monedero de un usuario."""
    if euros <= 0:
        raise ValueError("La recarga debe ser mayor que cero")
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "UPDATE usuario SET saldo = saldo + ? WHERE id = ?", (euros, usuario_id)
        )
        if cur.rowcount == 0:                     # rowcount = cuántas filas ha cambiado
            raise ValueError("Usuario inexistente")


def borrar_usuario(usuario_id):
    """Borra un usuario. No se puede si ya ha hecho pedidos (los protege la clave ajena)."""
    try:
        with closing(get_conn()) as conn, conn:
            cur = conn.execute("DELETE FROM usuario WHERE id = ?", (usuario_id,))
            if cur.rowcount == 0:
                raise ValueError("Usuario inexistente")
    except sqlite3.IntegrityError as e:           # la FK de pedido.usuario_id lo impide
        raise ValueError("No se puede borrar: el usuario tiene pedidos") from e