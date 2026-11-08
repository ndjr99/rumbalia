
-- =============================================================================
-- PROYECTO: DISEÑADOR INTELIGENTE DE PLANES TURÍSTICOS
-- MVP - SPRINT 1
-- Script SQL idempotente: estructura y datos iniciales
-- Motor: PostgreSQL
-- =============================================================================


-- =============================================================================
-- 1. TABLA DE USUARIOS
-- =============================================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    contrasena_cifrada VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL
        CHECK (rol IN ('asesor', 'administrador', 'cliente')),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_eliminacion TIMESTAMP NULL
);

ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS eliminado BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS fecha_eliminacion TIMESTAMP NULL;


-- =============================================================================
-- 2. TABLA DE DESTINOS
-- =============================================================================

CREATE TABLE IF NOT EXISTS destinos (
    id_destino SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    pais VARCHAR(50) NOT NULL,
    continente VARCHAR(30) NOT NULL,
    imagen_url TEXT
);


-- =============================================================================
-- 3. TABLA DE PLANES TURÍSTICOS
-- =============================================================================

CREATE TABLE IF NOT EXISTS planes (
    id_plan SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    id_destino INT REFERENCES destinos(id_destino),
    id_asesor INT REFERENCES usuarios(id_usuario),
    duracion_dias INT NOT NULL CHECK (duracion_dias > 0),
    presupuesto NUMERIC(12, 2) NOT NULL CHECK (presupuesto > 0),
    tipo_viajero VARCHAR(50) NOT NULL,
    intereses TEXT NOT NULL,
    costo_estimado NUMERIC(12, 2) DEFAULT 0.0
        CHECK (costo_estimado >= 0),
    estado VARCHAR(20) DEFAULT 'Borrador'
        CHECK (estado IN ('Borrador', 'Pendiente', 'Publicado')),
    incluye TEXT,
    no_incluye TEXT,
    imagen_url TEXT,
    descuento_porcentaje NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (descuento_porcentaje >= 0 AND descuento_porcentaje <= 90),
    oferta_fecha_inicio DATE,
    oferta_fecha_fin DATE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migraciones seguras para bases de datos existentes.
ALTER TABLE planes ADD COLUMN IF NOT EXISTS imagen_url TEXT;\nALTER TABLE planes ADD COLUMN IF NOT EXISTS descripcion TEXT;
ALTER TABLE planes ADD COLUMN IF NOT EXISTS descuento_porcentaje NUMERIC(5,2) NOT NULL DEFAULT 0;
ALTER TABLE planes ADD COLUMN IF NOT EXISTS oferta_fecha_inicio DATE;
ALTER TABLE planes ADD COLUMN IF NOT EXISTS oferta_fecha_fin DATE;


-- Galería de fotografías propia de cada plan (no comparte imágenes entre destinos).
CREATE TABLE IF NOT EXISTS imagenes_plan (
    id_imagen SERIAL PRIMARY KEY,
    id_plan INT NOT NULL REFERENCES planes(id_plan) ON DELETE CASCADE,
    imagen_url TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 4. TABLA DE ITINERARIOS
-- =============================================================================

CREATE TABLE IF NOT EXISTS itinerarios (
    id_itinerario SERIAL PRIMARY KEY,
    id_plan INT UNIQUE
        REFERENCES planes(id_plan) ON DELETE CASCADE,
    generado_por_ia BOOLEAN DEFAULT TRUE
);


-- =============================================================================
-- 5. TABLA DE DÍAS DEL ITINERARIO
-- =============================================================================

CREATE TABLE IF NOT EXISTS dias_itinerario (
    id_dia SERIAL PRIMARY KEY,
    id_itinerario INT
        REFERENCES itinerarios(id_itinerario) ON DELETE CASCADE,
    numero_dia INT NOT NULL CHECK (numero_dia > 0),
    descripcion_resumen TEXT NOT NULL
);


-- =============================================================================
-- 6. TABLA DE REVISIONES DEL ADMINISTRADOR
-- =============================================================================

CREATE TABLE IF NOT EXISTS revisiones (
    id_revision SERIAL PRIMARY KEY,
    id_plan INT REFERENCES planes(id_plan) ON DELETE CASCADE,
    id_admin INT REFERENCES usuarios(id_usuario),
    decision VARCHAR(20) NOT NULL
        CHECK (decision IN ('Aprobado', 'Rechazado')),
    motivo TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =============================================================================
-- DATOS INICIALES
-- =============================================================================


-- =============================================================================
-- 7. USUARIOS INICIALES
-- Contraseña de prueba: 123456
-- =============================================================================

INSERT INTO usuarios (
    nombre,
    correo,
    contrasena_cifrada,
    rol
)
SELECT
    'Juan Torres',
    'asesor@turismo.com',
    'pbkdf2:sha256:260000$uG8WdJ3T$6800d9b4c09d571f30e00d9d20c3a2f8b50e303d7c3855a8cf7a1b66b6e4e0b0',
    'asesor'
WHERE NOT EXISTS (
    SELECT 1
    FROM usuarios
    WHERE correo = 'asesor@turismo.com'
);


INSERT INTO usuarios (
    nombre,
    correo,
    contrasena_cifrada,
    rol
)
SELECT
    'Laura Admin',
    'admin@turismo.com',
    'pbkdf2:sha256:260000$uG8WdJ3T$6800d9b4c09d571f30e00d9d20c3a2f8b50e303d7c3855a8cf7a1b66b6e4e0b0',
    'administrador'
WHERE NOT EXISTS (
    SELECT 1
    FROM usuarios
    WHERE correo = 'admin@turismo.com'
);


INSERT INTO usuarios (
    nombre,
    correo,
    contrasena_cifrada,
    rol
)
SELECT
    'Carlos Viajero',
    'cliente@gmail.com',
    'pbkdf2:sha256:260000$uG8WdJ3T$6800d9b4c09d571f30e00d9d20c3a2f8b50e303d7c3855a8cf7a1b66b6e4e0b0',
    'cliente'
WHERE NOT EXISTS (
    SELECT 1
    FROM usuarios
    WHERE correo = 'cliente@gmail.com'
);


-- =============================================================================
-- 8. DESTINOS INICIALES
-- =============================================================================

INSERT INTO destinos (
    nombre,
    pais,
    continente,
    imagen_url
)
SELECT
    'San Andrés',
    'Colombia',
    'América',
    'https://images.unsplash.com/photo-1590523741831-ab7e8b8f9c7f'
WHERE NOT EXISTS (
    SELECT 1 FROM destinos WHERE nombre = 'San Andrés'
);


INSERT INTO destinos (
    nombre,
    pais,
    continente,
    imagen_url
)
SELECT
    'Machu Picchu',
    'Perú',
    'América',
    'https://images.unsplash.com/photo-1526392060635-9d6019884377'
WHERE NOT EXISTS (
    SELECT 1 FROM destinos WHERE nombre = 'Machu Picchu'
);


INSERT INTO destinos (
    nombre,
    pais,
    continente,
    imagen_url
)
SELECT
    'París',
    'Francia',
    'Europa',
    'https://images.unsplash.com/photo-1502602898657-3e91760cbb34'
WHERE NOT EXISTS (
    SELECT 1 FROM destinos WHERE nombre = 'París'
);


INSERT INTO destinos (
    nombre,
    pais,
    continente,
    imagen_url
)
SELECT
    'Tokio',
    'Japón',
    'Asia',
    'https://images.unsplash.com/photo-1503899036084-c55cdd92da26'
WHERE NOT EXISTS (
    SELECT 1 FROM destinos WHERE nombre = 'Tokio'
);


INSERT INTO destinos (
    nombre,
    pais,
    continente,
    imagen_url
)
SELECT
    'España',
    'España',
    'Europa',
    'https://images.unsplash.com/photo-1539037116277-4db20889f2d4'
WHERE NOT EXISTS (
    SELECT 1 FROM destinos WHERE nombre = 'España'
);


-- =============================================================================
-- 9. CORREGIR DESTINOS DE PLANES ANTIGUOS DE ESPAÑA
-- =============================================================================

UPDATE planes p
SET id_destino = (
    SELECT d.id_destino
    FROM destinos d
    WHERE d.nombre = 'España'
    ORDER BY d.id_destino
    LIMIT 1
)
WHERE (
    p.nombre ILIKE '%España%'
    OR p.nombre ILIKE '%Madrid%'
    OR p.nombre ILIKE '%Toledo%'
    OR p.nombre ILIKE '%Córdoba%'
    OR p.nombre ILIKE '%Granada%'
    OR p.nombre ILIKE '%Sevilla%'
)
AND p.id_destino = (
    SELECT d.id_destino
    FROM destinos d
    WHERE d.nombre = 'San Andrés'
    ORDER BY d.id_destino
    LIMIT 1
);


-- =============================================================================
-- 10. PLANES DE PRUEBA INICIALES
-- Los identificadores se obtienen mediante consultas.
-- No se asume que los IDs sean 1 o 2.
-- =============================================================================

-- SAN ANDRÉS

INSERT INTO planes (
    nombre,
    id_destino,
    id_asesor,
    duracion_dias,
    presupuesto,
    tipo_viajero,
    intereses,
    costo_estimado,
    estado,
    incluye,
    no_incluye
)
SELECT
    'San Andrés Caribeño - 5 días',
    d.id_destino,
    u.id_usuario,
    5,
    2500000.00,
    'Familia',
    'Playa, gastronomía',
    2500000.00,
    'Publicado',
    'Tiquetes aéreos, hotel 4 estrellas y tour acuático.',
    'Gastos personales y desayunos.'
FROM destinos d
CROSS JOIN usuarios u
WHERE d.nombre = 'San Andrés'
AND u.correo = 'asesor@turismo.com'
AND NOT EXISTS (
    SELECT 1
    FROM planes p
    WHERE p.nombre = 'San Andrés Caribeño - 5 días'
);


-- MACHU PICCHU

INSERT INTO planes (
    nombre,
    id_destino,
    id_asesor,
    duracion_dias,
    presupuesto,
    tipo_viajero,
    intereses,
    costo_estimado,
    estado,
    incluye,
    no_incluye
)
SELECT
    'Aventura Machu Picchu - 5 días',
    d.id_destino,
    u.id_usuario,
    5,
    3500000.00,
    'Pareja',
    'Cultura, senderismo',
    3500000.00,
    'Publicado',
    'Hospedaje, entradas a ruinas y guía especializado.',
    'Vuelos internacionales.'
FROM destinos d
CROSS JOIN usuarios u
WHERE d.nombre = 'Machu Picchu'
AND u.correo = 'asesor@turismo.com'
AND NOT EXISTS (
    SELECT 1
    FROM planes p
    WHERE p.nombre = 'Aventura Machu Picchu - 5 días'
);


-- =============================================================================
-- 11. REPARAR RELACIONES DE LOS PLANES DE PRUEBA EXISTENTES
-- =============================================================================

UPDATE planes p
SET
    id_destino = d.id_destino,
    id_asesor = u.id_usuario
FROM destinos d, usuarios u
WHERE p.nombre = 'San Andrés Caribeño - 5 días'
AND d.nombre = 'San Andrés'
AND u.correo = 'asesor@turismo.com';


UPDATE planes p
SET
    id_destino = d.id_destino,
    id_asesor = u.id_usuario
FROM destinos d, usuarios u
WHERE p.nombre = 'Aventura Machu Picchu - 5 días'
AND d.nombre = 'Machu Picchu'
AND u.correo = 'asesor@turismo.com';


-- =============================================================================
-- 12. CREAR ITINERARIOS DE LOS PLANES DE PRUEBA
-- =============================================================================

INSERT INTO itinerarios (
    id_plan,
    generado_por_ia
)
SELECT
    p.id_plan,
    FALSE
FROM planes p
WHERE p.nombre IN (
    'San Andrés Caribeño - 5 días',
    'Aventura Machu Picchu - 5 días'
)
AND NOT EXISTS (
    SELECT 1
    FROM itinerarios i
    WHERE i.id_plan = p.id_plan
);


-- =============================================================================
-- 13. INSERTAR LOS DÍAS DE LOS ITINERARIOS
-- No se duplican los días si el script vuelve a ejecutarse.
-- =============================================================================

INSERT INTO dias_itinerario (
    id_itinerario,
    numero_dia,
    descripcion_resumen
)
SELECT
    i.id_itinerario,
    d.numero_dia,
    d.descripcion_resumen
FROM planes p
JOIN itinerarios i
    ON i.id_plan = p.id_plan
JOIN (
    VALUES

    -- SAN ANDRÉS

    (
        'San Andrés Caribeño - 5 días',
        1,
        'Llegada a San Andrés, instalación en el hotel y recorrido por el centro de la isla.'
    ),
    (
        'San Andrés Caribeño - 5 días',
        2,
        'Excursión al Acuario y Johnny Cay para disfrutar de sus playas y aguas cristalinas.'
    ),
    (
        'San Andrés Caribeño - 5 días',
        3,
        'Recorrido por la isla, visita a La Piscinita y actividades de playa.'
    ),
    (
        'San Andrés Caribeño - 5 días',
        4,
        'Tour acuático y tiempo libre para disfrutar de la gastronomía local.'
    ),
    (
        'San Andrés Caribeño - 5 días',
        5,
        'Desayuno, tiempo libre y regreso al lugar de origen.'
    ),

    -- MACHU PICCHU

    (
        'Aventura Machu Picchu - 5 días',
        1,
        'Llegada a Cusco, traslado al alojamiento y recorrido por el centro histórico.'
    ),
    (
        'Aventura Machu Picchu - 5 días',
        2,
        'Visita al Valle Sagrado de los Incas y recorrido por sus principales sitios arqueológicos.'
    ),
    (
        'Aventura Machu Picchu - 5 días',
        3,
        'Traslado a Aguas Calientes y preparación para la visita a Machu Picchu.'
    ),
    (
        'Aventura Machu Picchu - 5 días',
        4,
        'Visita guiada a Machu Picchu, exploración de las ruinas y regreso a Cusco.'
    ),
    (
        'Aventura Machu Picchu - 5 días',
        5,
        'Desayuno, tiempo libre y regreso al lugar de origen.'
    )

) AS d(nombre_plan, numero_dia, descripcion_resumen)
    ON p.nombre = d.nombre_plan
WHERE NOT EXISTS (
    SELECT 1
    FROM dias_itinerario di
    WHERE di.id_itinerario = i.id_itinerario
    AND di.numero_dia = d.numero_dia
);


-- =============================================================================
-- FIN DEL SCRIPT
-- DISEÑADOR INTELIGENTE DE PLANES TURÍSTICOS - MVP SPRINT 1
-- =============================================================================


-- =============================================================================
-- 8. SOLICITUDES DE CONTACTO DE CLIENTES
-- El cliente no necesita crear una cuenta para manifestar interés.
-- =============================================================================

CREATE TABLE IF NOT EXISTS solicitudes_contacto (
    id_solicitud SERIAL PRIMARY KEY,
    id_plan INT NOT NULL
        REFERENCES planes(id_plan) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL,
    telefono VARCHAR(30) NOT NULL,
    mensaje TEXT,
    estado VARCHAR(20) NOT NULL DEFAULT 'Nueva'
        CHECK (estado IN ('Nueva', 'En gestión', 'Atendida')),
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    archivada BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_archivado TIMESTAMP NULL,
    archivada_por INTEGER NULL REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_por INTEGER NULL REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
    eliminada BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_eliminacion TIMESTAMP NULL,
    eliminada_por INTEGER NULL REFERENCES usuarios(id_usuario) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_solicitudes_plan
    ON solicitudes_contacto(id_plan);


-- =============================================================================
-- MIGRACIÓN IDEMPOTENTE: GESTIÓN Y TRAZABILIDAD DE SOLICITUDES
-- También actualiza instalaciones existentes donde la tabla ya estaba creada.
-- =============================================================================
ALTER TABLE solicitudes_contacto
    ADD COLUMN IF NOT EXISTS archivada BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS fecha_archivado TIMESTAMP NULL,
    ADD COLUMN IF NOT EXISTS archivada_por INTEGER NULL REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS actualizado_por INTEGER NULL REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS eliminada BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS fecha_eliminacion TIMESTAMP NULL,
    ADD COLUMN IF NOT EXISTS eliminada_por INTEGER NULL REFERENCES usuarios(id_usuario) ON DELETE SET NULL;

DO $$
DECLARE restriccion RECORD;
BEGIN
    FOR restriccion IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'solicitudes_contacto'::regclass
          AND contype = 'c'
          AND pg_get_constraintdef(oid) ILIKE '%estado%'
    LOOP
        EXECUTE format('ALTER TABLE solicitudes_contacto DROP CONSTRAINT %I', restriccion.conname);
    END LOOP;
END $$;

UPDATE solicitudes_contacto SET estado = 'En gestión' WHERE estado = 'Contactada';
UPDATE solicitudes_contacto SET estado = 'Atendida' WHERE estado = 'Cerrada';
UPDATE solicitudes_contacto SET fecha_actualizacion = COALESCE(fecha_actualizacion, fecha_creacion, CURRENT_TIMESTAMP);

ALTER TABLE solicitudes_contacto
    ADD CONSTRAINT solicitudes_contacto_estado_check
    CHECK (estado IN ('Nueva', 'En gestión', 'Atendida'));

CREATE INDEX IF NOT EXISTS idx_solicitudes_plan_estado
    ON solicitudes_contacto(id_plan, estado);
CREATE INDEX IF NOT EXISTS idx_solicitudes_archivadas
    ON solicitudes_contacto(archivada, fecha_archivado DESC);


-- Historial de reasignaciones cuando un asesor deja la plataforma.
CREATE TABLE IF NOT EXISTS historial_asignaciones_planes (
    id_historial SERIAL PRIMARY KEY,
    id_plan INTEGER NOT NULL REFERENCES planes(id_plan) ON DELETE CASCADE,
    id_asesor_anterior INTEGER REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
    id_asesor_nuevo INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    id_admin INTEGER REFERENCES usuarios(id_usuario),
    fecha_asignacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
