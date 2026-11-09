import os
import sys
import unicodedata
from datetime import date
from pathlib import Path

# Raíz del proyecto: carpeta Turismo/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Permitir importar secret_config.py desde la raíz del proyecto.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Permitir importar los módulos que están dentro de src/.
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Buscar archivos secretos de Render
sys.path.insert(0, "/etc/secrets")

import psycopg2

try:
    import secret_config
except ImportError:
    secret_config = None


def _config_value(nombre, default=None):
    """Lee primero variables de entorno y luego secret_config.py."""
    valor = os.getenv(nombre)
    if valor not in (None, ""):
        return valor
    if secret_config is not None:
        valor = getattr(secret_config, nombre, None)
        if valor not in (None, ""):
            return valor
    return default

from model.logic import (
    PlanTuristico,
    DatosViajero,
    Itinerario,
    Usuario
)


class PlanesController:
    """Acceso a datos y operaciones de persistencia del módulo turístico."""

    ESTADOS_VALIDOS = {"Borrador", "Pendiente", "Publicado"}

    # ========================================================
    # CONEXIÓN A POSTGRESQL
    # ========================================================

    @staticmethod
    def obtener_cursor():
        requeridas = ("PGDATABASE", "PGUSER", "PGPASSWORD", "PGHOST")
        faltantes = [nombre for nombre in requeridas if not _config_value(nombre)]
        if faltantes:
            raise RuntimeError(
                "Faltan variables de configuración de PostgreSQL: "
                + ", ".join(faltantes)
            )

        conexion = psycopg2.connect(
            database=_config_value("PGDATABASE"),
            user=_config_value("PGUSER"),
            password=_config_value("PGPASSWORD"),
            host=_config_value("PGHOST"),
            port=int(_config_value("PGPORT", "5432")),
            sslmode="require",
            connect_timeout=10
        )
        return conexion.cursor()

    @staticmethod
    def _cerrar_cursor(cursor):
        if cursor is not None:
            conexion = cursor.connection
            cursor.close()
            conexion.close()

    # ========================================================
    # CREAR TABLAS E INICIALIZAR DATOS
    # ========================================================

    @staticmethod
    def crear_tabla():
        cursor = PlanesController.obtener_cursor()

        try:
            ruta_schema = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "sql",
                    "schema.sql"
                )
            )

            with open(ruta_schema, "r", encoding="utf-8") as archivo:
                cursor.execute(archivo.read())

            cursor.connection.commit()

        except Exception:
            cursor.connection.rollback()
            raise

        finally:
            PlanesController._cerrar_cursor(cursor)

    # ========================================================
    # USUARIOS
    # ========================================================

    @staticmethod
    def buscar_usuario_por_correo(correo: str):
        if not correo:
            return None

        cursor = PlanesController.obtener_cursor()

        try:
            cursor.execute(
                """
                SELECT id_usuario, nombre, correo,
                       contrasena_cifrada, rol
                FROM usuarios
                WHERE LOWER(correo) = LOWER(%s)
                  AND COALESCE(activo, TRUE) = TRUE
                  AND COALESCE(eliminado, FALSE) = FALSE;
                """,
                (correo.strip(),)
            )

            fila = cursor.fetchone()

            if not fila:
                return None

            return Usuario(
                id_usuario=fila[0],
                nombre=fila[1],
                correo=fila[2],
                contrasena_cifrada=fila[3],
                rol=fila[4]
            )

        finally:
            PlanesController._cerrar_cursor(cursor)

    # ========================================================
    # BUSCAR PLAN COMPLETO
    # ========================================================

    @staticmethod
    def buscar_plan(id_plan: int):
        cursor = PlanesController.obtener_cursor()

        try:
            cursor.execute(
                """
                SELECT
                    p.id_plan,
                    p.nombre,
                    d.nombre,
                    p.duracion_dias,
                    p.presupuesto,
                    p.tipo_viajero,
                    p.intereses,
                    p.id_asesor,
                    p.costo_estimado,
                    p.estado,
                    p.incluye,
                    p.no_incluye,
                    COALESCE(p.imagen_url, d.imagen_url),
                    p.descripcion
                FROM planes p
                JOIN destinos d ON p.id_destino = d.id_destino
                WHERE p.id_plan = %s;
                """,
                (id_plan,)
            )

            fila = cursor.fetchone()

            if not fila:
                return None

            datos_viajero = DatosViajero(
                duracion_dias=fila[3],
                presupuesto=float(fila[4]),
                tipo_viajero=fila[5],
                intereses=fila[6]
            )

            cursor.execute(
                """
                SELECT i.generado_por_ia,
                       di.numero_dia,
                       di.descripcion_resumen
                FROM itinerarios i
                LEFT JOIN dias_itinerario di
                    ON di.id_itinerario = i.id_itinerario
                WHERE i.id_plan = %s
                ORDER BY di.numero_dia ASC;
                """,
                (id_plan,)
            )

            filas_itinerario = cursor.fetchall()

            generado_por_ia = (
                bool(filas_itinerario[0][0])
                if filas_itinerario
                else False
            )

            itinerario = Itinerario(
                generado_por_ia=generado_por_ia
            )

            for fila_dia in filas_itinerario:
                if fila_dia[1] is not None:
                    itinerario.agregar_dia(
                        fila_dia[1],
                        fila_dia[2]
                    )

            cursor.execute(
                "SELECT DISTINCT imagen_url FROM imagenes_plan WHERE id_plan = %s ORDER BY imagen_url ASC;",
                (id_plan,)
            )
            imagenes_plan = [r[0] for r in cursor.fetchall()]

            # Recuperar la última decisión administrativa para que el asesor
            # conozca el motivo del rechazo al volver a editar el borrador.
            cursor.execute(
                """
                SELECT decision, motivo
                FROM revisiones
                WHERE id_plan = %s
                ORDER BY fecha DESC, id_revision DESC
                LIMIT 1;
                """,
                (id_plan,)
            )
            ultima_revision = cursor.fetchone()
            decision_revision = ultima_revision[0] if ultima_revision else None
            motivo_rechazo = (
                (ultima_revision[1] or "")
                if ultima_revision and ultima_revision[0] == "Rechazado"
                else ""
            )

            return PlanTuristico(
                id_plan=fila[0],
                nombre=fila[1],
                destino=fila[2],
                datos_viajero=datos_viajero,
                id_asesor=fila[7],
                costo_estimado=float(fila[8] or 0),
                estado=fila[9],
                itinerario=itinerario,
                incluye=fila[10] or "",
                no_incluye=fila[11] or "",
                imagen_url=fila[12],
                imagenes=imagenes_plan,
                decision_revision=decision_revision,
                motivo_rechazo=motivo_rechazo,
                descripcion=fila[13] or ""
            )

        finally:
            PlanesController._cerrar_cursor(cursor)

    # ========================================================
    # PLANES PUBLICADOS
    # ========================================================

    @staticmethod
    def obtener_todos_publicados(continente: str = None) -> list:
        cursor = PlanesController.obtener_cursor()

        try:
            consulta = """
                SELECT
                    p.id_plan,
                    p.nombre,
                    d.nombre,
                    d.pais,
                    d.continente,
                    COALESCE(p.imagen_url, d.imagen_url),
                    p.costo_estimado,
                    p.duracion_dias,
                    p.estado,
                    p.intereses
                FROM planes p
                JOIN destinos d ON p.id_destino = d.id_destino
                WHERE p.estado = 'Publicado'
            """

            parametros = []

            if continente and continente != "Todos":
                consulta += " AND d.continente = %s"
                parametros.append(continente)

            consulta += " ORDER BY p.id_plan DESC"

            cursor.execute(consulta, tuple(parametros))

            return [
                {
                    "id_plan": fila[0],
                    "nombre": fila[1],
                    "destino": fila[2],
                    "pais": fila[3],
                    "continente": fila[4],
                    "imagen_url": fila[5],
                    "costo_estimado": float(fila[6] or 0),
                    "duracion_dias": fila[7],
                    "estado": fila[8],
                    "intereses": fila[9] or ""
                }
                for fila in cursor.fetchall()
            ]

        finally:
            PlanesController._cerrar_cursor(cursor)

    @staticmethod
    def buscar_planes_publicos(
        texto: str = None,
        destino: str = None,
        pais: str = None,
        interes: str = None,
        presupuesto_max: float = None,
        duracion_min: int = None,
        duracion_max: int = None,
    ) -> list:
        """Busca únicamente planes publicados, filtrando destino y país por separado."""
        cursor = PlanesController.obtener_cursor()
        try:
            # Normaliza también el texto recibido para que "medellin" y
            # "Medellín" produzcan el mismo patrón de búsqueda.
            def normalizar(valor):
                if valor is None:
                    return None
                valor = unicodedata.normalize("NFD", str(valor))
                valor = "".join(c for c in valor if unicodedata.category(c) != "Mn")
                return valor.casefold().strip()

            # translate() evita depender de la extensión PostgreSQL unaccent.
            def campo_sin_tildes(campo):
                return f"translate(lower(COALESCE({campo}, '')), 'áéíóúüñ', 'aeiouun')"

            consulta = """
                SELECT p.id_plan, p.nombre, d.nombre, d.pais, d.continente,
                       COALESCE(p.imagen_url, d.imagen_url), p.costo_estimado,
                       p.duracion_dias, p.intereses, p.tipo_viajero,
                       COALESCE(p.descuento_porcentaje, 0), p.oferta_fecha_inicio, p.oferta_fecha_fin
                FROM planes p
                JOIN destinos d ON p.id_destino = d.id_destino
                WHERE p.estado = 'Publicado'
            """
            parametros = []
            if texto:
                patron = f"%{normalizar(texto)}%"
                consulta += f" AND ({campo_sin_tildes('d.nombre')} LIKE %s OR {campo_sin_tildes('d.pais')} LIKE %s OR {campo_sin_tildes('p.nombre')} LIKE %s)"
                parametros.extend([patron, patron, patron])
            if destino:
                consulta += f" AND {campo_sin_tildes('d.nombre')} LIKE %s"
                parametros.append(f"%{normalizar(destino)}%")
            if pais:
                consulta += f" AND {campo_sin_tildes('d.pais')} LIKE %s"
                parametros.append(f"%{normalizar(pais)}%")
            if interes:
                consulta += f" AND ({campo_sin_tildes('p.intereses')} LIKE %s OR {campo_sin_tildes('p.tipo_viajero')} LIKE %s)"
                patron = f"%{normalizar(interes)}%"
                parametros.extend([patron, patron])
            if presupuesto_max is not None:
                consulta += " AND p.costo_estimado <= %s"
                parametros.append(presupuesto_max)
            if duracion_min is not None:
                consulta += " AND p.duracion_dias >= %s"
                parametros.append(duracion_min)
            if duracion_max is not None:
                consulta += " AND p.duracion_dias <= %s"
                parametros.append(duracion_max)
            consulta += " ORDER BY p.id_plan DESC"
            cursor.execute(consulta, tuple(parametros))
            return [
                {
                    "id_plan": f[0], "nombre": f[1], "destino": f[2],
                    "pais": f[3], "continente": f[4], "imagen_url": f[5],
                    "costo_estimado": float(f[6] or 0), "duracion_dias": f[7],
                    "intereses": f[8] or "", "tipo_viajero": f[9] or "",
                    "descuento_porcentaje": float(f[10] or 0),
                    "oferta_fecha_inicio": f[11].isoformat() if f[11] else None,
                    "oferta_fecha_fin": f[12].isoformat() if f[12] else None
                }
                for f in cursor.fetchall()
            ]
        finally:
            PlanesController._cerrar_cursor(cursor)

    @staticmethod
    def obtener_ofertas_publicadas() -> list:
        """Devuelve planes publicados con descuento vigente en la fecha actual."""
        cursor = PlanesController.obtener_cursor()
        try:
            cursor.execute("""
                SELECT p.id_plan, p.nombre, d.nombre, d.pais, d.continente,
                       COALESCE(p.imagen_url, d.imagen_url), p.costo_estimado,
                       p.duracion_dias, p.intereses, p.tipo_viajero,
                       p.descuento_porcentaje, p.oferta_fecha_inicio, p.oferta_fecha_fin
                FROM planes p
                JOIN destinos d ON p.id_destino = d.id_destino
                WHERE p.estado = 'Publicado'
                  AND p.descuento_porcentaje > 0
                  AND CURRENT_DATE BETWEEN p.oferta_fecha_inicio AND p.oferta_fecha_fin
                ORDER BY p.oferta_fecha_fin ASC, p.id_plan DESC
            """)
            return [{
                "id_plan": f[0], "nombre": f[1], "destino": f[2], "pais": f[3],
                "continente": f[4], "imagen_url": f[5], "costo_estimado": float(f[6] or 0),
                "duracion_dias": f[7], "intereses": f[8] or "", "tipo_viajero": f[9] or "",
                "descuento_porcentaje": float(f[10] or 0),
                "oferta_fecha_inicio": f[11].isoformat() if f[11] else None,
                "oferta_fecha_fin": f[12].isoformat() if f[12] else None
            } for f in cursor.fetchall()]
        finally:
            PlanesController._cerrar_cursor(cursor)

    # ========================================================
    # PLANES DEL ASESOR
    # ========================================================

    @staticmethod
    def obtener_planes_asesor(id_asesor: int) -> list:
        cursor = PlanesController.obtener_cursor()

        try:
            cursor.execute(
                """
                SELECT
                    id_plan,
                    nombre,
                    duracion_dias,
                    costo_estimado,
                    estado
                FROM planes
                WHERE id_asesor = %s
                ORDER BY id_plan DESC;
                """,
                (id_asesor,)
            )

            return [
                {
                    "id_plan": fila[0],
                    "nombre": fila[1],
                    "duracion_dias": fila[2],
                    "costo_estimado": float(fila[3] or 0),
                    "estado": fila[4]
                }
                for fila in cursor.fetchall()
            ]

        finally:
            PlanesController._cerrar_cursor(cursor)

    # ========================================================
    # PLANES PENDIENTES DEL ADMINISTRADOR
    # ========================================================

    @staticmethod
    def obtener_pendientes_admin() -> list:
        cursor = PlanesController.obtener_cursor()

        try:
            cursor.execute(
                """
                SELECT
                    p.id_plan,
                    p.nombre,
                    u.nombre,
                    p.costo_estimado,
                    p.estado
                FROM planes p
                JOIN usuarios u ON p.id_asesor = u.id_usuario
                WHERE p.estado = 'Pendiente'
                ORDER BY p.id_plan ASC;
                """
            )

            return [
                {
                    "id_plan": fila[0],
                    "nombre": fila[1],
                    "nombre_asesor": fila[2],
                    "costo_estimado": float(fila[3] or 0),
                    "estado": fila[4]
                }
                for fila in cursor.fetchall()
            ]

        finally:
            PlanesController._cerrar_cursor(cursor)

    # ========================================================
    # ESTADÍSTICAS DEL ADMINISTRADOR
    # ========================================================

    @staticmethod
    def obtener_estadisticas_admin() -> dict:
        cursor = PlanesController.obtener_cursor()

        try:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM planes
                WHERE estado = 'Publicado';
                """
            )
            planes_publicados = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM usuarios
                WHERE rol = 'asesor'
                  AND COALESCE(activo, TRUE) = TRUE
                  AND COALESCE(eliminado, FALSE) = FALSE;
                """
            )
            asesores_activos = cursor.fetchone()[0]

            return {
                "planes_publicados": planes_publicados,
                "asesores_activos": asesores_activos
            }

        finally:
            PlanesController._cerrar_cursor(cursor)

    # ========================================================
    # BUSCAR O CREAR DESTINO
    # ========================================================

    @staticmethod
    def obtener_o_crear_destino(
        cursor,
        nombre,
        pais,
        continente,
        imagen_url=None
    ):
        cursor.execute(
            """
            SELECT id_destino, imagen_url
            FROM destinos
            WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s))
              AND LOWER(TRIM(pais)) = LOWER(TRIM(%s))
            LIMIT 1
            FOR UPDATE;
            """,
            (nombre, pais)
        )

        destino_existente = cursor.fetchone()

        if destino_existente:
            id_destino = destino_existente[0]
            # La fotografía nueva se guarda en planes.imagen_url.
            # El destino conserva su imagen general como respaldo.
            cursor.execute(
                """
                UPDATE destinos
                SET continente = %s
                WHERE id_destino = %s;
                """,
                (continente, id_destino)
            )

            return id_destino, destino_existente[1]

        cursor.execute(
            """
            INSERT INTO destinos (
                nombre, pais, continente, imagen_url
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id_destino;
            """,
            (nombre, pais, continente, imagen_url)
        )

        return cursor.fetchone()[0], imagen_url

    # ========================================================
    # INSERTAR PLAN E ITINERARIO
    # ========================================================

    @staticmethod
    def insertar_plan_con_itinerario(
        plan: PlanTuristico,
        pais: str,
        continente: str,
        imagen_url: str = None
    ) -> int:
        cursor = PlanesController.obtener_cursor()

        try:
            id_destino, imagen_final = (
                PlanesController.obtener_o_crear_destino(
                    cursor,
                    plan.destino,
                    pais,
                    continente,
                    imagen_url
                )
            )

            cursor.execute(
                """
                INSERT INTO planes (
                    nombre, descripcion, id_destino, id_asesor,
                    duracion_dias, presupuesto,
                    tipo_viajero, intereses,
                    costo_estimado, estado,
                    incluye, no_incluye, imagen_url
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_plan;
                """,
                (
                    plan.nombre,
                    plan.descripcion,
                    id_destino,
                    plan.id_asesor,
                    plan.datos_viajero.duracion_dias,
                    plan.datos_viajero.presupuesto,
                    plan.datos_viajero.tipo_viajero,
                    plan.datos_viajero.intereses,
                    plan.costo_estimado,
                    plan.estado,
                    plan.incluye,
                    plan.no_incluye,
                    plan.imagen_url
                )
            )

            id_plan = cursor.fetchone()[0]

            if plan.itinerario:
                cursor.execute(
                    """
                    INSERT INTO itinerarios (id_plan, generado_por_ia)
                    VALUES (%s, %s)
                    RETURNING id_itinerario;
                    """,
                    (id_plan, plan.itinerario.generado_por_ia)
                )

                id_itinerario = cursor.fetchone()[0]

                for dia in plan.itinerario.dias:
                    cursor.execute(
                        """
                        INSERT INTO dias_itinerario (
                            id_itinerario,
                            numero_dia,
                            descripcion_resumen
                        )
                        VALUES (%s, %s, %s);
                        """,
                        (
                            id_itinerario,
                            dia.numero_dia,
                            dia.descripcion_resumen
                        )
                    )

            cursor.connection.commit()
            return id_plan

        except Exception:
            cursor.connection.rollback()
            raise

        finally:
            PlanesController._cerrar_cursor(cursor)

    # ========================================================
    # ACTUALIZAR ITINERARIO
    # ========================================================

    @staticmethod
    def actualizar_itinerario(id_plan: int, dias: list):
        if not isinstance(dias, list) or not dias:
            raise ValueError("Debes enviar los días del itinerario.")

        cursor = PlanesController.obtener_cursor()

        try:
            cursor.execute(
                """
                SELECT p.estado, p.duracion_dias, i.id_itinerario
                FROM planes p
                LEFT JOIN itinerarios i ON i.id_plan = p.id_plan
                WHERE p.id_plan = %s
                FOR UPDATE OF p;
                """,
                (id_plan,)
            )

            fila = cursor.fetchone()

            if not fila:
                raise ValueError("El plan no existe.")

            estado, duracion, id_itinerario = fila

            if estado != "Borrador":
                raise ValueError(
                    "Solo puedes editar un plan que esté en borrador."
                )

            dias_normalizados = []
            numeros = set()

            for dia in dias:
                if not isinstance(dia, dict):
                    raise ValueError("El formato de un día no es válido.")

                numero = int(dia.get("numero_dia", 0))
                descripcion = str(
                    dia.get("descripcion_resumen", "")
                ).strip()

                if numero < 1 or numero > duracion:
                    raise ValueError("Hay un número de día fuera del rango.")

                if numero in numeros:
                    raise ValueError("No puede haber días duplicados.")

                if not descripcion:
                    raise ValueError(
                        f"La descripción del día {numero} es obligatoria."
                    )

                numeros.add(numero)
                dias_normalizados.append((numero, descripcion))

            if numeros != set(range(1, duracion + 1)):
                raise ValueError(
                    f"El itinerario debe contener exactamente "
                    f"los {duracion} días."
                )

            if not id_itinerario:
                cursor.execute(
                    """
                    INSERT INTO itinerarios (id_plan, generado_por_ia)
                    VALUES (%s, FALSE)
                    RETURNING id_itinerario;
                    """,
                    (id_plan,)
                )
                id_itinerario = cursor.fetchone()[0]

            cursor.execute(
                "DELETE FROM dias_itinerario WHERE id_itinerario = %s;",
                (id_itinerario,)
            )

            for numero, descripcion in sorted(dias_normalizados):
                cursor.execute(
                    """
                    INSERT INTO dias_itinerario (
                        id_itinerario, numero_dia, descripcion_resumen
                    )
                    VALUES (%s, %s, %s);
                    """,
                    (id_itinerario, numero, descripcion)
                )

            cursor.connection.commit()

        except Exception:
            cursor.connection.rollback()
            raise

        finally:
            PlanesController._cerrar_cursor(cursor)

    # ========================================================
    # ACTUALIZAR INFORMACIÓN COMERCIAL DEL PLAN
    # ========================================================

    @staticmethod
    def actualizar_informacion_plan(
        id_plan,
        incluye,
        no_incluye,
        costo_estimado,
        nombre=None,
        descripcion=None,
        descuento_porcentaje=0,
        oferta_fecha_inicio=None,
        oferta_fecha_fin=None
    ):
        incluye = str(incluye or "").strip()
        no_incluye = str(no_incluye or "").strip()

        if not incluye:
            raise ValueError("Debes especificar qué incluye el plan.")

        if not no_incluye:
            raise ValueError("Debes especificar qué no incluye el plan.")

        try:
            costo = float(costo_estimado)
        except (TypeError, ValueError):
            raise ValueError("El costo estimado debe ser numérico.")

        if costo < 0:
            raise ValueError("El costo estimado no puede ser negativo.")

        try:
            descuento = float(descuento_porcentaje or 0)
        except (TypeError, ValueError):
            raise ValueError("El descuento debe ser numérico.")
        if descuento < 0 or descuento > 90:
            raise ValueError("El descuento debe estar entre 0 y 90%.")
        if descuento > 0:
            if not oferta_fecha_inicio or not oferta_fecha_fin:
                raise ValueError("Indica las fechas de inicio y fin de la oferta.")
            try:
                fecha_inicio = date.fromisoformat(str(oferta_fecha_inicio))
                fecha_fin = date.fromisoformat(str(oferta_fecha_fin))
            except ValueError:
                raise ValueError("Las fechas de la oferta no tienen un formato válido.")
            if fecha_fin < fecha_inicio:
                raise ValueError("La fecha final no puede ser anterior a la inicial.")
            oferta_fecha_inicio = fecha_inicio
            oferta_fecha_fin = fecha_fin
        else:
            oferta_fecha_inicio = None
            oferta_fecha_fin = None

        cursor = PlanesController.obtener_cursor()

        try:
            cursor.execute(
                """
                UPDATE planes
                SET nombre = COALESCE(NULLIF(%s, ''), nombre),
                    descripcion = %s,
                    incluye = %s,
                    no_incluye = %s,
                    costo_estimado = %s,
                    descuento_porcentaje = %s,
                    oferta_fecha_inicio = %s,
                    oferta_fecha_fin = %s
                WHERE id_plan = %s
                  AND estado = 'Borrador';
                """,
                (nombre, descripcion, incluye, no_incluye, costo, descuento, oferta_fecha_inicio, oferta_fecha_fin, id_plan)
            )

            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT estado FROM planes WHERE id_plan = %s;",
                    (id_plan,)
                )
                fila = cursor.fetchone()

                if not fila:
                    raise ValueError("El plan no existe.")

                raise ValueError(
                    "Solo puedes modificar un plan en borrador."
                )

            cursor.connection.commit()

        except Exception:
            cursor.connection.rollback()
            raise

        finally:
            PlanesController._cerrar_cursor(cursor)

    # ========================================================
    # ACTUALIZAR ESTADO DEL PLAN
    # ========================================================

    @staticmethod
    def actualizar_estado(id_plan: int, nuevo_estado: str):
        if nuevo_estado not in PlanesController.ESTADOS_VALIDOS:
            raise ValueError("El estado solicitado no es válido.")

        cursor = PlanesController.obtener_cursor()

        try:
            cursor.execute(
                """
                UPDATE planes
                SET estado = %s
                WHERE id_plan = %s;
                """,
                (nuevo_estado, id_plan)
            )

            if cursor.rowcount == 0:
                raise ValueError("El plan no existe.")

            cursor.connection.commit()

        except Exception:
            cursor.connection.rollback()
            raise

        finally:
            PlanesController._cerrar_cursor(cursor)

    # ========================================================
    # REGISTRAR REVISIÓN DEL ADMINISTRADOR
    # ========================================================

    @staticmethod
    def registrar_revision(
        id_plan: int,
        id_admin: int,
        decision: str,
        motivo: str = ""
    ):
        if decision not in {"Aprobado", "Rechazado"}:
            raise ValueError(
                "La decisión debe ser 'Aprobado' o 'Rechazado'."
            )

        motivo = str(motivo or "").strip()

        cursor = PlanesController.obtener_cursor()

        try:
            cursor.execute(
                """
                SELECT estado
                FROM planes
                WHERE id_plan = %s
                FOR UPDATE;
                """,
                (id_plan,)
            )

            fila = cursor.fetchone()

            if not fila:
                raise ValueError("El plan no existe.")

            if fila[0] != "Pendiente":
                raise ValueError(
                    "El plan no está pendiente de revisión."
                )

            cursor.execute(
                """
                INSERT INTO revisiones (
                    id_plan, id_admin, decision, motivo
                )
                VALUES (%s, %s, %s, %s);
                """,
                (id_plan, id_admin, decision, motivo)
            )

            nuevo_estado = (
                "Publicado"
                if decision == "Aprobado"
                else "Borrador"
            )

            cursor.execute(
                """
                UPDATE planes
                SET estado = %s
                WHERE id_plan = %s;
                """,
                (nuevo_estado, id_plan)
            )

            cursor.connection.commit()
            return nuevo_estado

        except Exception:
            cursor.connection.rollback()
            raise

        finally:
            PlanesController._cerrar_cursor(cursor)


    # ========================================================
    # ACTUALIZAR IMAGEN INDIVIDUAL DEL PLAN
    # ========================================================

    @staticmethod
    def actualizar_imagen_plan(id_plan: int, imagen_url: str):
        cursor = PlanesController.obtener_cursor()
        try:
            cursor.execute(
                """
                SELECT imagen_url
                FROM planes
                WHERE id_plan = %s AND estado = 'Borrador'
                FOR UPDATE;
                """,
                (id_plan,)
            )
            fila = cursor.fetchone()
            if not fila:
                raise ValueError(
                    "El plan no existe o ya no está en borrador."
                )
            imagen_anterior = fila[0]
            cursor.execute(
                """
                UPDATE planes
                SET imagen_url = %s
                WHERE id_plan = %s;
                """,
                (imagen_url, id_plan)
            )
            cursor.connection.commit()
            return imagen_anterior
        except Exception:
            cursor.connection.rollback()
            raise
        finally:
            PlanesController._cerrar_cursor(cursor)

    @staticmethod
    def imagen_referenciada(imagen_url: str) -> bool:
        if not imagen_url:
            return False
        cursor = PlanesController.obtener_cursor()
        try:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM planes WHERE imagen_url = %s
                    UNION ALL
                    SELECT 1 FROM destinos WHERE imagen_url = %s
                );
                """,
                (imagen_url, imagen_url)
            )
            return bool(cursor.fetchone()[0])
        finally:
            PlanesController._cerrar_cursor(cursor)

    # ========================================================
    # GALERÍA DE IMÁGENES POR PLAN

    @staticmethod
    def agregar_imagenes_plan(id_plan: int, imagenes_url: list):
        cursor = PlanesController.obtener_cursor()
        try:
            # Normalizar el lote y evitar insertar dos veces una misma ruta.
            # La restricción UNIQUE de (id_plan, imagen_url) protege también
            # frente a solicitudes repetidas o concurrentes.
            urls_unicas = list(dict.fromkeys(
                str(url).strip() for url in (imagenes_url or []) if str(url).strip()
            ))
            for url in urls_unicas:
                cursor.execute(
                    """
                    INSERT INTO imagenes_plan (id_plan, imagen_url)
                    VALUES (%s, %s)
                    ON CONFLICT (id_plan, imagen_url) DO NOTHING;
                    """,
                    (id_plan, url)
                )
            cursor.connection.commit()
        except Exception:
            cursor.connection.rollback()
            raise
        finally:
            PlanesController._cerrar_cursor(cursor)

    @staticmethod
    def eliminar_imagen_galeria(id_plan: int, imagen_url: str) -> bool:
        cursor = PlanesController.obtener_cursor()
        try:
            cursor.execute(
                """
                DELETE FROM imagenes_plan
                WHERE id_plan = %s AND imagen_url = %s
                RETURNING id_imagen;
                """,
                (id_plan, imagen_url)
            )
            eliminada = cursor.fetchone() is not None
            cursor.connection.commit()
            return eliminada
        except Exception:
            cursor.connection.rollback()
            raise
        finally:
            PlanesController._cerrar_cursor(cursor)

    # SOLICITUDES DE CONTACTO DE CLIENTES
    # ========================================================

    @staticmethod
    def crear_solicitud_contacto(
        id_plan: int, nombre: str, correo: str,
        telefono: str, mensaje: str = ""
    ) -> int:
        cursor = PlanesController.obtener_cursor()
        try:
            cursor.execute(
                """
                INSERT INTO solicitudes_contacto
                    (id_plan, nombre, correo, telefono, mensaje)
                SELECT %s, %s, %s, %s, %s
                FROM planes
                WHERE id_plan = %s AND estado = 'Publicado'
                RETURNING id_solicitud;
                """,
                (id_plan, nombre, correo, telefono, mensaje, id_plan)
            )
            fila = cursor.fetchone()
            if not fila:
                raise ValueError(
                    "El plan ya no está disponible para solicitudes."
                )
            cursor.connection.commit()
            return fila[0]
        except Exception:
            cursor.connection.rollback()
            raise
        finally:
            PlanesController._cerrar_cursor(cursor)

    @staticmethod
    def obtener_solicitudes_asesor(id_asesor: int) -> list:
        cursor = PlanesController.obtener_cursor()
        try:
            cursor.execute(
                """
                SELECT
                    s.id_solicitud, s.nombre, s.correo, s.telefono,
                    s.mensaje, s.estado, s.fecha_creacion,
                    p.id_plan, p.nombre, s.fecha_actualizacion,
                    s.actualizado_por, ua.nombre
                FROM solicitudes_contacto s
                JOIN planes p ON p.id_plan = s.id_plan
                LEFT JOIN usuarios ua ON ua.id_usuario = s.actualizado_por
                WHERE p.id_asesor = %s AND COALESCE(s.archivada,FALSE)=FALSE AND COALESCE(s.eliminada,FALSE)=FALSE
                ORDER BY s.fecha_creacion DESC;
                """,
                (id_asesor,)
            )
            return [
                {
                    "id_solicitud": fila[0],
                    "nombre": fila[1],
                    "correo": fila[2],
                    "telefono": fila[3],
                    "mensaje": fila[4] or "",
                    "estado": fila[5],
                    "fecha_creacion": fila[6].isoformat(),
                    "id_plan": fila[7],
                    "nombre_plan": fila[8],
                    "fecha_actualizacion": fila[9].isoformat() if fila[9] else None,
                    "actualizado_por": fila[10],
                    "nombre_actualizador": fila[11]
                }
                for fila in cursor.fetchall()
            ]
        finally:
            PlanesController._cerrar_cursor(cursor)

    # ========================================================
    # ELIMINAR PLAN DEL ASESOR
    # ========================================================

    @staticmethod
    def eliminar_plan(id_plan: int) -> bool:
        """Elimina un borrador o un plan publicado de forma transaccional.

        Las claves foráneas de itinerarios y revisiones usan ON DELETE CASCADE,
        por lo que PostgreSQL elimina también sus registros dependientes.
        Los planes pendientes no se pueden eliminar durante la revisión.
        """
        cursor = PlanesController.obtener_cursor()

        try:
            cursor.execute(
                """
                SELECT estado
                FROM planes
                WHERE id_plan = %s
                FOR UPDATE;
                """,
                (id_plan,)
            )

            fila = cursor.fetchone()

            if not fila:
                return False

            if fila[0] not in {"Borrador", "Publicado"}:
                raise ValueError(
                    "Solo se pueden eliminar planes en borrador o publicados."
                )

            cursor.execute(
                "DELETE FROM planes WHERE id_plan = %s;",
                (id_plan,)
            )

            eliminado = cursor.rowcount > 0
            cursor.connection.commit()
            return eliminado

        except Exception:
            cursor.connection.rollback()
            raise

        finally:
            PlanesController._cerrar_cursor(cursor)
