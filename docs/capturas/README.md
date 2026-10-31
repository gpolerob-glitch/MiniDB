# Evidencias de ejecución

Estas capturas corresponden a pruebas ejecutadas desde MiniDB Studio con PostgreSQL y MongoDB locales en Docker.

| Archivo | Prueba |
| --- | --- |
| `01-postgresql-consulta.png` | Consulta SQL con dos filas después de INSERT, UPDATE y DELETE. |
| `02-postgresql-alter-table.png` | ALTER TABLE: nueva columna `correo`. |
| `03-postgresql-drop-table.png` | Verificación de DROP TABLE por medio de `to_regclass()`. |
| `04-mongodb-crear-coleccion.png` | Creación de la colección `estudiantes`. |
| `05-mongodb-consulta.png` | `find({})` mostrando un documento. |
| `06-mongodb-actualizacion.png` | Verificación de `updateOne()`. |
| `07-mongodb-error.png` | Mensaje de error de sintaxis controlado. |
| `08-mongodb-recuperacion.png` | Consulta válida ejecutada después de un error. |

Las capturas no incluyen necesariamente todas las pruebas realizadas; los ejemplos reproducibles se encuentran en `examples/`.
