PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS pedido_plato;
DROP TABLE IF EXISTS pedido;
DROP TABLE IF EXISTS plato;
DROP TABLE IF EXISTS rider;
DROP TABLE IF EXISTS usuario;


CREATE TABLE usuario (
    id     INTEGER PRIMARY KEY,
    nombre TEXT    NOT NULL,
    barrio TEXT    NOT NULL,
    saldo  INTEGER NOT NULL          
);


CREATE TABLE rider (
    id       INTEGER PRIMARY KEY,
    nombre   TEXT NOT NULL,
    vehiculo TEXT NOT NULL           
);


CREATE TABLE plato (
    id          INTEGER PRIMARY KEY,
    nombre      TEXT    NOT NULL,
    restaurante TEXT    NOT NULL,
    categoria   TEXT    NOT NULL,    
    precio      INTEGER NOT NULL    
);

-- Cada pedido lo hace UN usuario y lo reparte UN rider
CREATE TABLE pedido (
    id         INTEGER PRIMARY KEY,
    fecha      TEXT    NOT NULL,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    rider_id   INTEGER NOT NULL REFERENCES rider(id)
);

-- Un pedido lleva VARIOS platos, y de cada uno una cantidad (N:N)
CREATE TABLE pedido_plato (
    pedido_id INTEGER NOT NULL REFERENCES pedido(id),
    plato_id  INTEGER NOT NULL REFERENCES plato(id),
    cantidad  INTEGER NOT NULL,
    PRIMARY KEY (pedido_id, plato_id)
);

-- ---------- DATOS ----------
INSERT INTO usuario (id, nombre, barrio, saldo) VALUES
 (1, 'Carlos', 'Centro',      120),
 (2, 'Lucía',  'Tetuán',      200),
 (3, 'Dani',   'Vallecas',     15),   -- va justo de saldo...
 (4, 'Marta',  'Chamberí',     90),
 (5, 'Raúl',   'Latina',      250),
 (6, 'Nerea',  'Carabanchel',  60),
 (7, 'Iván',   'Usera',       150),
 (8, 'Paula',  'Moncloa',      30);   -- esta cocina en casa, nunca pide

INSERT INTO rider (id, nombre, vehiculo) VALUES
 (1, 'Samu',  'moto'),
 (2, 'Óscar', 'bici'),
 (3, 'Leire', 'patinete');

INSERT INTO plato (id, nombre, restaurante, categoria, precio) VALUES
 (1, 'Hamburguesa Clásica', 'BurgerLab',  'hamburguesa',     9),
 (2, 'Patatas Deluxe',      'BurgerLab',  'acompañamiento',  4),
 (3, 'Pizza Margarita',     'Napolitana', 'pizza',          11),
 (4, 'Pizza Barbacoa',      'Napolitana', 'pizza',          13),
 (5, 'Sushi 12 piezas',     'SakuraGo',   'sushi',          14),
 (6, 'Kebab Mixto',         'Estambul',   'kebab',           6),
 (7, 'Tarta de Queso',      'BurgerLab',  'postre',          5),
 (8, 'Refresco',            'varios',     'bebida',          2);

INSERT INTO pedido (id, fecha, usuario_id, rider_id) VALUES
 (1,  '2026-03-01', 1, 1),
 (2,  '2026-03-01', 5, 2),
 (3,  '2026-03-02', 2, 1),
 (4,  '2026-03-02', 1, 3),
 (5,  '2026-03-03', 7, 2),
 (6,  '2026-03-03', 5, 1),
 (7,  '2026-03-04', 4, 3),
 (8,  '2026-03-04', 3, 2),
 (9,  '2026-03-05', 5, 1),
 (10, '2026-03-05', 6, 3);

INSERT INTO pedido_plato (pedido_id, plato_id, cantidad) VALUES
 (1, 1, 3), (1, 7, 1),                 -- Carlos: 3 hamburguesas, 1 tarta
 (2, 6, 4), (2, 5, 2), (2, 3, 1),      -- Raúl: 4 kebabs, 2 sushis, 1 pizza
 (3, 4, 2), (3, 2, 1),                 -- Lucía: 2 pizzas barbacoa, 1 patatas
 (4, 8, 2), (4, 6, 1),                 -- Carlos: 2 refrescos, 1 kebab
 (5, 8, 3), (5, 3, 1),                 -- Iván: 3 refrescos, 1 pizza
 (6, 1, 2), (6, 7, 1),                 -- Raúl: 2 hamburguesas, 1 tarta
 (7, 2, 3), (7, 8, 2),                 -- Marta: 3 patatas, 2 refrescos
 (8, 3, 1), (8, 5, 1),                 -- Dani: 1 pizza (11) + 1 sushi (14) = 25€... y tiene 15
 (9, 3, 2), (9, 6, 5),                 -- Raúl: 2 pizzas, 5 kebabs
 (10, 1, 1), (10, 7, 1);               -- Nerea: 1 hamburguesa, 1 tarta

-- ---------- PARTE 4: repartos pendientes del turno (para el algoritmo voraz) ----------
-- Cada reparto ocupa una franja. Un rider solo puede hacer uno a la vez (sin solapar).
DROP TABLE IF EXISTS reparto;
CREATE TABLE reparto (
    id     INTEGER PRIMARY KEY,
    zona   TEXT NOT NULL,
    inicio TEXT NOT NULL,              -- 'HH:MM'
    fin    TEXT NOT NULL
);
INSERT INTO reparto (id, zona, inicio, fin) VALUES
 (1, 'Centro',   '09:00', '10:30'),
 (2, 'Tetuán',   '09:30', '10:00'),
 (3, 'Chamberí', '10:00', '11:00'),
 (4, 'Latina',   '10:30', '12:00'),
 (5, 'Usera',    '11:00', '11:30'),
 (6, 'Vallecas', '11:15', '12:15'),
 (7, 'Moncloa',  '12:00', '13:00');
