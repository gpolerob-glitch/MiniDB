-- Ejecutar una sentencia a la vez, o seleccionar/cargar varias juntas.
-- 1. Crear tabla (DDL)
CREATE TABLE IF NOT EXISTS estudiantes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    carrera VARCHAR(100) NOT NULL
);

-- 2. Insertar (DML)
INSERT INTO estudiantes (nombre, carrera)
VALUES ('Ana', 'Sistemas'), ('Carlos', 'Industrial');

-- 3. Consultar (DML)
SELECT * FROM estudiantes ORDER BY id;

-- 4. Modificar estructura (DDL)
ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS edad INTEGER;

-- 5. Actualizar (DML)
UPDATE estudiantes SET edad = 19 WHERE nombre = 'Ana';

-- 6. Ver cambios (DML)
SELECT * FROM estudiantes ORDER BY id;

-- 7. Eliminar dato (DML)
DELETE FROM estudiantes WHERE nombre = 'Carlos';

-- 8. Eliminar estructura (DDL): ejecutar solo al terminar la demostración.
-- DROP TABLE IF EXISTS estudiantes;
