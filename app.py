
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
    RevisionPlan,
    Usuario
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
    MAX_CONTENT_LENGTH=42 * 1024 * 1024,
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

# En Render, configura UPLOAD_FOLDER=/var/data/uploads/destinos y
# adjunta un Persistent Disk montado en /var/data. Si no se configura,
# se conserva la ruta local para desarrollo.
CARPETA_DESTINOS_LEGACY = os.path.join(
    BASE_DIR, "static", "uploads", "destinos"
)
CARPETA_DESTINOS = os.path.abspath(
    os.getenv("UPLOAD_FOLDER", CARPETA_DESTINOS_LEGACY)
)
os.makedirs(CARPETA_DESTINOS, exist_ok=True)


def migrar_imagenes_locales_a_almacenamiento_persistente():
    """Copia imágenes locales antiguas al volumen persistente, sin sobrescribir."""
    if os.path.abspath(CARPETA_DESTINOS) == os.path.abspath(CARPETA_DESTINOS_LEGACY):
        return
    if not os.path.isdir(CARPETA_DESTINOS_LEGACY):
        return

    import shutil

    for nombre in os.listdir(CARPETA_DESTINOS_LEGACY):
        origen = os.path.join(CARPETA_DESTINOS_LEGACY, nombre)
        destino = os.path.join(CARPETA_DESTINOS, nombre)
        if (
            os.path.isfile(origen)
            and nombre.lower().rsplit(".", 1)[-1] in EXTENSIONES_VALIDAS
            and not os.path.exists(destino)
        ):
            try:
                shutil.copy2(origen, destino)
            except OSError:
                app.logger.exception("No se pudo migrar la imagen %s al disco persistente", nombre)


migrar_imagenes_locales_a_almacenamiento_persistente()

if os.getenv("RENDER") and not os.getenv("UPLOAD_FOLDER"):
    app.logger.warning(
        "Rumbalia está en Render pero UPLOAD_FOLDER no está configurado; "
        "las imágenes se guardarán en el sistema efímero."
    )


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

    # Revalida el estado de la cuenta para revocar sesiones ya abiertas.
    cursor = None
    try:
        cursor = PlanesController.obtener_cursor()
        cursor.execute("SELECT COALESCE(activo, TRUE), COALESCE(eliminado, FALSE) FROM usuarios WHERE id_usuario=%s;", (usuario.get("id_usuario"),))
        fila = cursor.fetchone()
        if not fila or not fila[0] or fila[1]:
            session.clear()
            return None, (jsonify({"error": "Tu cuenta está desactivada o fue eliminada. Contacta al administrador."}), 401)
    except Exception:
        app.logger.exception("No fue posible validar el estado de la cuenta")
        return None, (jsonify({"error": "No fue posible validar tus permisos. Inténtalo nuevamente."}), 503)
    finally:
        if cursor is not None:
            PlanesController._cerrar_cursor(cursor)

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


@app.route("/static/uploads/destinos/<path:filename>", methods=["GET"])
def servir_imagen_destino(filename):
    """Sirve las imágenes desde el directorio persistente configurado."""
    return send_from_directory(CARPETA_DESTINOS, filename)


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


@app.route("/api/registro", methods=["POST"])
def registrar_cliente():
    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")
    correo = datos.get("correo")
    contrasena = datos.get("contrasena")
    acepta_datos = datos.get("acepta_datos") is True

    if not all(isinstance(v, str) for v in (nombre, correo, contrasena)):
        return jsonify({"error": "Completa todos los campos obligatorios."}), 400
    nombre = nombre.strip()
    correo = correo.strip().lower()
    if len(nombre) < 3 or len(nombre) > 100:
        return jsonify({"error": "El nombre debe tener entre 3 y 100 caracteres."}), 400
    import re
    if len(correo) > 100 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", correo):
        return jsonify({"error": "Ingresa un correo electrónico válido."}), 400
    if len(contrasena) < 8 or len(contrasena) > 128:
        return jsonify({"error": "La contraseña debe tener entre 8 y 128 caracteres."}), 400
    if not acepta_datos:
        return jsonify({"error": "Debes aceptar el tratamiento de tus datos para crear la cuenta."}), 400

    cursor = None
    try:
        cursor = PlanesController.obtener_cursor()
        cursor.execute("SELECT 1 FROM usuarios WHERE LOWER(correo)=LOWER(%s) LIMIT 1;", (correo,))
        if cursor.fetchone():
            return jsonify({"error": "Ya existe una cuenta con ese correo electrónico."}), 409
        cursor.execute("""
            INSERT INTO usuarios (nombre, correo, contrasena_cifrada, rol)
            VALUES (%s, %s, %s, 'cliente')
            ON CONFLICT (correo) DO NOTHING
            RETURNING id_usuario, nombre, correo, rol;
        """, (nombre, correo, Usuario.cifrar_contrasena(contrasena)))
        fila = cursor.fetchone()
        if not fila:
            cursor.connection.rollback()
            return jsonify({"error": "Ya existe una cuenta con ese correo electrónico."}), 409
        cursor.connection.commit()
        session.clear()
        session["usuario"] = {"id_usuario": fila[0], "nombre": fila[1], "correo": fila[2], "rol": fila[3]}
        return jsonify({"mensaje": "Cuenta creada correctamente.", "usuario": session["usuario"]}), 201
    except Exception:
        if cursor is not None: cursor.connection.rollback()
        app.logger.exception("Error al registrar cliente")
        return jsonify({"error": "No fue posible crear la cuenta. Inténtalo nuevamente."}), 500
    finally:
        if cursor is not None: PlanesController._cerrar_cursor(cursor)


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


@app.route("/api/planes/ofertas", methods=["GET"])
def obtener_ofertas_publicas():
    try:
        return jsonify(PlanesController.obtener_ofertas_publicadas()), 200
    except Exception:
        app.logger.exception("Error al consultar ofertas públicas")
        return jsonify({"error": "No fue posible cargar las ofertas."}), 500


@app.route("/api/planes/buscar", methods=["GET"])
def buscar_planes_publicos():
    """Búsqueda pública con filtros; nunca expone borradores ni planes pendientes."""
    try:
        def numero_opcional(nombre, tipo):
            valor = request.args.get(nombre, "").strip()
            if not valor:
                return None
            try:
                numero = tipo(valor)
            except (TypeError, ValueError):
                raise ValueError(f"El filtro {nombre} no es válido.")
            if numero < 0:
                raise ValueError(f"El filtro {nombre} no puede ser negativo.")
            return numero

        presupuesto_max = numero_opcional("presupuesto_max", float)
        duracion_min = numero_opcional("duracion_min", int)
        duracion_max = numero_opcional("duracion_max", int)
        if duracion_min is not None and duracion_max is not None and duracion_min > duracion_max:
            return jsonify({"error": "La duración mínima no puede superar la máxima."}), 400

        planes = PlanesController.buscar_planes_publicos(
            texto=request.args.get("q", "").strip() or None,
            destino=request.args.get("destino", "").strip() or None,
            pais=request.args.get("pais", "").strip() or None,
            interes=request.args.get("interes", "").strip() or None,
            presupuesto_max=presupuesto_max,
            duracion_min=duracion_min,
            duracion_max=duracion_max,
        )
        return jsonify(planes), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        app.logger.exception("Error al buscar planes públicos")
        return jsonify({"error": "No fue posible realizar la búsqueda."}), 500


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

@app.route("/api/asesor/planes/<int:id_plan>/volver-borrador", methods=["POST"])
def volver_plan_a_borrador(id_plan):
    """Retira un plan publicado del catálogo para que su asesor lo edite y reenvíe."""
    usuario, error = requiere_rol("asesor")
    if error:
        return error
    try:
        plan = PlanesController.buscar_plan(id_plan)
        if not plan:
            return jsonify({"error": "Plan no encontrado."}), 404
        if plan.id_asesor != usuario["id_usuario"]:
            return jsonify({"error": "No puedes modificar un plan de otro asesor."}), 403
        if plan.estado != "Publicado":
            return jsonify({"error": "Solo puedes devolver a borrador un plan publicado."}), 409
        PlanesController.actualizar_estado(id_plan, "Borrador")
        return jsonify({"mensaje": "El plan volvió a borrador. Ya no está visible para los clientes y debe enviarse nuevamente a revisión."}), 200
    except Exception:
        app.logger.exception("Error al devolver el plan a borrador")
        return jsonify({"error": "No fue posible devolver el plan a borrador."}), 500


@app.route(
    "/api/asesor/planes/<int:id_plan>",
    methods=["GET"]
)
def obtener_borrador_asesor(id_plan):
    usuario, error = requiere_rol("asesor")

    if error:
        return error

    try:
        plan = PlanesController.buscar_plan(id_plan)

        if not plan:
            return jsonify({
                "error": "Plan no encontrado."
            }), 404

        if plan.id_asesor != usuario["id_usuario"]:
            return jsonify({
                "error": "No puedes consultar un plan de otro asesor."
            }), 403

        if plan.estado != "Borrador":
            return jsonify({
                "error": "Solo puedes editar planes en borrador."
            }), 409

        return jsonify(plan.to_dict()), 200

    except Exception:
        app.logger.exception(
            "Error al recuperar el borrador del asesor"
        )

        return jsonify({
            "error": "No fue posible recuperar el borrador."
        }), 500

@app.route(
    "/api/asesor/planes/<int:id_plan>",
    methods=["DELETE"]
)
def eliminar_borrador_asesor(id_plan):
    usuario, error = requiere_rol("asesor")

    if error:
        return error

    try:
        plan = PlanesController.buscar_plan(id_plan)

        if not plan:
            return jsonify({
                "error": "Plan no encontrado."
            }), 404

        if plan.id_asesor != usuario["id_usuario"]:
            return jsonify({
                "error": "No puedes eliminar un plan de otro asesor."
            }), 403

        if plan.estado not in {"Borrador", "Publicado"}:
            return jsonify({
                "error": "Solo puedes eliminar planes en borrador o publicados."
            }), 409

        eliminado = PlanesController.eliminar_plan(id_plan)

        if not eliminado:
            return jsonify({
                "error": "No se pudo eliminar el plan."
            }), 404

        # Si la imagen era exclusiva del plan, limpiar el archivo local.
        imagen_plan = plan.imagen_url
        if (
            imagen_plan
            and imagen_plan.startswith("/static/uploads/destinos/")
            and not PlanesController.imagen_referenciada(imagen_plan)
        ):
            eliminar_archivo_si_existe(
                os.path.join(CARPETA_DESTINOS, os.path.basename(imagen_plan))
            )

        return jsonify({
            "mensaje": "Plan eliminado correctamente."
        }), 200

    except ValueError as error:
        return jsonify({"error": str(error)}), 409

    except Exception:
        app.logger.exception("Error al eliminar el plan")

        return jsonify({
            "error": "No fue posible eliminar el plan."
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
        nombre_plan, descripcion_plan, itinerario = GeneradorItinerarioIA.generar(
            destino,
            datos_viajero,
            pais=pais,
            continente=continente
        )

        if not itinerario.esta_completo(datos_viajero.duracion_dias):
            raise ValueError(
                "El itinerario generado no contiene todos los días. "
                "Intenta generar el plan nuevamente."
            )

        plan = PlanTuristico(
            id_plan=None,
            nombre=nombre_plan[:150],
            descripcion=descripcion_plan,
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
            costo_estimado=datos.get("costo_estimado"),
            nombre=datos.get("nombre"),
            descripcion=datos.get("descripcion"),
            descuento_porcentaje=datos.get("descuento_porcentaje", 0),
            oferta_fecha_inicio=datos.get("oferta_fecha_inicio"),
            oferta_fecha_fin=datos.get("oferta_fecha_fin")
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
# ACTUALIZAR IMAGEN DEL PLAN (ASESOR)
# ============================================================

@app.route(
    "/api/planes/<int:id_plan>/imagen",
    methods=["PUT"]
)
def actualizar_imagen_plan(id_plan):
    usuario, error = requiere_rol("asesor")
    if error:
        return error

    ruta_nueva = None
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
                "error": "Solo puedes cambiar la imagen de un borrador."
            }), 409

        imagen = request.files.get("imagen")
        if not imagen or not imagen.filename:
            return jsonify({
                "error": "Selecciona una imagen para continuar."
            }), 400

        contenido, extension = validar_imagen_subida(imagen)
        nombre_archivo = f"{uuid.uuid4().hex}.{extension}"
        ruta_nueva = os.path.join(CARPETA_DESTINOS, nombre_archivo)
        with open(ruta_nueva, "wb") as archivo:
            archivo.write(contenido)

        nueva_url = f"/static/uploads/destinos/{nombre_archivo}"
        imagen_anterior = PlanesController.actualizar_imagen_plan(
            id_plan, nueva_url
        )

        # Eliminar la anterior solo si era un archivo local y ya no está referenciada.
        if (
            imagen_anterior
            and imagen_anterior.startswith("/static/uploads/destinos/")
            and imagen_anterior != nueva_url
            and not PlanesController.imagen_referenciada(imagen_anterior)
        ):
            nombre_anterior = os.path.basename(imagen_anterior)
            eliminar_archivo_si_existe(
                os.path.join(CARPETA_DESTINOS, nombre_anterior)
            )

        return jsonify({
            "mensaje": "Imagen del plan actualizada correctamente.",
            "imagen_url": nueva_url
        }), 200

    except ValueError as error:
        eliminar_archivo_si_existe(ruta_nueva)
        return jsonify({"error": str(error)}), 400
    except Exception:
        eliminar_archivo_si_existe(ruta_nueva)
        app.logger.exception("Error al actualizar la imagen del plan")
        return jsonify({
            "error": "No fue posible actualizar la imagen del plan."
        }), 500


# ============================================================
# GALERÍA DE IMÁGENES DEL PLAN (ASESOR)
# ============================================================

@app.route("/api/planes/<int:id_plan>/imagenes", methods=["POST", "DELETE"])
def agregar_imagenes_galeria(id_plan):
    usuario, error = requiere_rol("asesor")
    if error:
        return error
    rutas_guardadas = []
    try:
        plan = PlanesController.buscar_plan(id_plan)
        if not plan:
            return jsonify({"error": "Plan no encontrado."}), 404
        if plan.id_asesor != usuario["id_usuario"]:
            return jsonify({"error": "No puedes modificar un plan de otro asesor."}), 403
        if plan.estado != "Borrador":
            return jsonify({"error": "Solo puedes modificar la galería de un borrador."}), 409

        if request.method == "DELETE":
            datos = request.get_json(silent=True) or {}
            imagen_url = str(datos.get("imagen_url") or "").strip()
            if not imagen_url:
                return jsonify({"error": "No se indicó la fotografía que deseas quitar."}), 400
            if not PlanesController.eliminar_imagen_galeria(id_plan, imagen_url):
                return jsonify({"error": "La fotografía ya no existe en la galería."}), 404
            return jsonify({"mensaje": "Fotografía retirada de la galería."}), 200

        archivos = request.files.getlist("imagenes")
        if not archivos or len(archivos) > 8:
            return jsonify({"error": "Selecciona entre 1 y 8 fotografías por carga."}), 400
        urls = []
        for imagen in archivos:
            if not imagen or not imagen.filename:
                continue
            contenido, extension = validar_imagen_subida(imagen)
            nombre = f"{uuid.uuid4().hex}.{extension}"
            ruta = os.path.join(CARPETA_DESTINOS, nombre)
            with open(ruta, "wb") as archivo:
                archivo.write(contenido)
            rutas_guardadas.append(ruta)
            urls.append(f"/static/uploads/destinos/{nombre}")
        if not urls:
            return jsonify({"error": "No se recibieron imágenes válidas."}), 400
        PlanesController.agregar_imagenes_plan(id_plan, urls)
        return jsonify({"mensaje": "Fotografías agregadas a la galería.", "imagenes": urls}), 201
    except ValueError as error:
        for ruta in rutas_guardadas:
            eliminar_archivo_si_existe(ruta)
        return jsonify({"error": str(error)}), 400
    except Exception:
        for ruta in rutas_guardadas:
            eliminar_archivo_si_existe(ruta)
        app.logger.exception("Error al agregar fotografías a la galería")
        return jsonify({"error": "No fue posible guardar las fotografías."}), 500


# ============================================================
# SOLICITUD DE CONTACTO DEL CLIENTE (SIN CUENTA)
# ============================================================

@app.route(
    "/api/planes/<int:id_plan>/solicitudes",
    methods=["POST"]
)
def crear_solicitud_cliente(id_plan):
    # Las solicitudes pueden enviarse como visitante o desde una cuenta cliente,
    # pero nunca desde cuentas internas (asesor/administrador).
    usuario = usuario_actual()
    if usuario and usuario.get("rol") != "cliente":
        return jsonify({"error": "Las cuentas de asesor y administrador no pueden enviar solicitudes de clientes."}), 403
    try:
        datos = request.get_json(silent=True) or {}
        nombre = str(datos.get("nombre", "")).strip()
        correo = str(datos.get("correo", "")).strip().lower()
        telefono = str(datos.get("telefono", "")).strip()
        mensaje = str(datos.get("mensaje", "")).strip()

        if len(nombre) < 2 or len(nombre) > 100:
            raise ValueError("Ingresa un nombre válido (2 a 100 caracteres).")
        if len(correo) > 150 or "@" not in correo or "." not in correo.split("@")[-1]:
            raise ValueError("Ingresa un correo electrónico válido.")
        if len(telefono) < 7 or len(telefono) > 30:
            raise ValueError("Ingresa un teléfono válido.")
        if len(mensaje) > 1000:
            raise ValueError("El mensaje no puede superar los 1000 caracteres.")

        id_solicitud = PlanesController.crear_solicitud_contacto(
            id_plan, nombre, correo, telefono, mensaje
        )
        return jsonify({
            "mensaje": (
                "¡Solicitud enviada! Un asesor se pondrá en contacto contigo "
                "pronto para brindarte más información."
            ),
            "id_solicitud": id_solicitud
        }), 201

    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        app.logger.exception("Error al registrar solicitud del cliente")
        return jsonify({
            "error": "No fue posible enviar tu solicitud. Inténtalo nuevamente."
        }), 500


@app.route("/api/asesor/solicitudes", methods=["GET"])
def obtener_solicitudes_asesor():
    usuario, error = requiere_rol("asesor")
    if error:
        return error
    try:
        solicitudes = PlanesController.obtener_solicitudes_asesor(
            usuario["id_usuario"]
        )
        return jsonify(solicitudes), 200
    except Exception:
        app.logger.exception("Error al consultar solicitudes del asesor")
        return jsonify({
            "error": "No fue posible cargar las solicitudes."
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
            # La revisión administrativa debe incluir las condiciones completas
            # de la oferta antes de que el administrador apruebe el plan.
            cursor.execute(
                """
                SELECT
                    COALESCE(descuento_porcentaje, 0),
                    oferta_fecha_inicio,
                    oferta_fecha_fin
                FROM planes
                WHERE id_plan = %s;
                """,
                (id_plan,)
            )
            oferta = cursor.fetchone()
            resultado["descuento_porcentaje"] = float(oferta[0] or 0) if oferta else 0
            resultado["oferta_fecha_inicio"] = oferta[1].isoformat() if oferta and oferta[1] else None
            resultado["oferta_fecha_fin"] = oferta[2].isoformat() if oferta and oferta[2] else None

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


@app.route("/api/admin/usuarios", methods=["GET"])
def listar_usuarios_admin():
    admin, error = requiere_rol("administrador")
    if error: return error
    cursor = None
    try:
        cursor = PlanesController.obtener_cursor()
        # La propia cuenta no se muestra: no puede gestionarse ni eliminarse desde esta pantalla.
        cursor.execute("SELECT id_usuario, nombre, correo, rol, COALESCE(activo, TRUE) FROM usuarios WHERE id_usuario <> %s AND COALESCE(eliminado, FALSE)=FALSE ORDER BY rol, nombre;", (admin.get("id_usuario"),))
        return jsonify([{"id_usuario": r[0], "nombre": r[1], "correo": r[2], "rol": r[3], "activo": r[4]} for r in cursor.fetchall()]), 200
    except Exception:
        app.logger.exception("Error al listar usuarios")
        return jsonify({"error": "No fue posible consultar los usuarios."}), 500
    finally:
        if cursor is not None: PlanesController._cerrar_cursor(cursor)


@app.route("/api/admin/usuarios/eliminados", methods=["GET"])
def listar_usuarios_eliminados_admin():
    _, error = requiere_rol("administrador")
    if error: return error
    cursor = None
    try:
        cursor = PlanesController.obtener_cursor()
        cursor.execute("""SELECT id_usuario, nombre, correo, rol, fecha_eliminacion
                          FROM usuarios WHERE COALESCE(eliminado, FALSE)=TRUE
                          ORDER BY fecha_eliminacion DESC NULLS LAST, nombre;""")
        return jsonify([{"id_usuario":r[0],"nombre":r[1],"correo":r[2],"rol":r[3],"fecha_eliminacion":r[4].isoformat() if r[4] else None} for r in cursor.fetchall()]), 200
    except Exception:
        app.logger.exception("Error al consultar historial de cuentas eliminadas")
        return jsonify({"error":"No fue posible consultar el historial de cuentas eliminadas."}), 500
    finally:
        if cursor is not None: PlanesController._cerrar_cursor(cursor)


@app.route("/api/admin/usuarios", methods=["POST"])
def crear_usuario_admin():
    _, error = requiere_rol("administrador")
    if error: return error
    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")
    correo = datos.get("correo")
    contrasena = datos.get("contrasena")
    rol = datos.get("rol")
    if not all(isinstance(v, str) for v in (nombre, correo, contrasena, rol)):
        return jsonify({"error": "Completa nombre, correo, contraseña y rol."}), 400
    nombre, correo, rol = nombre.strip(), correo.strip().lower(), rol.strip().lower()
    if len(nombre) < 3 or len(nombre) > 100:
        return jsonify({"error": "El nombre debe tener entre 3 y 100 caracteres."}), 400
    import re
    if len(correo) > 100 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", correo):
        return jsonify({"error": "Ingresa un correo válido."}), 400
    if len(contrasena) < 8 or len(contrasena) > 128:
        return jsonify({"error": "La contraseña debe tener entre 8 y 128 caracteres."}), 400
    if rol not in ("asesor", "administrador"):
        return jsonify({"error": "Solo puedes crear cuentas de asesor o administrador."}), 400
    cursor = None
    try:
        cursor = PlanesController.obtener_cursor()
        cursor.execute("""INSERT INTO usuarios (nombre, correo, contrasena_cifrada, rol, activo)
                          VALUES (%s, %s, %s, %s, TRUE)
                          ON CONFLICT (correo) DO NOTHING
                          RETURNING id_usuario, nombre, correo, rol, activo;""",
                       (nombre, correo, Usuario.cifrar_contrasena(contrasena), rol))
        fila = cursor.fetchone()
        if not fila:
            cursor.connection.rollback()
            return jsonify({"error": "Ya existe una cuenta con ese correo electrónico."}), 409
        cursor.connection.commit()
        return jsonify({"mensaje": "Usuario creado correctamente.", "usuario": {"id_usuario":fila[0],"nombre":fila[1],"correo":fila[2],"rol":fila[3],"activo":fila[4]}}), 201
    except Exception:
        if cursor: cursor.connection.rollback()
        app.logger.exception("Error al crear usuario administrativo")
        return jsonify({"error": "No fue posible crear el usuario."}), 500
    finally:
        if cursor: PlanesController._cerrar_cursor(cursor)


@app.route("/api/admin/usuarios/<int:id_usuario>/estado", methods=["PATCH"])
def cambiar_estado_usuario_admin(id_usuario):
    admin, error = requiere_rol("administrador")
    if error: return error
    datos = request.get_json(silent=True) or {}
    activo = datos.get("activo")
    if not isinstance(activo, bool):
        return jsonify({"error": "Indica si la cuenta debe estar activa."}), 400
    if id_usuario == admin["id_usuario"] and not activo:
        return jsonify({"error": "No puedes desactivar tu propia cuenta."}), 400
    cursor = None
    try:
        cursor = PlanesController.obtener_cursor()
        cursor.execute("LOCK TABLE usuarios IN SHARE ROW EXCLUSIVE MODE;")
        cursor.execute("SELECT rol, activo, COALESCE(eliminado,FALSE) FROM usuarios WHERE id_usuario=%s FOR UPDATE;", (id_usuario,))
        usuario = cursor.fetchone()
        if not usuario or usuario[2]: return jsonify({"error": "Usuario no encontrado o eliminado."}), 404
        if usuario[0] == "administrador" and not activo and usuario[1]:
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol='administrador' AND COALESCE(activo,TRUE)=TRUE AND COALESCE(eliminado,FALSE)=FALSE;")
            if cursor.fetchone()[0] <= 1:
                cursor.connection.rollback()
                return jsonify({"error": "No puedes desactivar al último administrador activo."}), 409
        cursor.execute("UPDATE usuarios SET activo=%s WHERE id_usuario=%s;", (activo,id_usuario))
        cursor.connection.commit()
        return jsonify({"mensaje": "Estado de la cuenta actualizado."}), 200
    except Exception:
        if cursor: cursor.connection.rollback()
        app.logger.exception("Error al cambiar estado de usuario")
        return jsonify({"error": "No fue posible actualizar la cuenta."}), 500
    finally:
        if cursor: PlanesController._cerrar_cursor(cursor)


@app.route("/api/admin/usuarios/<int:id_usuario>", methods=["DELETE"])
def eliminar_usuario_admin(id_usuario):
    admin, error = requiere_rol("administrador")
    if error: return error
    if id_usuario == admin["id_usuario"]:
        return jsonify({"error": "No puedes eliminar tu propia cuenta."}), 400
    cursor = None
    try:
        cursor = PlanesController.obtener_cursor()
        cursor.execute("LOCK TABLE usuarios IN SHARE ROW EXCLUSIVE MODE;")
        cursor.execute("SELECT rol, activo, COALESCE(eliminado,FALSE) FROM usuarios WHERE id_usuario=%s FOR UPDATE;", (id_usuario,))
        usuario = cursor.fetchone()
        if not usuario or usuario[2]: return jsonify({"error": "Usuario no encontrado o ya eliminado."}), 404
        if usuario[0] == "administrador" and usuario[1]:
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol='administrador' AND COALESCE(activo,TRUE)=TRUE AND COALESCE(eliminado,FALSE)=FALSE;")
            if cursor.fetchone()[0] <= 1:
                cursor.connection.rollback()
                return jsonify({"error": "No puedes eliminar al último administrador activo."}), 409
        # Anonimización irreversible: conserva la fila técnica por integridad referencial,
        # pero elimina los datos personales y bloquea el acceso.
        cursor.execute("""
            UPDATE usuarios
               SET activo=FALSE, eliminado=TRUE,
                   fecha_eliminacion=CURRENT_TIMESTAMP,
                   nombre='Usuario eliminado',
                   correo='eliminado+' || id_usuario::TEXT || '@rumbalia.invalid',
                   contrasena_cifrada='CUENTA_ELIMINADA'
             WHERE id_usuario=%s;
        """, (id_usuario,))
        cursor.connection.commit()
        return jsonify({"mensaje": "Cuenta eliminada y datos personales anonimizados. Se conservaron únicamente las relaciones necesarias para el historial."}), 200
    except Exception:
        if cursor: cursor.connection.rollback()
        app.logger.exception("Error al eliminar usuario")
        return jsonify({"error": "No fue posible eliminar la cuenta."}), 500
    finally:
        if cursor: PlanesController._cerrar_cursor(cursor)


@app.route("/api/admin/planes-sin-asesor", methods=["GET"])
def listar_planes_sin_asesor_admin():
    """Planes cuyo asesor fue eliminado; permite recuperarlos y reasignarlos."""
    _, error = requiere_rol("administrador")
    if error: return error
    cursor = None
    try:
        cursor = PlanesController.obtener_cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_asignaciones_planes (
                id_historial SERIAL PRIMARY KEY,
                id_plan INTEGER NOT NULL REFERENCES planes(id_plan) ON DELETE CASCADE,
                id_asesor_anterior INTEGER REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
                id_asesor_nuevo INTEGER NOT NULL REFERENCES usuarios(id_usuario),
                id_admin INTEGER REFERENCES usuarios(id_usuario),
                fecha_asignacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            SELECT p.id_plan, p.nombre, p.estado, p.fecha_creacion,
                   u.nombre, u.id_usuario,
                   COALESCE((SELECT COUNT(*) FROM historial_asignaciones_planes h WHERE h.id_plan=p.id_plan),0)
              FROM planes p
              LEFT JOIN usuarios u ON u.id_usuario=p.id_asesor
             WHERE p.id_asesor IS NULL OR COALESCE(u.eliminado,FALSE)=TRUE
             ORDER BY p.fecha_creacion DESC NULLS LAST, p.id_plan DESC;
        """)
        planes=[{"id_plan":r[0],"nombre":r[1],"estado":r[2],"fecha_creacion":r[3].isoformat() if r[3] else None,"asesor_anterior":r[4] or "Sin asesor","id_asesor_anterior":r[5],"reasignaciones":r[6]} for r in cursor.fetchall()]
        cursor.execute("SELECT id_usuario,nombre,correo FROM usuarios WHERE rol='asesor' AND COALESCE(activo,TRUE)=TRUE AND COALESCE(eliminado,FALSE)=FALSE ORDER BY nombre;")
        asesores=[{"id_usuario":r[0],"nombre":r[1],"correo":r[2]} for r in cursor.fetchall()]
        cursor.connection.commit()
        return jsonify({"planes":planes,"asesores":asesores}),200
    except Exception:
        if cursor: cursor.connection.rollback()
        app.logger.exception("Error al consultar planes sin asesor")
        return jsonify({"error":"No fue posible consultar los planes pendientes de reasignación."}),500
    finally:
        if cursor: PlanesController._cerrar_cursor(cursor)


@app.route("/api/admin/planes/<int:id_plan>/reasignar", methods=["PATCH"])
def reasignar_plan_admin(id_plan):
    admin, error = requiere_rol("administrador")
    if error: return error
    datos=request.get_json(silent=True) or {}
    try: id_nuevo=int(datos.get("id_asesor_nuevo"))
    except (TypeError,ValueError): return jsonify({"error":"Selecciona un asesor válido."}),400
    cursor=None
    try:
        cursor=PlanesController.obtener_cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_asignaciones_planes (
                id_historial SERIAL PRIMARY KEY,
                id_plan INTEGER NOT NULL REFERENCES planes(id_plan) ON DELETE CASCADE,
                id_asesor_anterior INTEGER REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
                id_asesor_nuevo INTEGER NOT NULL REFERENCES usuarios(id_usuario),
                id_admin INTEGER REFERENCES usuarios(id_usuario),
                fecha_asignacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("SELECT id_asesor FROM planes WHERE id_plan=%s FOR UPDATE;",(id_plan,))
        fila=cursor.fetchone()
        if not fila:
            cursor.connection.rollback(); return jsonify({"error":"Plan no encontrado."}),404
        id_anterior=fila[0]
        cursor.execute("SELECT 1 FROM usuarios WHERE id_usuario=%s AND rol='asesor' AND COALESCE(activo,TRUE)=TRUE AND COALESCE(eliminado,FALSE)=FALSE;",(id_nuevo,))
        if not cursor.fetchone():
            cursor.connection.rollback(); return jsonify({"error":"El asesor seleccionado no existe o no está activo."}),400
        cursor.execute("SELECT 1 FROM usuarios WHERE id_usuario=%s AND COALESCE(eliminado,FALSE)=TRUE;",(id_anterior,))
        anterior_eliminado = id_anterior is None or cursor.fetchone() is not None
        if not anterior_eliminado:
            cursor.connection.rollback(); return jsonify({"error":"Este plan todavía pertenece a un asesor activo. Solo se reasignan planes de asesores eliminados o sin asignar."}),409
        if id_anterior == id_nuevo:
            cursor.connection.rollback(); return jsonify({"error":"Selecciona un asesor diferente."}),400
        cursor.execute("UPDATE planes SET id_asesor=%s WHERE id_plan=%s;",(id_nuevo,id_plan))
        cursor.execute("INSERT INTO historial_asignaciones_planes (id_plan,id_asesor_anterior,id_asesor_nuevo,id_admin) VALUES (%s,%s,%s,%s);",(id_plan,id_anterior,id_nuevo,admin["id_usuario"]))
        cursor.connection.commit()
        return jsonify({"mensaje":"Plan reasignado correctamente. El nuevo asesor ya puede gestionarlo."}),200
    except Exception:
        if cursor: cursor.connection.rollback()
        app.logger.exception("Error al reasignar plan")
        return jsonify({"error":"No fue posible reasignar el plan."}),500
    finally:
        if cursor: PlanesController._cerrar_cursor(cursor)


@app.route("/api/admin/reportes", methods=["GET"])
def reportes_admin():
    _, error = requiere_rol("administrador")
    if error: return error
    cursor = None
    try:
        cursor = PlanesController.obtener_cursor()
        cursor.execute("""
            SELECT
              COUNT(*) FILTER (WHERE estado='Publicado'),
              COUNT(*) FILTER (WHERE estado='Pendiente'),
              COUNT(*) FILTER (WHERE estado='Borrador'),
              (SELECT COUNT(*) FROM usuarios WHERE rol='asesor' AND COALESCE(eliminado,FALSE)=FALSE),
              (SELECT COUNT(*) FROM usuarios WHERE rol='cliente' AND COALESCE(eliminado,FALSE)=FALSE),
              (SELECT COUNT(*) FROM solicitudes_contacto),
              COUNT(*) FILTER (WHERE estado='Publicado' AND COALESCE(descuento_porcentaje,0)>0 AND oferta_fecha_inicio<=CURRENT_DATE AND oferta_fecha_fin>=CURRENT_DATE)
            FROM planes;
        """)
        r = cursor.fetchone()
        return jsonify({"planes_publicados":r[0],"planes_pendientes":r[1],"planes_borrador":r[2],"asesores":r[3],"clientes":r[4],"solicitudes":r[5],"ofertas_vigentes":r[6]}), 200
    except Exception:
        app.logger.exception("Error al generar reportes administrativos")
        return jsonify({"error": "No fue posible generar los reportes."}), 500
    finally:
        if cursor is not None: PlanesController._cerrar_cursor(cursor)


@app.route("/api/asesor/reportes", methods=["GET"])
def reportes_asesor():
    usuario, error = requiere_rol("asesor")
    if error: return error
    cursor = None
    try:
        cursor = PlanesController.obtener_cursor()
        cursor.execute("""
            SELECT COUNT(*), COUNT(*) FILTER (WHERE estado='Publicado'),
                   COUNT(*) FILTER (WHERE estado='Pendiente'), COUNT(*) FILTER (WHERE estado='Borrador'),
                   (SELECT COUNT(*) FROM solicitudes_contacto s JOIN planes p ON p.id_plan=s.id_plan WHERE p.id_asesor=%s),
                   (SELECT COUNT(*) FROM solicitudes_contacto s JOIN planes p ON p.id_plan=s.id_plan WHERE p.id_asesor=%s AND s.estado='Nueva')
            FROM planes WHERE id_asesor=%s;
        """, (usuario["id_usuario"], usuario["id_usuario"], usuario["id_usuario"]))
        r=cursor.fetchone()
        return jsonify({"planes_total":r[0],"publicados":r[1],"pendientes":r[2],"borradores":r[3],"solicitudes":r[4],"solicitudes_nuevas":r[5]}),200
    except Exception:
        app.logger.exception("Error al generar reportes del asesor")
        return jsonify({"error":"No fue posible generar tus reportes."}),500
    finally:
        if cursor is not None: PlanesController._cerrar_cursor(cursor)


@app.route("/api/asesor/solicitudes/<int:id_solicitud>/estado", methods=["PATCH"])
def actualizar_estado_solicitud_asesor(id_solicitud):
    usuario, error = requiere_rol("asesor")
    if error: return error
    datos=request.get_json(silent=True) or {}
    estado=datos.get("estado")
    if estado not in {"Nueva", "En gestión", "Atendida"}:
        return jsonify({"error":"Estado de solicitud no válido."}),400
    cursor=None
    try:
        cursor=PlanesController.obtener_cursor()
        cursor.execute("""UPDATE solicitudes_contacto s
                         SET estado=%s, fecha_actualizacion=CURRENT_TIMESTAMP,
                             actualizado_por=%s
                         FROM planes p
                         WHERE s.id_solicitud=%s AND p.id_plan=s.id_plan
                           AND p.id_asesor=%s AND COALESCE(s.archivada,FALSE)=FALSE AND COALESCE(s.eliminada,FALSE)=FALSE
                         RETURNING s.id_solicitud;""",
                       (estado, usuario["id_usuario"], id_solicitud, usuario["id_usuario"]))
        if not cursor.fetchone():
            cursor.connection.rollback(); return jsonify({"error":"No se encontró la solicitud activa."}),404
        cursor.connection.commit(); return jsonify({"mensaje":"Estado actualizado."}),200
    except Exception:
        if cursor: cursor.connection.rollback()
        app.logger.exception("Error actualizando solicitud")
        return jsonify({"error":"No fue posible actualizar la solicitud."}),500
    finally:
        if cursor: PlanesController._cerrar_cursor(cursor)


@app.route("/api/asesor/solicitudes/<int:id_solicitud>/archivar", methods=["PATCH"])
def archivar_solicitud_asesor(id_solicitud):
    usuario, error = requiere_rol("asesor")
    if error: return error
    return _archivar_solicitud(id_solicitud, usuario)


def _archivar_solicitud(id_solicitud, usuario):
    cursor=None
    try:
        cursor=PlanesController.obtener_cursor()
        filtro_asesor = "AND p.id_asesor=%s" if usuario.get("rol") == "asesor" else ""
        params=[usuario["id_usuario"], id_solicitud]
        if filtro_asesor: params.append(usuario["id_usuario"])
        cursor.execute(f"""UPDATE solicitudes_contacto s
            SET archivada=TRUE, fecha_archivado=CURRENT_TIMESTAMP,
                archivada_por=%s, fecha_actualizacion=CURRENT_TIMESTAMP,
                actualizado_por=%s
            FROM planes p
            WHERE s.id_solicitud=%s AND p.id_plan=s.id_plan
              AND COALESCE(s.archivada,FALSE)=FALSE AND COALESCE(s.eliminada,FALSE)=FALSE {filtro_asesor}
            RETURNING s.id_solicitud;""", (usuario["id_usuario"], usuario["id_usuario"], id_solicitud, *([usuario["id_usuario"]] if filtro_asesor else [])))
        if not cursor.fetchone():
            cursor.connection.rollback(); return jsonify({"error":"No se encontró la solicitud activa o no tienes permisos."}),404
        cursor.connection.commit(); return jsonify({"mensaje":"Solicitud archivada."}),200
    except Exception:
        if cursor: cursor.connection.rollback()
        app.logger.exception("Error archivando solicitud")
        return jsonify({"error":"No fue posible archivar la solicitud."}),500
    finally:
        if cursor: PlanesController._cerrar_cursor(cursor)


@app.route("/api/admin/solicitudes/<int:id_solicitud>/estado", methods=["PATCH"])
def actualizar_estado_solicitud_admin(id_solicitud):
    usuario, error=requiere_rol("administrador")
    if error: return error
    estado=(request.get_json(silent=True) or {}).get("estado")
    if estado not in {"Nueva", "En gestión", "Atendida"}:
        return jsonify({"error":"Estado de solicitud no válido."}),400
    cursor=None
    try:
        cursor=PlanesController.obtener_cursor()
        cursor.execute("""UPDATE solicitudes_contacto SET estado=%s,
            fecha_actualizacion=CURRENT_TIMESTAMP, actualizado_por=%s
            WHERE id_solicitud=%s AND COALESCE(archivada,FALSE)=FALSE AND COALESCE(eliminada,FALSE)=FALSE
            RETURNING id_solicitud;""",(estado,usuario["id_usuario"],id_solicitud))
        if not cursor.fetchone(): cursor.connection.rollback(); return jsonify({"error":"No se encontró la solicitud activa."}),404
        cursor.connection.commit(); return jsonify({"mensaje":"Estado actualizado."}),200
    except Exception:
        if cursor: cursor.connection.rollback()
        app.logger.exception("Error actualizando solicitud administrativa")
        return jsonify({"error":"No fue posible actualizar la solicitud."}),500
    finally:
        if cursor: PlanesController._cerrar_cursor(cursor)


@app.route("/api/admin/solicitudes/<int:id_solicitud>/archivar", methods=["PATCH"])
def archivar_solicitud_admin(id_solicitud):
    usuario, error=requiere_rol("administrador")
    if error: return error
    return _archivar_solicitud(id_solicitud, usuario)


def _desarchivar_solicitud(id_solicitud, usuario):
    cursor = None
    try:
        cursor = PlanesController.obtener_cursor()
        es_asesor = usuario.get("rol") == "asesor"
        filtro_asesor = "AND p.id_asesor=%s" if es_asesor else ""
        params = [usuario["id_usuario"], id_solicitud]
        if es_asesor:
            params.append(usuario["id_usuario"])
        cursor.execute(f"""
            UPDATE solicitudes_contacto s
               SET archivada=FALSE, fecha_archivado=NULL,
                   archivada_por=NULL, fecha_actualizacion=CURRENT_TIMESTAMP,
                   actualizado_por=%s
              FROM planes p
             WHERE s.id_solicitud=%s AND p.id_plan=s.id_plan
               AND COALESCE(s.archivada,FALSE)=TRUE
               AND COALESCE(s.eliminada,FALSE)=FALSE {filtro_asesor}
         RETURNING s.id_solicitud;
        """, tuple(params))
        if not cursor.fetchone():
            cursor.connection.rollback()
            return jsonify({"error":"No se encontró la solicitud archivada o no tienes permisos."}),404
        cursor.connection.commit()
        return jsonify({"mensaje":"Solicitud restaurada a la bandeja principal."}),200
    except Exception:
        if cursor: cursor.connection.rollback()
        app.logger.exception("Error desarchivando solicitud")
        return jsonify({"error":"No fue posible restaurar la solicitud."}),500
    finally:
        if cursor: PlanesController._cerrar_cursor(cursor)


@app.route("/api/asesor/solicitudes/<int:id_solicitud>/desarchivar", methods=["PATCH"])
def desarchivar_solicitud_asesor(id_solicitud):
    usuario, error = requiere_rol("asesor")
    if error: return error
    return _desarchivar_solicitud(id_solicitud, usuario)


@app.route("/api/admin/solicitudes/<int:id_solicitud>/desarchivar", methods=["PATCH"])
def desarchivar_solicitud_admin(id_solicitud):
    usuario, error = requiere_rol("administrador")
    if error: return error
    return _desarchivar_solicitud(id_solicitud, usuario)


def _eliminar_solicitud_definitivamente(id_solicitud, usuario):
    """Eliminación física de una solicitud; solo el rol autorizado puede ejecutarla."""
    cursor = None
    try:
        cursor = PlanesController.obtener_cursor()
        es_asesor = usuario.get("rol") == "asesor"
        filtro_asesor = "AND p.id_asesor=%s" if es_asesor else ""
        params = [id_solicitud]
        if es_asesor:
            params.append(usuario["id_usuario"])
        cursor.execute(f"""
            DELETE FROM solicitudes_contacto s
             USING planes p
             WHERE s.id_solicitud=%s AND p.id_plan=s.id_plan
               AND COALESCE(s.eliminada,FALSE)=FALSE {filtro_asesor}
         RETURNING s.id_solicitud;
        """, tuple(params))
        if not cursor.fetchone():
            cursor.connection.rollback()
            return jsonify({"error":"No se encontró la solicitud o no tienes permisos."}),404
        cursor.connection.commit()
        return jsonify({"mensaje":"Solicitud eliminada definitivamente."}),200
    except Exception:
        if cursor: cursor.connection.rollback()
        app.logger.exception("Error eliminando definitivamente solicitud")
        return jsonify({"error":"No fue posible eliminar la solicitud."}),500
    finally:
        if cursor: PlanesController._cerrar_cursor(cursor)


@app.route("/api/asesor/solicitudes/<int:id_solicitud>", methods=["DELETE"])
def eliminar_solicitud_asesor(id_solicitud):
    usuario, error = requiere_rol("asesor")
    if error: return error
    return _eliminar_solicitud_definitivamente(id_solicitud, usuario)


@app.route("/api/admin/solicitudes/<int:id_solicitud>", methods=["DELETE"])
def eliminar_solicitud_admin(id_solicitud):
    usuario, error = requiere_rol("administrador")
    if error: return error
    return _eliminar_solicitud_definitivamente(id_solicitud, usuario)


@app.route("/api/asesor/solicitudes/archivadas", methods=["GET"])
def solicitudes_asesor_archivadas():
    usuario, error=requiere_rol("asesor")
    if error: return error
    cursor=None
    try:
        cursor=PlanesController.obtener_cursor()
        cursor.execute("""SELECT s.id_solicitud,s.nombre,s.correo,s.telefono,s.mensaje,s.estado,s.fecha_creacion,
            s.fecha_archivado,p.nombre FROM solicitudes_contacto s
            JOIN planes p ON p.id_plan=s.id_plan
            WHERE p.id_asesor=%s AND COALESCE(s.archivada,FALSE)=TRUE AND COALESCE(s.eliminada,FALSE)=FALSE
            ORDER BY s.fecha_archivado DESC;""",(usuario["id_usuario"],))
        return jsonify([{"id_solicitud":r[0],"nombre":r[1],"correo":r[2],"telefono":r[3],"mensaje":r[4] or "","estado":r[5],"fecha_creacion":r[6].isoformat(),"fecha_archivado":r[7].isoformat() if r[7] else None,"nombre_plan":r[8]} for r in cursor.fetchall()]),200
    except Exception:
        app.logger.exception("Error consultando solicitudes archivadas del asesor")
        return jsonify({"error":"No fue posible consultar las solicitudes archivadas."}),500
    finally:
        if cursor: PlanesController._cerrar_cursor(cursor)


@app.route("/api/admin/solicitudes", methods=["GET"])
def solicitudes_admin():
    _, error=requiere_rol("administrador")
    if error: return error
    cursor=None
    try:
        cursor=PlanesController.obtener_cursor()
        cursor.execute("""SELECT s.id_solicitud,s.nombre,s.correo,s.telefono,s.mensaje,s.estado,s.fecha_creacion,
                         p.nombre,u.nombre,s.fecha_actualizacion,ua.nombre
                         FROM solicitudes_contacto s JOIN planes p ON p.id_plan=s.id_plan
                         JOIN usuarios u ON u.id_usuario=p.id_asesor
                         LEFT JOIN usuarios ua ON ua.id_usuario=s.actualizado_por
                         WHERE COALESCE(s.archivada,FALSE)=FALSE AND COALESCE(s.eliminada,FALSE)=FALSE
                         ORDER BY s.fecha_creacion DESC;""")
        return jsonify([{"id_solicitud":r[0],"nombre":r[1],"correo":r[2],"telefono":r[3],"mensaje":r[4] or "","estado":r[5],"fecha_creacion":r[6].isoformat(),"plan":r[7],"asesor":r[8],"fecha_actualizacion":r[9].isoformat() if r[9] else None,"actualizado_por":r[10]} for r in cursor.fetchall()]),200
    except Exception:
        app.logger.exception("Error consultando solicitudes administrativas")
        return jsonify({"error":"No fue posible consultar las solicitudes."}),500
    finally:
        if cursor: PlanesController._cerrar_cursor(cursor)


@app.route("/api/admin/solicitudes/archivadas", methods=["GET"])
def solicitudes_admin_archivadas():
    _, error=requiere_rol("administrador")
    if error: return error
    cursor=None
    try:
        cursor=PlanesController.obtener_cursor()
        cursor.execute("""SELECT s.id_solicitud,s.nombre,s.correo,s.telefono,s.mensaje,s.estado,
            s.fecha_creacion,s.fecha_archivado,p.nombre,u.nombre
            FROM solicitudes_contacto s JOIN planes p ON p.id_plan=s.id_plan
            JOIN usuarios u ON u.id_usuario=p.id_asesor
            WHERE COALESCE(s.archivada,FALSE)=TRUE AND COALESCE(s.eliminada,FALSE)=FALSE ORDER BY s.fecha_archivado DESC;""")
        return jsonify([{"id_solicitud":r[0],"nombre":r[1],"correo":r[2],"telefono":r[3],"mensaje":r[4] or "","estado":r[5],"fecha_creacion":r[6].isoformat(),"fecha_archivado":r[7].isoformat() if r[7] else None,"plan":r[8],"asesor":r[9]} for r in cursor.fetchall()]),200
    except Exception:
        app.logger.exception("Error consultando solicitudes archivadas")
        return jsonify({"error":"No fue posible consultar las solicitudes archivadas."}),500
    finally:
        if cursor: PlanesController._cerrar_cursor(cursor)


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
