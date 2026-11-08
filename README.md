# RUMBALIA – Plataforma Inteligente de Planes Turísticos

Aplicación web para la creación, consulta y administración de planes turísticos personalizados mediante inteligencia artificial. El sistema permite conectar a clientes, asesores turísticos y administradores a través de una plataforma desarrollada con Python, Flask, PostgreSQL, HTML, CSS y JavaScript.

## Autores

- Francisco Gómez Gutiérrez
- Isabella Quintero Gutiérrez
- Nelson David Jiménez Ruiz

---

## 1. Descripción del proyecto

Rumbalia es una plataforma web orientada a facilitar la creación y consulta de experiencias turísticas personalizadas. Permite que los asesores diseñen planes de viaje con ayuda de inteligencia artificial, que los administradores supervisen y gestionen su publicación y que los clientes exploren los planes disponibles y soliciten información.

La aplicación contempla tres roles principales:

- **Cliente:** explora los planes turísticos publicados, consulta sus características e itinerarios y puede enviar solicitudes de contacto sin necesidad de crear una cuenta.
- **Asesor:** crea planes turísticos, genera itinerarios mediante inteligencia artificial, edita la información, administra borradores, envía planes a revisión y gestiona las solicitudes de los clientes.
- **Administrador:** supervisa los planes enviados a revisión, aprueba o rechaza propuestas, consulta estadísticas, administra las cuentas de usuario y gestiona las solicitudes de contacto.

## 2. Funcionalidades del MVP

### 2.1. Funcionalidades generales

- Inicio de sesión con autenticación y control de acceso según el rol.
- Registro público de clientes.
- Gestión de sesiones y cierre de sesión.
- Protección de rutas según los permisos de cada usuario.
- Interfaz web adaptable a diferentes tamaños de pantalla.

### 2.2. Funcionalidades del cliente

- Consulta de planes turísticos publicados.
- Exploración de destinos por continente.
- Visualización de la ficha descriptiva de cada plan.
- Consulta de itinerarios, duración, presupuesto, destino, servicios incluidos y servicios no incluidos.
- Búsqueda de planes por destino, país, intereses, presupuesto y duración.
- Exploración de experiencias según intereses turísticos.
- Consulta de ofertas disponibles.
- Visualización de la información institucional de Rumbalia.
- Envío de solicitudes de contacto desde los planes publicados, sin necesidad de iniciar sesión.
- Confirmación del envío de la solicitud.

### 2.3. Funcionalidades del asesor

- Creación de planes turísticos.
- Generación de itinerarios mediante inteligencia artificial.
- Edición de la información comercial del plan.
- Edición de los días y descripciones del itinerario.
- Guardado y consulta de borradores.
- Envío de planes para revisión administrativa.
- Regreso de planes rechazados al estado de borrador.
- Actualización de la imagen principal de un plan.
- Administración de la galería de imágenes.
- Eliminación de planes en estado Borrador o Publicado.
- Consulta de reportes propios.
- Consulta de solicitudes recibidas para sus planes.
- Actualización del estado de las solicitudes.
- Archivado, desarchivado y eliminación definitiva de solicitudes.

### 2.4. Funcionalidades del administrador

- Consulta de planes pendientes de revisión.
- Visualización del detalle de los planes enviados.
- Aprobación o rechazo de planes.
- Registro del motivo de rechazo.
- Consulta de estadísticas generales.
- Administración de usuarios.
- Creación de cuentas de asesores y administradores.
- Activación y desactivación de cuentas.
- Eliminación lógica y anonimización de cuentas de usuario, conservando la integridad de los registros relacionados.
- Consulta de reportes generales.
- Consulta y gestión de todas las solicitudes de contacto.
- Filtrado de solicitudes por estado, asesor y fechas de recepción.
- Actualización del estado de las solicitudes.
- Archivado, desarchivado y eliminación definitiva de solicitudes.

## 3. Flujo de estados de los planes

Los planes turísticos utilizan los siguientes estados:

| Estado | Descripción |
|---|---|
| Borrador | Plan creado por el asesor que puede continuar editándose. |
| Pendiente | Plan enviado por el asesor y pendiente de revisión administrativa. |
| Publicado | Plan aprobado y disponible para consulta pública. |

El flujo general es:

1. El asesor crea un plan.
2. El plan se guarda como borrador.
3. El asesor completa la información y el itinerario.
4. El asesor envía el plan a revisión.
5. El administrador aprueba o rechaza la propuesta.
6. Si se aprueba, el plan pasa a estado Publicado.
7. Si se rechaza, el plan regresa a estado Borrador para que el asesor pueda corregirlo.

Los planes pendientes no pueden eliminarse mientras se encuentran en revisión. Los asesores pueden eliminar sus propios borradores y planes publicados.

## 4. Gestión de solicitudes de contacto

Rumbalia permite que los visitantes manifiesten interés en los planes turísticos publicados mediante un formulario de contacto.

El visitante proporciona:

- Nombre.
- Correo electrónico.
- Número de teléfono.
- Mensaje opcional.

La solicitud queda almacenada en PostgreSQL y asociada al plan seleccionado.

### Estados de las solicitudes

| Estado | Descripción |
|---|---|
| Nueva | Solicitud recibida y pendiente de gestión. |
| En gestión | El asesor o administrador está realizando seguimiento. |
| Atendida | La solicitud ya fue atendida. |

### Administración de solicitudes

- El asesor consulta únicamente las solicitudes relacionadas con sus propios planes.
- El administrador puede consultar todas las solicitudes.
- Los usuarios autorizados pueden actualizar el estado de una solicitud.
- Las solicitudes pueden archivarse y desarchivarse.
- Las solicitudes archivadas se conservan en el historial.
- Se puede realizar la eliminación definitiva de una solicitud.
- Se registra información de seguimiento, incluyendo fechas de actualización y usuarios responsables.

La eliminación definitiva es irreversible.

## 5. Catálogo público, búsqueda y ofertas

### Experiencias

La sección Experiencias permite explorar planes publicados según intereses turísticos, entre ellos:

- Aventura.
- Playa.
- Cultura.
- Naturaleza.
- Gastronomía.
- Familiar.

### Buscador

El buscador permite consultar planes publicados mediante los siguientes criterios:

- Texto de búsqueda.
- Destino.
- País.
- Interés.
- Presupuesto máximo.
- Duración mínima.
- Duración máxima.

La búsqueda normaliza mayúsculas y tildes para facilitar la localización de destinos y planes. Por ejemplo, permite encontrar «Medellín» al escribir «medellin».

### Ofertas

La sección Ofertas presenta el espacio destinado a las promociones de planes turísticos.

El sistema permite consultar las ofertas que tengan un descuento configurado y cuya vigencia corresponda a la fecha actual. Si no existen promociones activas, se informa al visitante sin mostrar descuentos ficticios.

La estructura de la base de datos contempla:

- Porcentaje de descuento.
- Fecha de inicio de la oferta.
- Fecha de finalización de la oferta.

## 6. Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| Python 3 | Lenguaje principal del backend. |
| Flask | Framework para el servidor y la API. |
| PostgreSQL | Sistema de gestión de base de datos. |
| Psycopg2 | Conexión entre Python y PostgreSQL. |
| HTML5 | Estructura de la interfaz. |
| CSS3 | Diseño visual y estilos adaptables. |
| JavaScript | Interactividad y comunicación con la API. |
| Groq API | Servicio de inteligencia artificial para generar itinerarios. |
| OpenAI Python SDK | Cliente compatible utilizado para comunicarse con la API de Groq. |
| Werkzeug | Funciones de seguridad para el manejo de contraseñas. |
| Flask-CORS | Configuración de solicitudes entre orígenes. |
| Gunicorn | Servidor WSGI para el despliegue. |
| Render | Plataforma de despliegue de la aplicación. |

## 7. Arquitectura del proyecto

El proyecto utiliza una arquitectura organizada por responsabilidades:

- **Modelo (`src/model/logic.py`):** contiene las clases y reglas de negocio de usuarios, datos del viajero, planes turísticos, itinerarios, generación mediante IA y revisiones.
- **Controlador (`src/controller/planes_controller.py`):** gestiona las consultas, operaciones de persistencia y comunicación con PostgreSQL.
- **Backend (`app.py`):** implementa las rutas de la aplicación, autenticación, control de permisos, validaciones y comunicación entre frontend y controlador.
- **Frontend (`index.html`):** contiene la interfaz desarrollada con HTML, CSS y JavaScript.
- **Base de datos (`sql/schema.sql`):** define las tablas, relaciones, restricciones y datos iniciales.
- **Base de datos (`sql/`):** contiene el esquema principal de PostgreSQL (`schema.sql`).
- **Pruebas (`test/`):** contiene pruebas automatizadas del modelo.

## 8. Estructura de carpetas

```text
Turismo/
│
├── app.py
├── index.html
├── requirements.txt
├── README.md
├── secret_config_sample.py
├── .gitignore
│
├── sql/
│   ├── schema.sql

│
├── src/
│   ├── model/
│   │   ├── __init__.py
│   │   └── logic.py
│   │
│   └── controller/
│       ├── __init__.py
│       └── planes_controller.py
│
├── static/
│   ├── img/
│   │   └── logo-rumbalia.png
│   │
│   └── uploads/
│       └── destinos/
│
└── test/
    ├── __init__.py
    └── test_logic.py
```

## 9. Requisitos previos

Para ejecutar el proyecto se necesita:

- Python 3.
- PostgreSQL.
- Una base de datos PostgreSQL accesible.
- Una clave de API de Groq para utilizar la generación de itinerarios.
- Las dependencias especificadas en `requirements.txt`.

## 10. Instalación y configuración local

### 10.1. Obtener el proyecto

Descargar o clonar el repositorio y ubicarse en la carpeta raíz `Turismo/`.

### 10.2. Crear un entorno virtual

En Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

En Linux o macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 10.3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 10.4. Configurar PostgreSQL

Crear una base de datos PostgreSQL y preparar el archivo de configuración local.

Copiar:

```text
secret_config_sample.py
```

y crear una copia llamada:

```text
secret_config.py
```

Configurar los valores de conexión:

```python
PGHOST = "HOST_DE_POSTGRESQL"
PGDATABASE = "NOMBRE_DE_LA_BASE"
PGUSER = "USUARIO"
PGPASSWORD = "CONTRASEÑA"
PGPORT = 5432

GROQ_API_KEY = "CLAVE_DE_GROQ"
```

El archivo `secret_config.py` contiene información sensible y no debe subirse al repositorio ni compartirse públicamente.

### 10.5. Configurar la inteligencia artificial

Rumbalia utiliza Groq para generar itinerarios turísticos mediante un modelo compatible con la API de OpenAI.

La clave se configura mediante:

```python
GROQ_API_KEY = "CLAVE_DE_GROQ"
```

También puede proporcionarse mediante una variable de entorno con el mismo nombre.

Sin una clave válida, las funcionalidades de generación mediante IA no estarán disponibles.

## 11. Base de datos

Rumbalia utiliza PostgreSQL para almacenar usuarios, destinos, planes, itinerarios, solicitudes y revisiones administrativas.

### Tablas principales

| Tabla | Descripción |
|---|---|
| `usuarios` | Almacena los usuarios, credenciales, roles y estado de las cuentas. |
| `destinos` | Contiene los destinos turísticos disponibles. |
| `planes` | Almacena los planes turísticos creados por los asesores. |
| `imagenes_plan` | Almacena las fotografías asociadas a cada plan. |
| `itinerarios` | Relaciona cada plan con su itinerario. |
| `dias_itinerario` | Almacena las actividades correspondientes a cada día. |
| `revisiones` | Registra las decisiones administrativas sobre los planes. |
| `solicitudes_contacto` | Almacena las solicitudes enviadas por los visitantes y su seguimiento. |

### Relaciones y consideraciones

- Un asesor puede crear varios planes turísticos.
- Cada plan está relacionado con un destino.
- Cada plan puede tener un itinerario.
- Un itinerario puede contener varios días.
- Cada plan puede tener varias imágenes.
- Las solicitudes de contacto están relacionadas con el plan de interés.
- Las revisiones están relacionadas con los planes y los administradores responsables.

Las relaciones que corresponden utilizan claves foráneas para mantener la integridad de los datos. La eliminación de un plan también elimina los registros dependientes configurados con `ON DELETE CASCADE`.

### Inicialización de una base de datos nueva

El archivo `sql/schema.sql` contiene la estructura de las tablas, restricciones, índices y datos iniciales de prueba.

Para inicializar una base de datos nueva, se puede ejecutar el script desde una herramienta de administración de PostgreSQL.

Al ejecutar localmente:

```bash
python app.py
```

la aplicación también intenta ejecutar `PlanesController.crear_tabla()`, que procesa el archivo `sql/schema.sql`.

**Importante:** el script incluye datos iniciales de prueba y operaciones de preparación de destinos y planes. Antes de ejecutarlo sobre una base de datos que ya contiene información real, realiza un respaldo y revisa las operaciones del script.

## 12. Ejecución local

Desde la carpeta raíz `Turismo/`, con el entorno virtual activado:

```bash
python app.py
```

La aplicación estará disponible en:

```text
http://127.0.0.1:5000
```

Para detener el servidor, utilizar `Ctrl + C` en la terminal.

## 13. Despliegue en Render

La aplicación puede desplegarse como un servicio web de Python en Render.

### Configuración del servicio

| Parámetro | Valor |
|---|---|
| Runtime | Python 3 |
| Branch | `main` |
| Root Directory | Vacío si `app.py` está en la raíz del repositorio. |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |

### Variables de entorno

Configurar en Render las variables necesarias:

```text
SECRET_KEY
GROQ_API_KEY
```

También se pueden configurar las variables de conexión de PostgreSQL si se utiliza el archivo de configuración de ejemplo basado en variables de entorno.

### Archivo secreto de PostgreSQL

Si se utiliza el mecanismo de archivo secreto, crear en Render un Secret File con el nombre:

```text
secret_config.py
```

El archivo debe contener los parámetros de conexión a PostgreSQL y la clave de Groq.

La aplicación busca este archivo en `/etc/secrets/`.

No se debe subir `secret_config.py` al repositorio de GitHub.

### Consideraciones para Render

- El servicio web debe estar conectado a la base de datos PostgreSQL correspondiente.
- Se debe verificar que la conexión a PostgreSQL funcione desde el servicio desplegado.
- El comando de inicio utiliza Gunicorn.
- Gunicorn importa la aplicación mediante `app:app`; por ello, no ejecuta el bloque `if __name__ == "__main__"` de `app.py`.
- La base de datos debe estar inicializada previamente con el esquema principal de la base de datos.
- Las imágenes cargadas en el almacenamiento local del servicio pueden perderse al reiniciar o desplegar nuevamente el servicio, salvo que se configure almacenamiento persistente o externo.

## 14. Pruebas automatizadas

El proyecto contiene pruebas unitarias en:

```text
test/test_logic.py
```

Para ejecutarlas desde la raíz del proyecto:

```bash
python -m unittest discover -s test -p "test_*.py" -v
```

Las pruebas deben ejecutarse con las dependencias instaladas.

Las pruebas que requieran PostgreSQL deben realizarse sobre una base de datos de pruebas y no directamente sobre la base de datos de producción.

## 15. Seguridad y buenas prácticas

- Las contraseñas de los usuarios se almacenan utilizando funciones de hash seguro.
- Las rutas administrativas y de asesor cuentan con validación de rol.
- El registro público permite crear cuentas únicamente con rol de cliente.
- Los roles de asesor y administrador son gestionados desde el panel administrativo.
- Las operaciones de los asesores deben limitarse a sus propios planes y solicitudes.
- Las consultas SQL utilizan parámetros para reducir el riesgo de inyección SQL.
- Las claves de PostgreSQL y Groq deben mantenerse fuera del repositorio.
- Se recomienda utilizar una `SECRET_KEY` segura y diferente para producción.
- Se recomienda realizar respaldos antes de realizar cambios importantes o eliminaciones definitivas.
- La eliminación de solicitudes es irreversible.
- La eliminación de cuentas de usuario conserva los registros necesarios para mantener la integridad referencial.

## 16. Consideraciones y limitaciones del MVP

- La generación de itinerarios depende de la disponibilidad de la API de Groq y de una clave válida.
- Los resultados generados mediante inteligencia artificial deben ser revisados por el asesor antes de enviarse a aprobación.
- Las ofertas solo se muestran cuando tienen descuentos y fechas de vigencia configurados.
- La aplicación almacena las imágenes en el directorio local `static/uploads/destinos`; para producción se recomienda utilizar almacenamiento persistente o un servicio externo de imágenes.
- Las solicitudes de contacto son gestionadas dentro de la plataforma; el registro de una solicitud no implica que se haya enviado automáticamente un correo electrónico al cliente.
- El proyecto corresponde a un producto mínimo viable (MVP), por lo que puede ampliarse con nuevas funcionalidades en versiones posteriores.

---

**Proyecto:** Rumbalia – Plataforma Inteligente de Planes Turísticos.

**Versión:** MVP.

**Tecnologías principales:** Python, Flask, PostgreSQL, HTML, CSS y JavaScript.\n\n### Nombre y descripción comercial de los planes\n\nDurante la creación, el asesor puede escribir un nombre comercial para el plan. Si no lo especifica, Rumbalia conserva el nombre sugerido por destino y duración. La IA genera tanto el itinerario como una descripción comercial del viaje; el asesor puede editar ambos textos antes de enviar el plan a revisión. La descripción se muestra debajo de la galería de imágenes en el detalle público.\n\nLa tabla `planes` incluye la columna `descripcion`. En bases de datos ya existentes, ejecutar una sola vez `ALTER TABLE planes ADD COLUMN IF NOT EXISTS descripcion TEXT;` antes de desplegar esta versión. Esta actualización no requiere eliminar ni recrear tablas o registros.\n

## Generación comercial con IA

Al generar un plan, Groq devuelve ahora tres componentes: nombre comercial, descripción para el viajero e itinerario. El nombre y la descripción se muestran en el formulario de revisión para que el asesor pueda editarlos antes de continuar. Ambos campos se guardan junto con el plan y la descripción aparece debajo de la galería en el detalle público.

La columna `planes.descripcion` ya está contemplada en `sql/schema.sql`. Si la base de datos existente no la tiene, ejecutar una sola vez:

```sql
ALTER TABLE planes ADD COLUMN IF NOT EXISTS descripcion TEXT;
```

## Corrección de generación de itinerarios con IA

Se corrigió la lectura de la respuesta de Groq para reconocer correctamente los campos `NOMBRE` y `DESCRIPCION`, además de encabezados de día con formatos comunes (por ejemplo, `Día 1:`, `**Día 1:**` o `### Día 1:`). La validación continúa exigiendo exactamente la cantidad de días solicitada.

## Reasignación de planes y permisos de solicitudes

- Cuando se elimina un asesor, sus planes se conservan y aparecen en **Usuarios → Planes pendientes de reasignación** para que un administrador los asigne a un asesor activo.
- Cada reasignación se registra en `historial_asignaciones_planes` (plan, asesor anterior, nuevo asesor, administrador y fecha). La tabla se crea automáticamente al consultar la sección y también está incluida en `sql/schema.sql`.
- Las solicitudes de interés se pueden enviar como visitante o desde una cuenta cliente. Las sesiones de asesor y administrador reciben HTTP 403 tanto si intentan abrir el formulario como si llaman directamente al endpoint.
