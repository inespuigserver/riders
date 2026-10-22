-- ============================================================
--  RIDEREXPRESS · ampliación para la sesión 13: el mapa de barrios
--  Se carga DESPUÉS de delivery.sql:
--      sqlite3 delivery.db < delivery.sql
--      sqlite3 delivery.db < rutas.sql
--  Minutos en moto entre barrios vecinos (calles de doble sentido).
-- ============================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS tramo;
DROP TABLE IF EXISTS restaurante;

-- Dónde está cada restaurante
CREATE TABLE restaurante (
    nombre TEXT PRIMARY KEY,
    barrio TEXT NOT NULL
);
INSERT INTO restaurante (nombre, barrio) VALUES
 ('BurgerLab',  'Chamberí'),
 ('Napolitana', 'Centro'),
 ('SakuraGo',   'Moncloa'),
 ('Estambul',   'Usera');
-- El Refresco ('varios') se recoge en el mismo restaurante que el resto del pedido.

-- Dónde está ahora cada rider
ALTER TABLE rider ADD COLUMN barrio TEXT;
UPDATE rider SET barrio = 'Centro' WHERE nombre = 'Samu';
UPDATE rider SET barrio = 'Tetuán' WHERE nombre = 'Óscar';
UPDATE rider SET barrio = 'Usera'  WHERE nombre = 'Leire';

-- Las aristas del grafo: un tramo entre dos barrios vecinos y lo que se tarda
CREATE TABLE tramo (
    origen  TEXT    NOT NULL,
    destino TEXT    NOT NULL,
    minutos INTEGER NOT NULL CHECK (minutos > 0),
    PRIMARY KEY (origen, destino)
);
INSERT INTO tramo (origen, destino, minutos) VALUES
 ('Centro',      'Chamberí',     8),
 ('Centro',      'Latina',       7),
 ('Centro',      'Usera',       12),
 ('Centro',      'Vallecas',    15),
 ('Centro',      'Moncloa',     10),
 ('Chamberí',    'Tetuán',       7),
 ('Chamberí',    'Moncloa',      6),
 ('Moncloa',     'Tetuán',      12),
 ('Latina',      'Carabanchel',  6),
 ('Latina',      'Moncloa',     14),
 ('Carabanchel', 'Usera',        8),
 ('Usera',       'Vallecas',     9);
