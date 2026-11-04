import os
import sys
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
import secret_config

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
        conexion = psycopg2.connect(
            database=secret_config.PGDATABASE,
            user=secret_config.PGUSER,
            password=secret_config.PGPASSWORD,
            host=secret_config.PGHOST,
            port=secret_config.PGPORT,
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
                WHERE LOWER(correo) = LOWER(%s);
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
                    d.imagen_url
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
                imagen_url=fila[12]
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
                    d.continente,
                    d.imagen_url,
                    p.costo_estimado,
                    p.duracion_dias,
                    p.estado
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
                    "continente": fila[3],
                    "imagen_url": fila[4],
                    "costo_estimado": float(fila[5] or 0),
                    "duracion_dias": fila[6],
                    "estado": fila[7]
                }
                for fila in cursor.fetchall()
            ]

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
                WHERE rol = 'asesor';
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
            imagen_final = imagen_url or destino_existente[1]

            cursor.execute(
                """
                UPDATE destinos
                SET continente = %s,
                    imagen_url = %s
                WHERE id_destino = %s;
                """,
                (continente, imagen_final, id_destino)
            )

            return id_destino, imagen_final

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
                    nombre, id_destino, id_asesor,
                    duracion_dias, presupuesto,
                    tipo_viajero, intereses,
                    costo_estimado, estado,
                    incluye, no_incluye
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_plan;
                """,
                (
                    plan.nombre,
                    id_destino,
                    plan.id_asesor,
                    plan.datos_viajero.duracion_dias,
                    plan.datos_viajero.presupuesto,
                    plan.datos_viajero.tipo_viajero,
                    plan.datos_viajero.intereses,
                    plan.costo_estimado,
                    plan.estado,
                    plan.incluye,
                    plan.no_incluye
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
        costo_estimado
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

        cursor = PlanesController.obtener_cursor()

        try:
            cursor.execute(
                """
                UPDATE planes
                SET incluye = %s,
                    no_incluye = %s,
                    costo_estimado = %s
                WHERE id_plan = %s
                  AND estado = 'Borrador';
                """,
                (incluye, no_incluye, costo, id_plan)
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
