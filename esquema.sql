-- ============================================================
--  RIDEREXPRESS · esquema de la base de datos (SQLite)
--  Se carga ANTES que datos.sql (lo hace init_db() en db.py).
-- ============================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS pedido_plato;
DROP TABLE IF EXISTS pedido;
DROP TABLE IF EXISTS plato;
DROP TABLE IF EXISTS rider;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS reparto;
DROP TABLE IF EXISTS tramo;
DROP TABLE IF EXISTS restaurante;

-- Quién pide (los clientes de la app)
CREATE TABLE usuario (
    id     INTEGER PRIMARY KEY,
    nombre TEXT    NOT NULL,
    barrio TEXT    NOT NULL,
    saldo  INTEGER NOT NULL CHECK (saldo >= 0)     -- dinero en el monedero (€)
);

-- Quién reparte (los empleados) y en qué barrio está ahora
CREATE TABLE rider (
    id       INTEGER PRIMARY KEY,
    nombre   TEXT NOT NULL,
    vehiculo TEXT NOT NULL CHECK (vehiculo IN ('moto', 'bici', 'patinete')),
    barrio   TEXT                                   -- posición actual en el mapa
);

-- Qué se pide (los productos de la carta)
CREATE TABLE plato (
    id          INTEGER PRIMARY KEY,
    nombre      TEXT    NOT NULL,
    restaurante TEXT    NOT NULL,                   -- 'varios' = se recoge donde el resto del pedido
    categoria   TEXT    NOT NULL,
    precio      INTEGER NOT NULL CHECK (precio > 0) -- en €
);

-- Cada pedido lo hace UN usuario y lo reparte UN rider (relaciones 1:N)
CREATE TABLE pedido (
    id         INTEGER PRIMARY KEY,
    fecha      TEXT    NOT NULL,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    rider_id   INTEGER NOT NULL REFERENCES rider(id)
);

-- Un pedido lleva VARIOS platos y un plato está en VARIOS pedidos (N:N).
-- La tabla intermedia guarda lo que no cabe en ningún otro sitio: la cantidad.
CREATE TABLE pedido_plato (
    pedido_id INTEGER NOT NULL REFERENCES pedido(id),
    plato_id  INTEGER NOT NULL REFERENCES plato(id),
    cantidad  INTEGER NOT NULL CHECK (cantidad > 0),
    PRIMARY KEY (pedido_id, plato_id)
);

-- Repartos pendientes del turno (para el algoritmo voraz)
CREATE TABLE reparto (
    id     INTEGER PRIMARY KEY,
    zona   TEXT NOT NULL,
    inicio TEXT NOT NULL,                           -- 'HH:MM': como texto se ordena bien
    fin    TEXT NOT NULL
);

-- Dónde está cada restaurante
CREATE TABLE restaurante (
    nombre TEXT PRIMARY KEY,
    barrio TEXT NOT NULL
);

-- Las aristas del grafo: un tramo entre dos barrios vecinos (doble sentido)
CREATE TABLE tramo (
    origen  TEXT    NOT NULL,
    destino TEXT    NOT NULL,
    minutos INTEGER NOT NULL CHECK (minutos > 0),   -- Dijkstra necesita pesos positivos
    PRIMARY KEY (origen, destino)
);