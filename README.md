# RUMBALIA – Plataforma Inteligente de Planes Turísticos

Aplicación web para la creación, consulta y administración de planes turísticos personalizados mediante inteligencia artificial. Rumbalia conecta a clientes, asesores turísticos y administradores a través de una plataforma que facilita el diseño de experiencias de viaje, la generación de itinerarios, la revisión de propuestas y la publicación de planes turísticos.

Los asesores pueden crear planes con ayuda de inteligencia artificial, generar nombres comerciales, descripciones e itinerarios, y editar su contenido antes de enviarlo a revisión. Los administradores supervisan y gestionan la publicación de los planes, mientras que los clientes pueden explorar destinos, consultar experiencias y enviar solicitudes de contacto.

La plataforma está desarrollada con Python, Flask, PostgreSQL, HTML, CSS y JavaScript, e integra la API de Groq para la generación de contenido turístico mediante inteligencia artificial.

## Autores

- Francisco Gómez Gutiérrez
- Isabella Quintero Gutiérrez
- Nelson David Jiménez Ruiz

---

## 1. Descripción del proyecto

Rumbalia es una plataforma web orientada a facilitar la creación y consulta de experiencias turísticas personalizadas. Su propósito es conectar a clientes interesados en viajar con asesores encargados de diseñar planes turísticos y administradores responsables de supervisar su publicación.

La aplicación contempla tres roles principales:

- **Cliente:** explora los planes turísticos publicados, consulta sus características e itinerarios y puede enviar solicitudes de contacto sin necesidad de crear una cuenta.
- **Asesor:** crea planes turísticos, genera nombres comerciales, descripciones e itinerarios mediante inteligencia artificial, edita la información, administra borradores, envía planes a revisión y gestiona las solicitudes de los clientes.
- **Administrador:** supervisa los planes enviados a revisión, aprueba o rechaza propuestas, consulta estadísticas, administra las cuentas de usuario, reasigna planes cuando es necesario y gestiona las solicitudes de contacto.

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
- Autocompletado del nombre y correo electrónico al abrir el formulario de solicitud con una sesión de cliente activa. Estos datos pueden modificarse antes del envío.
- Ingreso manual de los datos de contacto para visitantes que no hayan iniciado sesión.
- Confirmación del envío de la solicitud.

### 2.3. Funcionalidades del asesor

- Creación de planes turísticos.
- Generación de nombres comerciales, descripciones e itinerarios mediante inteligencia artificial.
- Edición del nombre comercial y la descripción del plan.
- Edición de los días y las actividades del itinerario.
- Guardado y consulta de borradores.
- Envío de planes para revisión administrativa.
- Regreso de planes rechazados al estado de borrador.
- Actualización de la imagen principal de un plan.
- Administración de la galería de imágenes.
- Validación de imágenes cargadas y control de rutas duplicadas en la galería.
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
- Consulta de planes pendientes de reasignación cuando se elimina un asesor.
- Asignación de planes conservados a asesores activos.
- Registro del historial de reasignaciones.
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
3. El asesor completa la información comercial y el itinerario.
4. El asesor envía el plan a revisión.
5. El administrador aprueba o rechaza la propuesta.
6. Si se aprueba, el plan pasa a estado Publicado.
7. Si se rechaza, el plan regresa a estado Borrador para que el asesor pueda corregirlo y enviarlo nuevamente.

Los planes pendientes no pueden eliminarse mientras se encuentran en revisión. Los asesores pueden eliminar sus propios borradores y planes publicados.

Cuando se elimina una cuenta de asesor, sus planes se conservan para que un administrador pueda asignarlos a otro asesor activo. Las reasignaciones quedan registradas en el historial correspondiente.

## 4. Gestión de solicitudes de contacto

Rumbalia permite que los visitantes manifiesten interés en los planes turísticos publicados mediante un formulario de contacto.

El formulario solicita:

- Nombre.
- Correo electrónico.
- Número de teléfono.
- Mensaje opcional.

Cuando un cliente ha iniciado sesión, el formulario puede completar automáticamente su nombre y correo electrónico con los datos de su cuenta. Estos campos permanecen editables. El número de teléfono se ingresa manualmente.

Los visitantes sin sesión también pueden enviar solicitudes proporcionando sus datos de contacto.

La solicitud queda almacenada en PostgreSQL y asociada al plan seleccionado. Las solicitudes pueden ser consultadas y gestionadas por los usuarios autorizados según su rol.

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
- Las sesiones de asesor y administrador no pueden enviar solicitudes como clientes.
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

La sección Ofertas presenta las promociones de planes turísticos.

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
| Groq API | Servicio de inteligencia artificial para generar nombres comerciales, descripciones e itinerarios. |
| OpenAI Python SDK | Cliente compatible utilizado para comunicarse con la API de Groq. |
| Werkzeug | Funciones de seguridad para el manejo de contraseñas. |
| Flask-CORS | Configuración de solicitudes entre orígenes. |
| Gunicorn | Servidor WSGI para el despliegue. |
| Render | Plataforma de despliegue de la aplicación. |

## 7. Arquitectura del proyecto

El proyecto utiliza una arquitectura organizada por responsabilidades:

- **Modelo (`src/model/logic.py`):** contiene las clases y reglas de negocio relacionadas con usuarios, planes turísticos, itinerarios, generación mediante IA y revisiones.
- **Controlador (`src/controller/planes_controller.py`):** gestiona las consultas, operaciones de persistencia y comunicación con PostgreSQL.
- **Backend (`app.py`):** implementa las rutas de la aplicación, autenticación, control de permisos, validaciones y comunicación entre frontend y controlador.
- **Frontend (`index.html`):** contiene la interfaz desarrollada con HTML, CSS y JavaScript.
- **Base de datos (`sql/schema.sql`):** define las tablas, relaciones, restricciones, índices y datos iniciales.
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
- Una clave de API de Groq para utilizar la generación de contenido mediante inteligencia artificial.
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
python -m pip install -r requirements.txt
```

### 10.4. Configurar las variables de entorno

La aplicación utiliza variables de entorno para gestionar las credenciales de PostgreSQL y Groq.

Configurar las siguientes variables:

| Variable | Descripción |
|---|---|
| `PGHOST` | Dirección del servidor PostgreSQL. |
| `PGDATABASE` | Nombre de la base de datos. |
| `PGUSER` | Usuario de PostgreSQL. |
| `PGPASSWORD` | Contraseña de PostgreSQL. |
| `PGPORT` | Puerto de conexión de PostgreSQL. |
| `GROQ_API_KEY` | Clave de acceso a la API de Groq. |
| `SECRET_KEY` | Clave secreta utilizada por Flask para gestionar las sesiones. |

El archivo `secret_config_sample.py` contiene una plantilla que permite leer los valores desde las variables de entorno. Si el proyecto requiere el módulo `secret_config.py`, se puede crear una copia de la plantilla con ese nombre.

No se deben incluir credenciales reales en el repositorio ni compartir públicamente el archivo `secret_config.py`.

### 10.5. Configurar la inteligencia artificial

Rumbalia utiliza Groq para generar contenido turístico mediante un modelo compatible con la API de OpenAI.

La clave de acceso se proporciona mediante la variable de entorno:

```text
GROQ_API_KEY
```

La generación mediante IA permite obtener:

- Nombre comercial del plan.
- Descripción del viaje para el cliente.
- Itinerario organizado por días y actividades.

El asesor puede revisar y editar el nombre, la descripción y el itinerario antes de enviar el plan a revisión administrativa.

Sin una clave válida y acceso al servicio de Groq, las funcionalidades de generación mediante IA no estarán disponibles.

## 11. Base de datos

Rumbalia utiliza PostgreSQL para almacenar usuarios, destinos, planes, itinerarios, imágenes, solicitudes de contacto y revisiones administrativas.

### Tablas principales

| Tabla | Descripción |
|---|---|
| `usuarios` | Almacena los usuarios, credenciales, roles y estado de las cuentas. |
| `destinos` | Contiene los destinos turísticos disponibles. |
| `planes` | Almacena los planes turísticos creados por los asesores, incluyendo su información comercial y descripción. |
| `imagenes_plan` | Almacena las fotografías asociadas a cada plan. |
| `itinerarios` | Relaciona cada plan con su itinerario. |
| `dias_itinerario` | Almacena las actividades correspondientes a cada día. |
| `revisiones` | Registra las decisiones administrativas sobre los planes. |
| `solicitudes_contacto` | Almacena las solicitudes enviadas por visitantes y clientes, así como su seguimiento. |
| `historial_asignaciones_planes` | Registra las reasignaciones de planes entre asesores. |

### Relaciones y consideraciones

- Un asesor puede crear varios planes turísticos.
- Cada plan está relacionado con un destino.
- Cada plan puede tener un itinerario.
- Un itinerario puede contener varios días.
- Cada plan puede tener varias imágenes.
- Las solicitudes de contacto están relacionadas con el plan de interés.
- Las revisiones están relacionadas con los planes y los administradores responsables.
- El historial de asignaciones permite consultar los cambios de asesor responsable de un plan.

Las relaciones correspondientes utilizan claves foráneas para mantener la integridad de los datos. La eliminación de un plan también elimina los registros dependientes configurados con `ON DELETE CASCADE`.

### Inicialización de una base de datos nueva

El archivo `sql/schema.sql` contiene la estructura de las tablas, restricciones, índices y datos iniciales de prueba.

Para inicializar una base de datos nueva, se puede ejecutar el script desde una herramienta de administración de PostgreSQL.

Al ejecutar localmente:

```bash
python app.py
```

la aplicación también intenta ejecutar `PlanesController.crear_tabla()`, que procesa el archivo `sql/schema.sql`.

**Importante:** el script incluye datos iniciales de prueba y operaciones de preparación de destinos y planes. Antes de ejecutarlo sobre una base de datos que ya contiene información real, realiza un respaldo y revisa las operaciones del script.

### Actualización de bases de datos existentes

La tabla `planes` utiliza la columna `descripcion` para almacenar la descripción comercial de cada plan.

Si una base de datos existente no cuenta con esta columna, ejecutar una sola vez:

```sql
ALTER TABLE planes ADD COLUMN IF NOT EXISTS descripcion TEXT;
```

Esta operación agrega la columna sin eliminar las tablas ni los registros existentes.

La tabla `historial_asignaciones_planes` forma parte del esquema de la aplicación y se utiliza para registrar las reasignaciones de planes.

## 12. Ejecución local

Desde la carpeta raíz `Turismo/`, con el entorno virtual activado y las variables de entorno configuradas:

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
PGHOST
PGDATABASE
PGUSER
PGPASSWORD
PGPORT
```

Los valores de conexión deben corresponder a la base de datos PostgreSQL utilizada por la aplicación.

### Configuración de fotografías y almacenamiento persistente

Las fotografías de los planes se guardan en la ubicación definida por la variable `UPLOAD_FOLDER`.

En desarrollo local, si no se define esta variable, Rumbalia utiliza:

```text
static/uploads/destinos
```

En Render, el sistema de archivos predeterminado es efímero. Esto significa que los archivos guardados localmente pueden perderse cuando el servicio se reinicia o se despliega nuevamente.

Para conservar las fotografías se recomienda configurar un Persistent Disk:

1. En el Dashboard de Render, abre el servicio web de Rumbalia y entra a **Disks**.
2. Agrega un Persistent Disk. Esta funcionalidad requiere un plan de servicio compatible. Los discos persistentes no están disponibles en el plan Free.
3. Configura el **Mount Path** con el valor:

   ```text
   /var/data
   ```

4. En **Environment**, agrega la variable:

   ```text
   UPLOAD_FOLDER=/var/data/uploads/destinos
   ```

5. Guarda los cambios y espera a que termine el nuevo despliegue.
6. Crea un plan de prueba con una imagen principal y varias fotografías en la galería. Comprueba que sigan disponibles después de reiniciar o desplegar nuevamente el servicio.

La aplicación conserva las rutas públicas de las fotografías bajo `/static/uploads/destinos/...` y utiliza `UPLOAD_FOLDER` como ubicación física de almacenamiento. También puede realizar una migración de archivos locales existentes hacia el almacenamiento persistente cuando estos todavía están disponibles.

**Importante:** un Persistent Disk de Render está conectado a una sola instancia y no permite escalar horizontalmente el servicio a varias instancias. Si se necesita utilizar varias instancias o un plan sin discos persistentes, se recomienda implementar un servicio de almacenamiento de objetos externo, como Amazon S3 o Cloudinary.

### Archivo secreto de PostgreSQL

Como alternativa a las variables de entorno individuales, si se utiliza el mecanismo de archivos secretos de Render, se puede crear un Secret File con el nombre:

```text
secret_config.py
```

Este archivo debe contener los parámetros de conexión a PostgreSQL y la clave de Groq, siguiendo la estructura que espera la aplicación.

Cuando se utiliza este mecanismo, la aplicación busca el archivo en:

```text
/etc/secrets/
```

No se debe subir `secret_config.py` al repositorio de GitHub.

### Consideraciones para Render

- El servicio web debe estar conectado a la base de datos PostgreSQL correspondiente.
- Se debe verificar que la conexión a PostgreSQL funcione desde el servicio desplegado.
- El comando de inicio utiliza Gunicorn.
- Gunicorn importa la aplicación mediante `app:app`; por ello, no ejecuta el bloque `if __name__ == "__main__"` de `app.py`.
- La base de datos debe estar inicializada previamente con el esquema principal.
- Se debe configurar el almacenamiento persistente o externo para conservar las fotografías entre despliegues.

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
- Las sesiones de asesor y administrador no pueden utilizar las funcionalidades destinadas al envío de solicitudes como cliente.
- Las consultas SQL utilizan parámetros para reducir el riesgo de inyección SQL.
- Las claves de PostgreSQL y Groq deben mantenerse fuera del repositorio.
- Se recomienda utilizar una `SECRET_KEY` segura y diferente para producción.
- Se recomienda realizar respaldos antes de realizar cambios importantes o eliminaciones definitivas.
- La eliminación de solicitudes es irreversible.
- La eliminación de cuentas de usuario conserva los registros necesarios para mantener la integridad referencial.

## 16. Consideraciones y limitaciones del MVP

- La generación de nombres comerciales, descripciones e itinerarios depende de la disponibilidad de la API de Groq y de una clave válida.
- Los resultados generados mediante inteligencia artificial deben ser revisados por el asesor antes de enviarse a aprobación.
- Las ofertas solo se muestran cuando tienen descuentos y fechas de vigencia configurados.
- Las imágenes se almacenan en `UPLOAD_FOLDER`; en desarrollo se utiliza `static/uploads/destinos` y en Render se recomienda configurar un Persistent Disk o un almacenamiento de objetos externo.
- Las solicitudes de contacto son gestionadas dentro de la plataforma; el registro de una solicitud no implica que se haya enviado automáticamente un correo electrónico al cliente.
- El proyecto corresponde a un producto mínimo viable (MVP), por lo que puede ampliarse con nuevas funcionalidades en versiones posteriores.

---

**Proyecto:** Rumbalia – Plataforma Inteligente de Planes Turísticos.

**Versión:** MVP.

**Tecnologías principales:** Python, Flask, PostgreSQL, HTML, CSS y JavaScript.