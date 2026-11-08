
import unittest
import sys

sys.path.append(".")
sys.path.append("src")

from model.logic import (
    DatosViajero,
    Itinerario,
    PlanTuristico,
    RevisionPlan,
    GeneradorItinerarioIA
)


class TestLogicModulo1(unittest.TestCase):

    def test_plan_creacion_y_revision_exitosa(self):
        datos = DatosViajero(
            duracion_dias=3,
            presupuesto=1500000,
            tipo_viajero="Pareja",
            intereses="Playa"
        )

        itinerario = Itinerario(generado_por_ia=True)
        itinerario.agregar_dia(1, "Llegada y check-in en el hotel.")
        itinerario.agregar_dia(2, "Tour por la bahía y snorkel.")
        itinerario.agregar_dia(3, "Compras libres y retorno.")

        plan = PlanTuristico(
            id_plan=1,
            nombre="San Andrés 3 días",
            destino="San Andrés",
            datos_viajero=datos,
            id_asesor=1,
            costo_estimado=1500000,
            estado="Borrador",
            itinerario=itinerario,
            incluye="Alojamiento, transporte y tour por la bahía.",
            no_incluye="Alimentación y gastos personales."
        )

        nuevo_estado = plan.enviar_a_revision()

        self.assertEqual(nuevo_estado, "Pendiente")
        self.assertEqual(plan.estado, "Pendiente")
        self.assertTrue(plan.itinerario.esta_completo(3))

    def test_datos_viajero_invalidos(self):
        with self.assertRaises(ValueError):
            DatosViajero(
                duracion_dias=0,
                presupuesto=1000000,
                tipo_viajero="Familia",
                intereses="Cultura"
            )

        with self.assertRaises(ValueError):
            DatosViajero(
                duracion_dias=5,
                presupuesto=-500,
                tipo_viajero="Familia",
                intereses="Cultura"
            )

    def test_enviar_revision_itinerario_incompleto(self):
        datos = DatosViajero(
            duracion_dias=5,
            presupuesto=2000000,
            tipo_viajero="Amigos",
            intereses="Fiesta"
        )

        itinerario = Itinerario(generado_por_ia=True)
        itinerario.agregar_dia(1, "Llegada al destino.")
        itinerario.agregar_dia(2, "Recorrido por la ciudad.")

        plan = PlanTuristico(
            id_plan=2,
            nombre="París Express",
            destino="París",
            datos_viajero=datos,
            id_asesor=1,
            costo_estimado=2000000,
            estado="Borrador",
            itinerario=itinerario,
            incluye="Alojamiento y recorridos turísticos.",
            no_incluye="Vuelos y gastos personales."
        )

        with self.assertRaises(ValueError):
            plan.enviar_a_revision()


    def test_parsear_itinerario_tres_dias(self):
        respuesta_ia = """NOMBRE: Escapada entre montañas y colores
DESCRIPCION: Descubre paisajes, cultura y aventura en una experiencia especial por el destino.
Día 1: Llegada, recorrido por el pueblo y visita a sus principales atractivos.
Día 2: Caminata por senderos naturales y actividades junto al embalse.
Día 3: Desayuno, visita a talleres artesanales y regreso.
"""
        itinerario = GeneradorItinerarioIA._parsear(respuesta_ia, 3)
        self.assertTrue(itinerario.esta_completo(3))
        self.assertEqual([dia.numero_dia for dia in itinerario.dias], [1, 2, 3])

    def test_parsear_itinerario_tres_dias_con_formato_markdown(self):
        respuesta_ia = """**Día 1:** Llegada y recorrido por el destino.
### Día 2: Visita a atractivos naturales.
- Día 3 - Desayuno y regreso.
"""
        itinerario = GeneradorItinerarioIA._parsear(respuesta_ia, 3)
        self.assertTrue(itinerario.esta_completo(3))

    def test_motivo_rechazo_admin_invalido(self):
        with self.assertRaises(ValueError):
            RevisionPlan(
                id_revision=1,
                id_plan=10,
                id_admin=2,
                decision="Rechazado",
                motivo="Corto"
            )


if __name__ == "__main__":
    unittest.main()
