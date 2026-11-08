# Diseñador Inteligente de Planes Turísticos – MVP

Aplicación web para la creación, consulta y administración de planes turísticos mediante inteligencia artificial, desarrollada con Python, Flask, PostgreSQL, HTML, CSS y JavaScript.

## Autores

- Francisco Gómez Gutiérrez
- Isabella Quintero Gutiérrez
- Nelson David Jiménez Ruiz

## 1. Descripción del proyecto

El Diseñador Inteligente de Planes Turísticos permite gestionar planes de viaje y facilitar la creación de itinerarios personalizados según las características y preferencias del viajero.

La aplicación contempla tres roles:

- **Asesor:** crea planes turísticos, genera itinerarios con inteligencia artificial, edita las propuestas, guarda borradores y envía planes a revisión.
- **Administrador:** consulta los planes pendientes, revisa su información y decide si los aprueba o rechaza.
- **Cliente:** consulta los planes publicados y visualiza sus detalles e itinerarios.

## 2. Alcance del MVP – Sprint 1

El MVP contempla las siguientes funcionalidades:

- Inicio de sesión y control de acceso según el rol del usuario.
- Consulta de planes turísticos publicados.
- Exploración de destinos por continente.
- Visualización del detalle de los planes y sus itinerarios.
- Creación de planes turísticos por parte del asesor.
- Generación de itinerarios mediante inteligencia artificial.
- Edición de los días del itinerario generado.
- Guardado de planes como borradores.
- Envío de planes para revisión administrativa.
- Panel de administración para consultar planes pendientes.
- Aprobación o rechazo de planes por parte del administrador.
- Persistencia de usuarios, destinos, planes, itinerarios y revisiones en PostgreSQL.

Las funcionalidades que no hacen parte de este alcance quedan para sprints posteriores.

## 3. Tecnologías utilizadas

- **Python 3:** lenguaje principal del backend.
- **Flask:** framework para el servidor y la API.
- **PostgreSQL:** sistema de gestión de base de datos.
- **Psycopg2:** conexión entre Python y PostgreSQL.
- **HTML5:** estructura de la interfaz.
- **CSS3:** estilos y diseño adaptable.
- **JavaScript:** interacción con el usuario y consumo de la API mediante `fetch()`.
- **OpenAI API:** generación de propuestas de itinerarios turísticos.
- **Flask-CORS:** configuración de solicitudes entre orígenes.

## 4. Arquitectura del proyecto

El sistema utiliza una arquitectura organizada por capas:

- **Modelo (`src/model/logic.py`):** contiene las clases y reglas de negocio relacionadas con los usuarios, los datos del viajero, los planes turísticos, la generación de itinerarios y las revisiones.
- **Controlador (`src/controller/planes_controller.py`):** gestiona las operaciones de persistencia y consultas a PostgreSQL.
- **Backend (`app.py`):** implementa las rutas de la aplicación, las validaciones de solicitudes, la autenticación y la comunicación entre la interfaz y el controlador.
- **Frontend (`index.html`):** contiene la interfaz desarrollada con HTML, CSS y JavaScript.
- **Base de datos (`sql/schema.sql`):** define las tablas y los datos iniciales del sistema.
- **Pruebas (`test/`):** contiene las pruebas automatizadas del modelo.

## Promociones y búsqueda sin tildes

La búsqueda pública normaliza mayúsculas y tildes en destino, país, nombre del plan e intereses. Por ejemplo, `medellin` encuentra `Medellín`. La normalización SQL usa `translate()` y no requiere instalar la extensión PostgreSQL `unaccent`.

Para habilitar ofertas en una base de datos existente, ejecutar una sola vez el script `sql/migration_ofertas.sql` en PostgreSQL. La migración agrega el porcentaje de descuento y las fechas de vigencia; los planes existentes quedan con descuento 0 y no se eliminan ni modifican sus datos comerciales. El asesor puede definir la promoción en el formulario del borrador antes de enviarlo a revisión. Solo se muestran ofertas de planes publicados cuya vigencia incluya la fecha actual.

## 5. Estructura de carpetas

```text
Turismo/
│
├── app.py
├── index.html
├── requirements.txt
├── secret_config.py
├── secret_config_sample.py
├── README.md
│
├── docs/
│   └── Implementación del MVP de planes turísticos
│
├── sql/
│   └── schema.sql
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
│   └── uploads/
│       └── destinos/
│
└── test/
    ├── __init__.py
    └── test_logic.py
```

## 6. Requisitos previos

Para ejecutar el proyecto se necesita:

- Python 3.
- PostgreSQL.
- Una base de datos PostgreSQL accesible.
- Una clave de API de OpenAI para utilizar la generación de itinerarios.
- Las dependencias especificadas en `requirements.txt`.

## 7. Instalación y configuración

### 7.1. Clonar o descargar el proyecto

Ubicarse en la carpeta raíz `Turismo/`.

### 7.2. Crear un entorno virtual

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

### 7.3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 7.4. Configurar PostgreSQL

Copiar el archivo:

```text
secret_config_sample.py
```

y crear una copia llamada:

```text
secret_config.py
```

Configurar los datos de conexión a PostgreSQL:

```python
PGHOST = "su_host"
PGDATABASE = "nombre_de_la_base_de_datos"
PGUSER = "su_usuario"
PGPASSWORD = "su_contraseña"
PGPORT = 5432
```

El archivo `secret_config.py` contiene información sensible y no debe publicarse en el repositorio.

### 7.5. Configurar la API de OpenAI

Configurar la clave de API de OpenAI según el mecanismo de configuración utilizado por el proyecto.

No publicar la clave en el repositorio ni compartirla públicamente.

## 8. Ejecución del proyecto

Desde la carpeta raíz:

```bash
python app.py
```

Al iniciar mediante este comando, la aplicación ejecuta la inicialización de la base de datos utilizando `sql/schema.sql`.

La aplicación estará disponible en:

```text
http://127.0.0.1:5000
```

## 9. Base de datos

El proyecto utiliza PostgreSQL y contempla las siguientes tablas:

| Tabla | Descripción |
|---|---|
| `usuarios` | Almacena usuarios, credenciales y roles. |
| `destinos` | Contiene los destinos turísticos disponibles. |
| `planes` | Almacena los planes turísticos creados. |
| `itinerarios` | Relaciona cada plan con su itinerario. |
| `dias_itinerario` | Almacena las actividades de cada día. |
| `revisiones` | Registra las decisiones administrativas. |

La estructura y los datos iniciales se encuentran en `sql/schema.sql`.

## 10. Pruebas automatizadas

El proyecto contiene pruebas unitarias en:

```text
test/test_logic.py
```

Para ejecutarlas desde la carpeta raíz:

```bash
python -m unittest discover -s test -p "test_*.py" -v
```

El resultado de las pruebas debe verificarse después de instalar las dependencias necesarias.

## 11. Consideraciones del MVP

- Los planes turísticos deben conservar su relación con el destino y el asesor que los creó.
- Cada plan debe tener asociado su itinerario y los días correspondientes cuando exista una propuesta generada.
- Los planes enviados a revisión deben poder ser consultados por el administrador.
- Los planes aprobados quedan disponibles para su consulta pública.
- Los planes rechazados deben conservar la información del motivo de rechazo cuando corresponda.
- La información debe mantenerse persistida en PostgreSQL.

---

**Proyecto:** Diseñador Inteligente de Planes Turísticos.

**Versión:** MVP – Sprint 1.

## 12. Funcionalidades integradas en esta versión

- El asesor puede eliminar sus planes en estado **Borrador** o **Publicado**.
  Los planes pendientes de revisión quedan protegidos.
- El asesor puede reemplazar la imagen de un plan desde la pantalla de edición
  del borrador. La imagen se guarda a nivel de plan, para no modificar la
  fotografía compartida de otros planes del mismo destino.
- El visitante puede enviar una solicitud de contacto desde el detalle de un
  plan publicado, sin crear una cuenta.
- El asesor puede consultar las solicitudes recibidas para sus propios planes.
- La tabla `solicitudes_contacto` almacena nombre, correo, teléfono, mensaje,
  estado y fecha de recepción.

### Migración de base de datos

Al iniciar la aplicación, `PlanesController.crear_tabla()` ejecuta
`sql/schema.sql`. El script agrega `planes.imagen_url` con
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS` y crea `solicitudes_contacto`
si todavía no existe. No elimina las tablas ni los registros actuales.

### Endpoints nuevos

| Método | Ruta | Uso |
|---|---|---|
| PUT | `/api/planes/<id>/imagen` | Cambiar la imagen de un borrador propio (asesor). |
| POST | `/api/planes/<id>/solicitudes` | Registrar interés de un visitante en un plan publicado. |
| GET | `/api/asesor/solicitudes` | Consultar solicitudes de los planes del asesor autenticado. |


## Catálogo público y secciones complementarias

El menú público incluye ahora las secciones **Experiencias**, **Ofertas** y **Nosotros**.

- **Experiencias:** permite filtrar planes publicados por intereses (aventura, playa, cultura, naturaleza, gastronomía y familiar).
- **Ofertas:** muestra el espacio de promociones y, mientras no existan promociones configuradas, informa de forma explícita que no hay ofertas activas. No calcula ni inventa descuentos.
- **Nosotros:** presenta una descripción general de la plataforma y sus principios de orientación, descubrimiento y acompañamiento.
- **Buscador:** consulta planes publicados por destino, país, duración, interés y presupuesto máximo. Destino y país se filtran por separado para evitar confundir ciudades con el mismo nombre.

### Endpoint de búsqueda pública

`GET /api/planes/buscar` admite los parámetros opcionales `q`, `destino`, `pais`, `interes`, `presupuesto_max`, `duracion_min` y `duracion_max`. La consulta usa parámetros SQL y devuelve exclusivamente planes con estado `Publicado`.

La sección Ofertas queda preparada visualmente, pero la administración de promociones/descuentos (precio anterior, vigencia y publicación) requiere una siguiente iteración de datos y permisos; hasta entonces no se mostrarán descuentos ficticios.


## Registro de clientes y seguimiento (actualización MVP)

- El formulario público permite crear cuentas únicamente con rol `cliente`.
- El endpoint `POST /api/registro` valida nombre, correo, contraseña y aceptación del tratamiento de datos; las contraseñas se guardan con hash seguro de Werkzeug.
- Al completar el registro se inicia sesión automáticamente. Asesores y administradores no pueden autoasignarse esos roles desde el registro público.
- El panel del asesor incluye reportes propios y actualización del estado de sus solicitudes (`Nueva`, `Contactada`, `Cerrada`).
- El administrador puede consultar las solicitudes globales desde su nueva sección.


## Gestión de cuentas administrativas (RUMBALIA)

Antes de desplegar esta versión sobre una base de datos existente, ejecutar una sola vez `sql/migration_usuarios_activos.sql`. La migración agrega `usuarios.activo` y conserva todas las cuentas actuales como activas. En instalaciones nuevas, `schema.sql` ya incluye la columna.

Desde Administrador > Usuarios se pueden crear cuentas de asesor y administrador, activar/desactivar cuentas y solicitar su eliminación. La eliminación es lógica (desactivación): se conserva el historial de planes y revisiones y se impide el inicio de sesión. No se permite desactivar la propia cuenta ni dejar el sistema sin administradores activos. El registro público continúa creando únicamente clientes.


### Migración de eliminación lógica de usuarios

Antes de desplegar esta versión sobre una base de datos existente, ejecutar una sola vez `sql/migration_usuarios_eliminados.sql`. Agrega `usuarios.eliminado` y `usuarios.fecha_eliminacion` sin borrar cuentas ni relaciones. La sección Usuarios separa las cuentas activas/desactivadas del historial de cuentas eliminadas. Las cuentas eliminadas no pueden iniciar sesión.


## Gestión de solicitudes (actualización)

Para actualizar una base de datos existente, ejecutar una sola vez `sql/migration_gestion_solicitudes.sql`. Esta migración agrega los datos de archivado y auditoría y normaliza los estados anteriores (`Contactada` → `En gestión`, `Cerrada` → `Atendida`).

Las solicitudes activas aparecen en la bandeja principal. Asesores gestionan únicamente las solicitudes de sus planes; administradores pueden gestionar todas. Al archivar, la solicitud deja de aparecer en la bandeja principal y queda visible automáticamente en el historial correspondiente. Los registros no se eliminan físicamente.


## Gestión y seguimiento de solicitudes de contacto

La versión actual incorpora seguimiento comercial para asesor y administrador:

- Estados permitidos: **Nueva**, **En gestión** y **Atendida**.
- El asesor consulta únicamente solicitudes asociadas a sus propios planes.
- El administrador consulta todas las solicitudes y puede filtrar por estado, asesor y fechas de recepción.
- Ambos roles pueden archivar solicitudes; el historial se carga automáticamente al abrir la sección.
- Archivar no elimina el registro. No se ofrece eliminación definitiva desde las bandejas.
- Se conservan fecha de recepción, fecha de actualización y usuario que realizó la última actualización.

### Actualizar una base de datos existente

Antes de desplegar esta versión sobre una base PostgreSQL ya utilizada, realiza un respaldo y ejecuta una sola vez `sql/migration_gestion_solicitudes.sql`. La migración es idempotente: agrega los campos de trazabilidad, normaliza los estados antiguos `Contactada` y `Cerrada`, y crea los índices necesarios. En una base nueva, `sql/schema.sql` ya incluye estos campos.

Las pruebas de integración con PostgreSQL deben ejecutarse contra una base de pruebas; no se han realizado sobre las credenciales reales de producción.


## Ajustes de gestión de solicitudes y privacidad de usuarios

- Asesor y administrador pueden archivar y desarchivar solicitudes.
- Asesor y administrador pueden eliminar físicamente solicitudes activas o archivadas. Esta acción es irreversible.
- El detalle de cada solicitud muestra los datos de contacto, plan, fecha de recepción y comentario (o indica que no se dejó comentario).
- Al eliminar una cuenta, RUMBALIA bloquea el acceso y anonimiza nombre, correo y contraseña almacenada. La fila técnica se conserva para no romper las relaciones de planes y registros históricos.
- Las cuentas eliminadas ya no se muestran en el listado habitual de usuarios ni en una pantalla de historial con datos personales.

Ejecuta `sql/migration_gestion_solicitudes.sql` una sola vez en la base de datos (después de hacer un respaldo) para aplicar los cambios de esquema y anonimizar las cuentas que ya estaban marcadas como eliminadas.
