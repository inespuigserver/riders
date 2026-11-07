-- ============================================================
--  RIDEREXPRESS · Parte 3: las preguntas de siempre
--  Una consulta por pregunta. Se ejecutan con: python pruebas.py
-- ============================================================

-- 1. La carta: todos los platos, de más caro a más barato
SELECT nombre, restaurante, precio
FROM plato
ORDER BY precio DESC;

-- 2. Clientes con saldo: usuarios con 150 € o más en el monedero
SELECT nombre, barrio, saldo
FROM usuario
WHERE saldo >= 150;

-- 3. Dinero en la app: suma del saldo de todos los usuarios
SELECT SUM(saldo) AS saldo_total
FROM usuario;

-- 4. Lo caro: platos que cuestan más de 10 €
SELECT nombre, restaurante, precio
FROM plato
WHERE precio > 10;

-- 5. El registro de pedidos: fecha, usuario y rider (JOIN de tres tablas)
SELECT pe.id AS pedido, pe.fecha, u.nombre AS usuario, r.nombre AS rider
FROM pedido pe
JOIN usuario u ON u.id = pe.usuario_id
JOIN rider   r ON r.id = pe.rider_id
ORDER BY pe.id;

-- 6. El superventas: el plato más pedido, sumando cantidades
SELECT p.nombre, SUM(pp.cantidad) AS unidades
FROM pedido_plato pp
JOIN plato p ON p.id = pp.plato_id
GROUP BY p.id
ORDER BY unidades DESC
LIMIT 1;

-- 7. ¿Quién vive del delivery? Gasto total de cada usuario (precio x cantidad)
SELECT u.nombre, SUM(p.precio * pp.cantidad) AS gastado
FROM usuario u
JOIN pedido       pe ON pe.usuario_id = u.id
JOIN pedido_plato pp ON pp.pedido_id  = pe.id
JOIN plato        p  ON p.id          = pp.plato_id
GROUP BY u.id
ORDER BY gastado DESC;

-- 8. El rider estrella: el que ha repartido más pedidos
SELECT r.nombre, COUNT(*) AS pedidos
FROM pedido pe
JOIN rider r ON r.id = pe.rider_id
GROUP BY r.id
ORDER BY pedidos DESC
LIMIT 1;

-- 9. Los que cocinan en casa: usuarios que no han pedido nunca (LEFT JOIN)
SELECT u.nombre
FROM usuario u
LEFT JOIN pedido pe ON pe.usuario_id = u.id
WHERE pe.id IS NULL;

-- 10. Pedidos de fiesta: pedidos con más de 5 platos en total (GROUP BY + HAVING)
SELECT pe.id AS pedido, SUM(pp.cantidad) AS platos
FROM pedido pe
JOIN pedido_plato pp ON pp.pedido_id = pe.id
GROUP BY pe.id
HAVING SUM(pp.cantidad) > 5;

-- RETO: tarjeta rechazada. Pedidos que costaron más que el saldo del usuario
SELECT u.nombre, pe.id AS pedido, SUM(p.precio * pp.cantidad) AS total, u.saldo
FROM usuario u
JOIN pedido       pe ON pe.usuario_id = u.id
JOIN pedido_plato pp ON pp.pedido_id  = pe.id
JOIN plato        p  ON p.id          = pp.plato_id
GROUP BY pe.id
HAVING SUM(p.precio * pp.cantidad) > u.saldo;