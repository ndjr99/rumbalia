
import os
import sys
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from werkzeug.utils import secure_filename

from model.logic import (
    DatosViajero,
    PlanTuristico,
    GeneradorItinerarioIA,
    RevisionPlan
)
from controller.planes_controller import PlanesController


# ============================================================
# CONFIGURACIÓN
# ============================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "clave_desarrollo_turismo_cambiar_en_produccion"
)

app.config.update(
    MAX_CONTENT_LENGTH=6 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=(
        os.getenv("FLASK_ENV", "").lower() == "production"
    )
)

# La aplicación sirve el frontend desde el mismo origen.
# Si se despliega por separado, configura los orígenes permitidos.
CORS(app, supports_credentials=True)

CONTINENTES_VALIDOS = {
    "América",
    "Europa",
    "Asia",
    "África",
    "Oceanía"
}

EXTENSIONES_VALIDAS = {"jpg", "jpeg", "png", "webp"}

CARPETA_DESTINOS = os.path.join(
    BASE_DIR,
    "static",
    "uploads",
    "destinos"
)

os.makedirs(CARPETA_DESTINOS, exist_ok=True)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def usuario_actual():
    return session.get("usuario")


def requiere_rol(rol):
    usuario = usuario_actual()

    if not usuario:
        return None, (
            jsonify({"error": "Debes iniciar sesión."}),
            401
        )

    if usuario.get("rol") != rol:
        return None, (
            jsonify({"error": "No tienes permisos para esta operación."}),
            403
        )

    return usuario, None


def eliminar_archivo_si_existe(ruta):
    if ruta and os.path.isfile(ruta):
        try:
            os.remove(ruta)
        except OSError:
            app.logger.warning(
                "No se pudo eliminar el archivo temporal: %s",
                ruta
            )


def validar_imagen_subida(imagen):
    """
    Valida extensión, tamaño y firma del archivo.
    Devuelve los bytes y la extensión normalizada.
    """
    if not imagen or not imagen.filename:
        return None, None

    nombre_seguro = secure_filename(imagen.filename)

    if "." not in nombre_seguro:
        raise ValueError("El archivo no tiene una extensión válida.")

    extension = nombre_seguro.rsplit(".", 1)[1].lower()

    if extension not in EXTENSIONES_VALIDAS:
        raise ValueError(
            "Formato no permitido. Usa JPG, PNG o WEBP."
        )

    contenido = imagen.read()

    if not contenido:
        raise ValueError("La imagen está vacía.")

    if len(contenido) > 5 * 1024 * 1024:
        raise ValueError("La imagen no puede superar los 5 MB.")

    firmas = {
        "jpg": contenido.startswith(b"\xff\xd8\xff"),
        "jpeg": contenido.startswith(b"\xff\xd8\xff"),
        "png": contenido.startswith(b"\x89PNG\r\n\x1a\n"),
        "webp": (
            len(contenido) >= 12
            and contenido[:4] == b"RIFF"
            and contenido[8:12] == b"WEBP"
        )
    }

    if not firmas.get(extension, False):
        raise ValueError(
            "El contenido del archivo no corresponde a una imagen válida."
        )

    return contenido, extension


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return send_from_directory(BASE_DIR, "index.html")


# ============================================================
# LOGIN Y SESIONES
# ============================================================

@app.route("/api/login", methods=["POST"])
def login():
    datos = request.get_json(silent=True) or {}

    correo = datos.get("correo")
    contrasena = datos.get("contrasena")

    if (
        not isinstance(correo, str)
        or not correo.strip()
        or not isinstance(contrasena, str)
        or not contrasena
    ):
        return jsonify({
            "error": "Ingresa el correo y la contraseña."
        }), 400

    try:
        usuario = PlanesController.buscar_usuario_por_correo(
            correo.strip()
        )

        if not usuario or not usuario.verificar_contrasena(contrasena):
            return jsonify({
                "error": "Credenciales inválidas. Verifica el correo y la contraseña."
            }), 401

        # Evita conservar datos de una sesión anterior al autenticarse.
        session.clear()
        session["usuario"] = usuario.to_dict()

        return jsonify({
            "mensaje": "Inicio de sesión exitoso.",
            "usuario": session["usuario"]
        }), 200

    except Exception:
        app.logger.exception("Error al iniciar sesión")

        return jsonify({
            "error": "Error interno al iniciar sesión."
        }), 500


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "mensaje": "Sesión cerrada correctamente."
    }), 200


@app.route("/api/sesion-actual", methods=["GET"])
def sesion_actual():
    return jsonify(usuario_actual()), 200


# ============================================================
# CATÁLOGO PÚBLICO DE PLANES
# ============================================================

@app.route("/api/planes", methods=["GET"])
def obtener_planes():
    try:
        continente = request.args.get("continente")

        if continente and continente != "Todos":
            if continente not in CONTINENTES_VALIDOS:
                return jsonify({
                    "error": "El continente seleccionado no es válido."
                }), 400

        planes = PlanesController.obtener_todos_publicados(continente)

        return jsonify(planes), 200

    except Exception:
        app.logger.exception("Error al obtener planes publicados")

        return jsonify({
            "error": "Error al obtener los planes."
        }), 500


@app.route("/api/planes/<int:id_plan>", methods=["GET"])
def obtener_detalle_plan(id_plan):
    try:
        plan = PlanesController.buscar_plan(id_plan)

        if not plan or plan.estado != "Publicado":
            return jsonify({
                "error": "Plan no encontrado."
            }), 404

        return jsonify(plan.to_dict()), 200

    except Exception:
        app.logger.exception("Error al consultar el detalle del plan")

        return jsonify({
            "error": "Error interno al consultar el plan."
        }), 500


# ============================================================
# PLANES DEL ASESOR
# ============================================================

@app.route(
    "/api/asesor/mis-planes/<int:id_asesor>",
    methods=["GET"]
)
def obtener_planes_asesor(id_asesor):
    usuario, error = requiere_rol("asesor")

    if error:
        return error

    if usuario["id_usuario"] != id_asesor:
        return jsonify({
            "error": "No puedes consultar los planes de otro asesor."
        }), 403

    try:
        planes = PlanesController.obtener_planes_asesor(id_asesor)
        return jsonify(planes), 200

    except Exception:
        app.logger.exception("Error al consultar planes del asesor")

        return jsonify({
            "error": "Error al obtener los planes del asesor."
        }), 500


# ============================================================
# CREAR PLAN Y GENERAR ITINERARIO
# ============================================================

@app.route("/api/planes/generar-ia", methods=["POST"])
def generar_plan_ia():
    usuario, error = requiere_rol("asesor")

    if error:
        return error

    ruta_imagen_guardada = None

    try:
        datos = request.form

        destino = datos.get("destino", "").strip()
        pais = datos.get("pais", "").strip()
        continente = datos.get("continente", "").strip()
        duracion = datos.get("duracion")
        presupuesto = datos.get("presupuesto")
        tipo_viajero = datos.get("tipo_viajero", "").strip()
        intereses = datos.get("intereses", "").strip()

        # Validaciones de campos obligatorios.
        if not destino:
            raise ValueError("El nombre del destino es obligatorio.")

        if not pais:
            raise ValueError("El país es obligatorio.")

        if continente not in CONTINENTES_VALIDOS:
            raise ValueError("Selecciona un continente válido.")

        if not duracion or not presupuesto:
            raise ValueError(
                "La duración y el presupuesto son obligatorios."
            )

        if not tipo_viajero:
            raise ValueError("El tipo de viajero es obligatorio.")

        if not intereses:
            raise ValueError("Los intereses son obligatorios.")

        datos_viajero = DatosViajero(
            duracion_dias=duracion,
            presupuesto=presupuesto,
            tipo_viajero=tipo_viajero,
            intereses=intereses
        )

        # Validar y guardar imagen opcional.
        imagen = request.files.get("imagen")
        imagen_url = None

        if imagen and imagen.filename:
            contenido, extension = validar_imagen_subida(imagen)

            nombre_archivo = f"{uuid.uuid4().hex}.{extension}"
            ruta_imagen_guardada = os.path.join(
                CARPETA_DESTINOS,
                nombre_archivo
            )

            with open(ruta_imagen_guardada, "wb") as archivo:
                archivo.write(contenido)

            imagen_url = (
                f"/static/uploads/destinos/{nombre_archivo}"
            )

        # Generar el itinerario.
        itinerario = GeneradorItinerarioIA.generar(
            destino,
            datos_viajero
        )

        if not itinerario.esta_completo(datos_viajero.duracion_dias):
            raise ValueError(
                "El itinerario generado no contiene todos los días. "
                "Intenta generar el plan nuevamente."
            )

        plan = PlanTuristico(
            id_plan=None,
            nombre=f"{destino} - {datos_viajero.duracion_dias} días",
            destino=destino,
            datos_viajero=datos_viajero,
            id_asesor=usuario["id_usuario"],
            costo_estimado=datos_viajero.presupuesto,
            estado="Borrador",
            itinerario=itinerario,
            imagen_url=imagen_url
        )

        id_plan = PlanesController.insertar_plan_con_itinerario(
            plan,
            pais,
            continente,
            imagen_url
        )

        plan_guardado = PlanesController.buscar_plan(id_plan)

        if not plan_guardado:
            raise RuntimeError(
                "No fue posible recuperar el plan recién guardado."
            )

        # La imagen ya está asociada al destino y al plan.
        ruta_imagen_guardada = None

        return jsonify({
            "mensaje": "Plan generado correctamente.",
            "plan": plan_guardado.to_dict()
        }), 201

    except TimeoutError as error:
        if (
            ruta_imagen_guardada
            and os.path.exists(ruta_imagen_guardada)
        ):
            os.remove(ruta_imagen_guardada)

        return jsonify({
            "error": str(error),
            "codigo": "IA_TIMEOUT",
            "reintentar": True
        }), 504

    except ValueError as error:
        if (
            ruta_imagen_guardada
            and os.path.exists(ruta_imagen_guardada)
        ):
            os.remove(ruta_imagen_guardada)

        return jsonify({
            "error": str(error),
            "codigo": "DATOS_INVALIDOS",
            "reintentar": True
        }), 400

    except RuntimeError as error:
        if (
            ruta_imagen_guardada
            and os.path.exists(ruta_imagen_guardada)
        ):
            os.remove(ruta_imagen_guardada)

        app.logger.warning(
            "No fue posible generar el itinerario: %s",
            error
        )

        return jsonify({
            "error": str(error),
            "codigo": "IA_ERROR",
            "reintentar": True
        }), 502

    except Exception:
        if (
            ruta_imagen_guardada
            and os.path.exists(ruta_imagen_guardada)
        ):
            os.remove(ruta_imagen_guardada)

        app.logger.exception("Error al generar el plan")

        return jsonify({
            "error": (
                "Ocurrió un error inesperado al generar el itinerario."
            ),
            "codigo": "ERROR_INTERNO",
            "reintentar": True
        }), 500


# ============================================================
# EDITAR ITINERARIO (HU-05)
# ============================================================

@app.route(
    "/api/planes/<int:id_plan>/itinerario",
    methods=["PUT"]
)
def editar_itinerario(id_plan):
    usuario, error = requiere_rol("asesor")

    if error:
        return error

    try:
        plan = PlanesController.buscar_plan(id_plan)

        if not plan:
            return jsonify({"error": "Plan no encontrado."}), 404

        if plan.id_asesor != usuario["id_usuario"]:
            return jsonify({
                "error": "No puedes editar un plan de otro asesor."
            }), 403

        if plan.estado != "Borrador":
            return jsonify({
                "error": "Solo puedes editar planes en borrador."
            }), 409

        datos = request.get_json(silent=True) or {}
        dias = datos.get("dias")

        PlanesController.actualizar_itinerario(id_plan, dias)

        plan_actualizado = PlanesController.buscar_plan(id_plan)

        return jsonify({
            "mensaje": "Itinerario actualizado correctamente.",
            "plan": plan_actualizado.to_dict()
        }), 200

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    except Exception:
        app.logger.exception("Error al editar el itinerario")

        return jsonify({
            "error": "No fue posible guardar los cambios del itinerario."
        }), 500


# ============================================================
# EDITAR COSTO E INFORMACIÓN COMERCIAL
# ============================================================

@app.route(
    "/api/planes/<int:id_plan>/informacion",
    methods=["PUT"]
)
def editar_informacion_plan(id_plan):
    usuario, error = requiere_rol("asesor")

    if error:
        return error

    try:
        plan = PlanesController.buscar_plan(id_plan)

        if not plan:
            return jsonify({"error": "Plan no encontrado."}), 404

        if plan.id_asesor != usuario["id_usuario"]:
            return jsonify({
                "error": "No puedes modificar un plan de otro asesor."
            }), 403

        if plan.estado != "Borrador":
            return jsonify({
                "error": "Solo puedes modificar planes en borrador."
            }), 409

        datos = request.get_json(silent=True) or {}

        if "costo_estimado" not in datos:
            return jsonify({
                "error": "El costo estimado es obligatorio."
            }), 400

        PlanesController.actualizar_informacion_plan(
            id_plan=id_plan,
            incluye=datos.get("incluye"),
            no_incluye=datos.get("no_incluye"),
            costo_estimado=datos.get("costo_estimado")
        )

        return jsonify({
            "mensaje": "Información del plan actualizada correctamente."
        }), 200

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    except Exception:
        app.logger.exception("Error al actualizar información del plan")

        return jsonify({
            "error": "No fue posible guardar la información del plan."
        }), 500


# ============================================================
# ENVIAR PLAN A REVISIÓN (HU-06)
# ============================================================

@app.route(
    "/api/planes/<int:id_plan>/enviar-revision",
    methods=["POST"]
)
def enviar_revision(id_plan):
    usuario, error = requiere_rol("asesor")

    if error:
        return error

    try:
        plan = PlanesController.buscar_plan(id_plan)

        if not plan:
            return jsonify({"error": "Plan no encontrado."}), 404

        if plan.id_asesor != usuario["id_usuario"]:
            return jsonify({
                "error": "No puedes enviar a revisión un plan de otro asesor."
            }), 403

        nuevo_estado = plan.enviar_a_revision()

        PlanesController.actualizar_estado(
            id_plan,
            nuevo_estado
        )

        return jsonify({
            "mensaje": "Plan enviado a revisión exitosamente.",
            "estado": nuevo_estado
        }), 200

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    except Exception:
        app.logger.exception("Error al enviar plan a revisión")

        return jsonify({
            "error": "Error interno al enviar el plan a revisión."
        }), 500


# ============================================================
# ADMINISTRADOR: PLANES PENDIENTES
# ============================================================

@app.route("/api/admin/pendientes", methods=["GET"])
def obtener_pendientes_admin():
    _, error = requiere_rol("administrador")

    if error:
        return error

    try:
        planes = PlanesController.obtener_pendientes_admin()
        return jsonify(planes), 200

    except Exception:
        app.logger.exception("Error al consultar planes pendientes")

        return jsonify({
            "error": "Error al obtener los planes pendientes."
        }), 500


# ============================================================
# ADMINISTRADOR: DETALLE DE UN PLAN PENDIENTE
# ============================================================

@app.route(
    "/api/admin/pendientes/<int:id_plan>",
    methods=["GET"]
)
def detalle_pendiente_admin(id_plan):
    _, error = requiere_rol("administrador")

    if error:
        return error

    try:
        plan = PlanesController.buscar_plan(id_plan)

        if not plan or plan.estado != "Pendiente":
            return jsonify({
                "error": "No se encontró un plan pendiente con ese identificador."
            }), 404

        resultado = plan.to_dict()

        cursor = PlanesController.obtener_cursor()

        try:
            cursor.execute(
                """
                SELECT nombre
                FROM usuarios
                WHERE id_usuario = %s;
                """,
                (plan.id_asesor,)
            )
            fila = cursor.fetchone()
            resultado["nombre_asesor"] = fila[0] if fila else "Asesor"
        finally:
            PlanesController._cerrar_cursor(cursor)

        return jsonify(resultado), 200

    except Exception:
        app.logger.exception("Error al consultar el detalle pendiente")

        return jsonify({
            "error": "No fue posible consultar el plan pendiente."
        }), 500


# ============================================================
# ADMINISTRADOR: ESTADÍSTICAS
# ============================================================

@app.route("/api/admin/estadisticas", methods=["GET"])
def estadisticas_admin():
    _, error = requiere_rol("administrador")

    if error:
        return error

    try:
        estadisticas = PlanesController.obtener_estadisticas_admin()
        return jsonify(estadisticas), 200

    except Exception:
        app.logger.exception("Error al consultar estadísticas")

        return jsonify({
            "error": "No fue posible consultar las estadísticas."
        }), 500


# ============================================================
# ADMINISTRADOR: APROBAR O RECHAZAR (HU-07)
# ============================================================

@app.route("/api/admin/revision", methods=["POST"])
def procesar_revision():
    usuario, error = requiere_rol("administrador")

    if error:
        return error

    try:
        datos = request.get_json(silent=True) or {}

        id_plan = datos.get("id_plan")
        decision = datos.get("decision")
        motivo = datos.get("motivo", "")

        if id_plan is None:
            return jsonify({
                "error": "Debes indicar el plan que se va a revisar."
            }), 400

        try:
            id_plan = int(id_plan)
        except (TypeError, ValueError):
            return jsonify({
                "error": "El identificador del plan no es válido."
            }), 400

        revision = RevisionPlan(
            id_revision=None,
            id_plan=id_plan,
            id_admin=usuario["id_usuario"],
            decision=decision,
            motivo=motivo
        )

        nuevo_estado = PlanesController.registrar_revision(
            id_plan=id_plan,
            id_admin=usuario["id_usuario"],
            decision=decision,
            motivo=motivo
        )

        return jsonify({
            "mensaje": f"Plan {decision.lower()} exitosamente.",
            "estado": nuevo_estado,
            "revision": revision.to_dict()
        }), 200

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    except Exception:
        app.logger.exception("Error al procesar la revisión")

        return jsonify({
            "error": "Error interno al procesar la revisión."
        }), 500


# ============================================================
# MANEJO DE ERRORES HTTP
# ============================================================

@app.errorhandler(413)
def archivo_demasiado_grande(_error):
    return jsonify({
        "error": "La solicitud o la imagen supera el tamaño permitido."
    }), 413


# ============================================================
# INICIAR APLICACIÓN
# ============================================================

if __name__ == "__main__":
    try:
        PlanesController.crear_tabla()
        print("Base de datos inicializada correctamente.")
    except Exception:
        app.logger.exception(
            "No fue posible inicializar la base de datos."
        )

    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1"
    )
