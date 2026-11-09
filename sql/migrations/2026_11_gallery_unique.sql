-- Rumbalia: normalización de galería y prevención de rutas repetidas.
-- Ejecutar una sola vez sobre la base existente (respalda antes de aplicar).

BEGIN;

DELETE FROM imagenes_plan duplicada
USING imagenes_plan conservada
WHERE duplicada.id_plan = conservada.id_plan
  AND duplicada.imagen_url = conservada.imagen_url
  AND duplicada.id_imagen > conservada.id_imagen;

CREATE UNIQUE INDEX IF NOT EXISTS uq_imagenes_plan_plan_url
    ON imagenes_plan (id_plan, imagen_url);

COMMIT;
