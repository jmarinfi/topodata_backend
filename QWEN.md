# TopoData Backend

**⚠️ INSTRUCCIONES PRIORITARIAS:**

* **NO MODIFICAR NINGÚN FICHERO NI EJECUTAR NINGÚN COMANDO SIN MI INSTRUCCIÓN EXPLÍCITA.**
* **CONSULTA EL MCP CONTEXT7 PARA CONOCER LAS MEJORES PRÁCTICAS ACTUALIZADAS DE FASTAPI Y PYTHON EN CONSULTAS QUE IMPLIQUEN DECISIONES ARQUITECTÓNICAS.**

## Resumen del Proyecto

TopoData Backend es una API RESTful basada en Python diseñada para gestionar proyectos de topografía. El proyecto sigue una arquitectura en capas clara, separando las responsabilidades entre el enrutamiento de la API, la lógica de negocio y el acceso a datos.

### Tecnologías Clave

* **Lenguaje:** Python (>= 3.14)
* **Gestor de Paquetes:** `uv`
* **Framework Web:** FastAPI
* **ORM de Base de Datos:** SQLAlchemy (versión 2.0+)
* **Validación de Datos:** Pydantic (a través de los esquemas de FastAPI)
* **Base de Datos:** SQLite (`./sqlite_database/dev.db`)

## Arquitectura y Estructura

El código base está organizado en capas distintas para imponer la separación de responsabilidades:

* **`main.py`**: El punto de entrada de la aplicación. Configura la aplicación FastAPI, los eventos de ciclo de vida (inicialización de la base de datos), el middleware CORS e incluye todos los enrutadores.
* **`api/` (Capa de Presentación):**
* `routes/`: Define los endpoints de la API (por ejemplo, `project_router.py`). Los enrutadores delegan la lógica real a los servicios.
* `schemas/`: Contiene modelos Pydantic utilizados para la validación de peticiones y serialización de respuestas.
* `dependencies.py`: Define las dependencias de FastAPI para la inyección de dependencias (por ejemplo, inyectar servicios en los enrutadores).
* **`services/` (Capa de Lógica de Negocio):**
* Contiene la lógica central de negocio (por ejemplo, `ProjectService`).
* Los servicios manejan el procesamiento de datos, interactúan con los repositorios para obtener/guardar datos, y mapean los modelos SQLAlchemy a los esquemas Pydantic antes de devolver los datos a la capa de API.
* **`data/` (Capa de Acceso a Datos):**
* `database/engine.py`: Configura el motor de SQLAlchemy y la gestión de sesiones.
* `database/models/`: Define la base declarativa de SQLAlchemy y los modelos de base de datos (por ejemplo, `project.py`, `import_session.py`).
* `repositories/`: Implementa el patrón Repositorio. Los repositorios abstraen las consultas directas a la base de datos de los servicios, utilizando sesiones de SQLAlchemy para interactuar con los modelos.

## Compilación y Ejecución

Dado que el proyecto utiliza `uv` para la gestión de dependencias y la versión estándar de FastAPI, puedes ejecutar la aplicación de la siguiente manera:

1. **Instalar dependencias:**

```bash
uv sync
```

*(Alternativamente, puedes crear y activar el entorno virtual e instalar las dependencias manualmente si no utilizas `uv sync` directamente).*

1. **Ejecutar el servidor de desarrollo:**

```bash
uv run fastapi dev main.py
```

La API normalmente estará disponible en `http://localhost:8000` o `http://127.0.0.1:8000`. Puedes acceder a la documentación interactiva de Swagger en `/docs`.

## Convenciones de Desarrollo

* **Inyección de Dependencias:** El proyecto se basa en gran medida en el sistema de inyección de dependencias de FastAPI (`Depends`). Los servicios se inyectan en los enrutadores, y las sesiones de base de datos se inyectan en los repositorios/servicios.
* **Patrón Repositorio:** El acceso a la base de datos se abstrae a través de Repositorios. Los servicios no deben ejecutar consultas SQLAlchemy directamente; deben usar el Repositorio apropiado.
* **Tipado Estático (Type Hinting):** El proyecto utiliza el tipado moderno de Python de forma extensiva.
* **Validación de Datos:** Los esquemas de Pydantic (`ProjectCreate`, `ProjectResponse`, etc.) se utilizan estrictamente para validar las solicitudes entrantes y serializar las respuestas salientes en la capa de enrutamiento. Los servicios son responsables de convertir los objetos ORM a estos modelos Pydantic.
* **Manejo de Errores:** Los servicios lanzan excepciones estándar de Python (por ejemplo, `ValueError`), que la capa de enrutamiento captura y traduce en excepciones HTTP apropiadas (por ejemplo, `HTTPException(status_code=404)`).
