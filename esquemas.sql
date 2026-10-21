PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    barrio TEXT NOT NULL,
    saldo_monedero REAL NOT NULL DEFAULT 0 CHECK (saldo_monedero >= 0)
);

CREATE TABLE IF NOT EXISTS riders (
    id_rider INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    vehiculo TEXT NOT NULL CHECK (vehiculo IN ('moto', 'bici', 'patinete'))
);

CREATE TABLE IF NOT EXISTS restaurantes (
    id_restaurante INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS platos (
    id_plato INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    id_restaurante INTEGER NOT NULL,
    categoria TEXT NOT NULL,
    precio REAL NOT NULL CHECK (precio >= 0),
    FOREIGN KEY (id_restaurante) REFERENCES restaurantes(id_restaurante)
);

CREATE TABLE IF NOT EXISTS pedidos (
    id_pedido INTEGER PRIMARY KEY,
    id_usuario INTEGER NOT NULL,
    id_rider INTEGER NOT NULL,
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_rider) REFERENCES riders(id_rider)
);

-- Tabla intermedia N:N entre pedidos y platos.
-- Guarda la cantidad de cada plato incluida en cada pedido.
CREATE TABLE IF NOT EXISTS detalle_pedido (
    id_pedido INTEGER NOT NULL,
    id_plato INTEGER NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    PRIMARY KEY (id_pedido, id_plato),
    FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido),
    FOREIGN KEY (id_plato) REFERENCES platos(id_plato)
);
