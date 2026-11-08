import os
import re
import sys

# Buscar archivos secretos de Render
sys.path.insert(0, "/etc/secrets")

from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# CLASE USUARIO
# ============================================================

class Usuario:
    def __init__(
        self,
        id_usuario,
        nombre,
        correo,
        contrasena_cifrada,
        rol
    ):
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.correo = correo
        self.contrasena_cifrada = contrasena_cifrada
        self.rol = rol

    @staticmethod
    def cifrar_contrasena(contrasena_plana):
        return generate_password_hash(contrasena_plana)

    def verificar_contrasena(self, contrasena_plana):
        if not self.contrasena_cifrada or not contrasena_plana:
            return False

        return check_password_hash(
            self.contrasena_cifrada,
            contrasena_plana
        )

    def to_dict(self):
        return {
            "id_usuario": self.id_usuario,
            "nombre": self.nombre,
            "correo": self.correo,
            "rol": self.rol
        }


# ============================================================
# CLASE DATOS VIAJERO
# ============================================================

class DatosViajero:
    def __init__(
        self,
        duracion_dias,
        presupuesto,
        tipo_viajero,
        intereses
    ):
        try:
            duracion = int(duracion_dias)
            presupuesto_val = float(presupuesto)
        except (TypeError, ValueError):
            raise ValueError(
                "La duración y el presupuesto deben ser valores numéricos."
            )

        if duracion <= 0:
            raise ValueError("La duración debe ser mayor a 0 días.")

        if presupuesto_val <= 0:
            raise ValueError("El presupuesto debe ser mayor a $0 COP.")

        if not tipo_viajero or not str(tipo_viajero).strip():
            raise ValueError("El tipo de viajero es obligatorio.")

        if not intereses or not str(intereses).strip():
            raise ValueError("Los intereses son obligatorios.")

        self.duracion_dias = duracion
        self.presupuesto = presupuesto_val
        self.tipo_viajero = str(tipo_viajero).strip()
        self.intereses = str(intereses).strip()

    def to_dict(self):
        return {
            "duracion_dias": self.duracion_dias,
            "presupuesto": self.presupuesto,
            "tipo_viajero": self.tipo_viajero,
            "intereses": self.intereses
        }


# ============================================================
# CLASE DIA ITINERARIO
# ============================================================

class DiaItinerario:
    def __init__(self, numero_dia, descripcion_resumen):
        try:
            numero = int(numero_dia)
        except (TypeError, ValueError):
            raise ValueError("El número de día debe ser un entero.")

        if numero <= 0:
            raise ValueError("El número de día debe ser positivo.")

        if (
            not descripcion_resumen
            or not str(descripcion_resumen).strip()
        ):
            raise ValueError(
                "La descripción del día no puede estar vacía."
            )

        self.numero_dia = numero
        self.descripcion_resumen = str(
            descripcion_resumen
        ).strip()

    def to_dict(self):
        return {
            "numero_dia": self.numero_dia,
            "descripcion_resumen": self.descripcion_resumen
        }


# ============================================================
# CLASE ITINERARIO
# ============================================================

class Itinerario:
    def __init__(self, generado_por_ia=True, dias=None):
        self.generado_por_ia = bool(generado_por_ia)
        self.dias = list(dias) if dias is not None else []

    def agregar_dia(self, numero_dia, descripcion):
        dia = DiaItinerario(numero_dia, descripcion)

        if any(
            existente.numero_dia == dia.numero_dia
            for existente in self.dias
        ):
            raise ValueError(
                f"El día {dia.numero_dia} ya existe en el itinerario."
            )

        self.dias.append(dia)
        self.dias.sort(key=lambda elemento: elemento.numero_dia)

    def esta_completo(self, duracion_esperada):
        if len(self.dias) != duracion_esperada:
            return False

        numeros = sorted(dia.numero_dia for dia in self.dias)

        return numeros == list(
            range(1, duracion_esperada + 1)
        )

    def to_dict(self):
        return {
            "generado_por_ia": self.generado_por_ia,
            "dias": [
                dia.to_dict()
                for dia in sorted(
                    self.dias,
                    key=lambda elemento: elemento.numero_dia
                )
            ]
        }


# ============================================================
# CLASE PLAN TURISTICO
# ============================================================

class PlanTuristico:
    def __init__(
        self,
        id_plan,
        nombre,
        destino,
        datos_viajero: DatosViajero,
        id_asesor,
        costo_estimado=0.0,
        estado="Borrador",
        itinerario: Itinerario = None,
        imagen_url=None,
        incluye="",
        no_incluye="",
        imagenes=None,
        decision_revision=None,
        motivo_rechazo=""
    ):
        self.id_plan = id_plan
        self.nombre = nombre
        self.destino = destino
        self.datos_viajero = datos_viajero
        self.id_asesor = id_asesor
        self.costo_estimado = float(costo_estimado or 0)
        self.estado = estado
        self.itinerario = itinerario
        self.imagen_url = imagen_url
        self.incluye = incluye or ""
        self.no_incluye = no_incluye or ""
        self.imagenes = imagenes or []
        self.decision_revision = decision_revision
        self.motivo_rechazo = motivo_rechazo or ""

    def enviar_a_revision(self):
        if not self.itinerario or not self.itinerario.esta_completo(
            self.datos_viajero.duracion_dias
        ):
            raise ValueError("El itinerario está incompleto.")

        if not self.incluye.strip():
            raise ValueError("Debes especificar qué incluye el plan.")

        if not self.no_incluye.strip():
            raise ValueError("Debes especificar qué no incluye el plan.")

        self.estado = "Pendiente"
        return self.estado

    def to_dict(self):
        return {
            "id_plan": self.id_plan,
            "nombre": self.nombre,
            "destino": self.destino,
            "datos_viajero": self.datos_viajero.to_dict(),
            "id_asesor": self.id_asesor,
            "costo_estimado": self.costo_estimado,
            "estado": self.estado,
            "imagen_url": self.imagen_url,
            "imagenes": self.imagenes,
            "decision_revision": self.decision_revision,
            "motivo_rechazo": self.motivo_rechazo,
            "incluye": self.incluye,
            "no_incluye": self.no_incluye,
            "itinerario": (
                self.itinerario.to_dict()
                if self.itinerario
                else None
            )
        }


# ============================================================
# CLASE GENERADOR DE ITINERARIOS CON IA
# ============================================================

class GeneradorItinerarioIA:
    MODELO_GROQ = "openai/gpt-oss-120b"
    TIEMPO_LIMITE = 30.0

    @staticmethod
    def generar(
        destino_nombre,
        datos_viajero: DatosViajero,
        pais,
        continente=None
    ):
        # 1. Obtener la clave de Groq.
        groq_key = None

        try:
            import secret_config
            groq_key = getattr(
                secret_config,
                "GROQ_API_KEY",
                None
            )
        except ImportError:
            pass

        if not groq_key:
            groq_key = os.getenv("GROQ_API_KEY")

        if not groq_key or not groq_key.strip():
            raise RuntimeError(
                "La integración con la IA no está configurada. "
                "Verifica GROQ_API_KEY."
            )

        groq_key = groq_key.strip()

        # 2. Construir las instrucciones para la IA.
        prompt = f"""
Actúa como un agente de viajes profesional.

Genera un itinerario turístico para {destino_nombre}, ubicado en {pais}.

Ubicación geográfica obligatoria:
- Destino indicado: {destino_nombre}
- País: {pais}
- Continente: {continente or "No especificado"}

Debes interpretar el destino exclusivamente dentro del país indicado.
Si existen ciudades, regiones o lugares con el mismo nombre en otros países,
ignóralos y utiliza únicamente el lugar que corresponda a {destino_nombre}
en {pais}. No mezcles atractivos, ciudades, moneda, gastronomía ni
referencias geográficas de otros países.

Datos del viajero:
- Destino: {destino_nombre}
- País: {pais}
- Duración: exactamente {datos_viajero.duracion_dias} días.
- Presupuesto total: ${datos_viajero.presupuesto:,.0f} COP.
- Tipo de viajero: {datos_viajero.tipo_viajero}.
- Intereses: {datos_viajero.intereses}.

Instrucciones:
1. Genera exactamente {datos_viajero.duracion_dias} días.
2. Incluye actividades relevantes y diferentes para cada día.
3. Usa lugares reales del destino dentro del país indicado; no inventes atracciones.
4. No incluyas lugares de otros países aunque tengan el mismo nombre.
5. Considera el presupuesto, el tipo de viajero y sus intereses.
6. Organiza las actividades de forma lógica y evita traslados imposibles.
7. No agregues introducciones ni conclusiones.

Formato obligatorio:
Día 1: Lugar o zona - Descripción de las actividades.
Día 2: Lugar o zona - Descripción de las actividades.

Continúa hasta completar exactamente
{datos_viajero.duracion_dias} días.

Devuelve únicamente las líneas del itinerario.
"""

        # 3. Verificar que el paquete necesario esté instalado.
        try:
            from openai import OpenAI, APITimeoutError
        except ImportError as error:
            raise RuntimeError(
                "Falta instalar la dependencia openai. "
                "Ejecuta: pip install openai"
            ) from error

        # 4. Consultar a Groq con un límite de tiempo y sin reintentos
        # automáticos del SDK.
        try:
            client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key,
                timeout=GeneradorItinerarioIA.TIEMPO_LIMITE,
                max_retries=0
            )

            respuesta = client.chat.completions.create(
                model=GeneradorItinerarioIA.MODELO_GROQ,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7
            )

        except APITimeoutError as error:
            raise TimeoutError(
                "La IA tardó más de lo esperado (30 segundos). "
                "Puedes intentarlo nuevamente."
            ) from error

        except Exception as error:
            mensaje = str(error).lower()

            if (
                "timeout" in mensaje
                or "timed out" in mensaje
                or "deadline exceeded" in mensaje
            ):
                raise TimeoutError(
                    "La IA tardó más de lo esperado (30 segundos). "
                    "Puedes intentarlo nuevamente."
                ) from error

            raise RuntimeError(
                "No fue posible obtener una respuesta de la IA. "
                "Inténtalo nuevamente más tarde."
            ) from error

        # 5. Verificar que Groq haya devuelto contenido.
        try:
            texto = respuesta.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as error:
            raise RuntimeError(
                "La respuesta de la IA no tiene el formato esperado."
            ) from error

        if not texto or not texto.strip():
            raise RuntimeError(
                "La IA devolvió una respuesta vacía. "
                "Puedes intentarlo nuevamente."
            )

        # 6. Interpretar y validar el itinerario.
        try:
            return GeneradorItinerarioIA._parsear(
                texto,
                datos_viajero.duracion_dias
            )
        except ValueError as error:
            raise RuntimeError(
                "La IA no generó un itinerario válido con todos los días "
                "solicitados. Inténtalo nuevamente."
            ) from error

    @staticmethod
    def _parsear(texto, duracion_esperada):
        itinerario = Itinerario(generado_por_ia=True)

        for linea in texto.strip().splitlines():
            coincidencia = re.match(
                r"^\s*(?:[-*]\s*)?\**Día\s+(\d+)\**\s*:\s*(.+)$",
                linea,
                re.IGNORECASE
            )

            if not coincidencia:
                continue

            numero_dia = int(coincidencia.group(1))
            descripcion = coincidencia.group(2).strip()

            if not 1 <= numero_dia <= duracion_esperada:
                raise ValueError(
                    f"La IA generó un número de día inválido: "
                    f"{numero_dia}."
                )

            if any(
                dia.numero_dia == numero_dia
                for dia in itinerario.dias
            ):
                raise ValueError(
                    f"La IA repitió el día {numero_dia}."
                )

            itinerario.agregar_dia(numero_dia, descripcion)

        itinerario.dias.sort(key=lambda dia: dia.numero_dia)

        if len(itinerario.dias) != duracion_esperada:
            raise ValueError(
                f"La IA generó {len(itinerario.dias)} días, "
                f"pero se esperaban {duracion_esperada}."
            )

        for posicion, dia in enumerate(itinerario.dias, start=1):
            if dia.numero_dia != posicion:
                raise ValueError(
                    "El itinerario tiene días desordenados o faltantes."
                )

        return itinerario


# ============================================================
# CLASE REVISION DEL PLAN
# ============================================================

class RevisionPlan:
    def __init__(
        self,
        id_revision,
        id_plan,
        id_admin,
        decision,
        motivo=""
    ):
        if decision not in {"Aprobado", "Rechazado"}:
            raise ValueError(
                "La decisión debe ser 'Aprobado' o 'Rechazado'."
            )

        motivo = str(motivo or "").strip()

        if (
            decision == "Rechazado"
            and motivo
            and len(motivo) < 10
        ):
            raise ValueError(
                "Si agregas un motivo de rechazo, debe contener "
                "al menos 10 caracteres."
            )

        self.id_revision = id_revision
        self.id_plan = id_plan
        self.id_admin = id_admin
        self.decision = decision
        self.motivo = motivo

    def to_dict(self):
        return {
            "id_revision": self.id_revision,
            "id_plan": self.id_plan,
            "id_admin": self.id_admin,
            "decision": self.decision,
            "motivo": self.motivo
        }
