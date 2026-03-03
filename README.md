# TopoData Backend

TopoData Backend es una API RESTful desarrollada en Python (FastAPI) diseñada para la gestión, almacenamiento y procesamiento de datos topográficos.

El sistema permite estructurar la información jerárquicamente: desde proyectos generales y sesiones de importación, hasta estacionamientos específicos y sus correspondientes mediciones (observaciones brutas y observaciones procesadas por Bessel).

## 🚀 Tecnologías Principales

*   **Framework:** FastAPI
*   **Lenguaje:** Python (>= 3.14)
*   **Gestor de Dependencias:** `uv`
*   **Base de Datos:** SQLite (con Alembic para migraciones)
*   **ORM:** SQLAlchemy 2.0+
*   **Validación:** Pydantic (v2)

## 🏗️ Arquitectura del Proyecto

La aplicación sigue una arquitectura limpia basada en capas para garantizar la separación de responsabilidades y la mantenibilidad:

1.  **Capa de Presentación (API):** Define las rutas (Routers), inyección de dependencias y validación de entrada/salida (Esquemas Pydantic).
2.  **Capa de Lógica de Negocio (Services):** Contiene la lógica central y las reglas de negocio. Esta capa es agnóstica a la base de datos.
3.  **Capa de Acceso a Datos (Repositories & Models):** Implementa el patrón Repositorio para abstraer las consultas de SQLAlchemy y define los modelos de la base de datos.

### Entidades Principales (Modelos de Dominio)
*   `Project`: Proyectos principales de topografía.
*   `ImportSession`: Sesiones de importación de datos vinculadas a un proyecto.
*   `StationSetup`: Estacionamientos de los instrumentos de medición.
*   `RawObservation`: Observaciones o mediciones brutas obtenidas en campo.
*   `BesselObservation`: Observaciones procesadas matemáticamente (promedios en círculo directo e inverso).

## 🛠️ Instalación y Ejecución

El proyecto utiliza `uv` para una gestión rápida y eficiente del entorno y las dependencias.

1.  **Instalar dependencias:**
    ```bash
    uv sync
    ```

2.  **Aplicar migraciones de Base de Datos:**
    Asegúrate de que la base de datos esté actualizada a la última versión.
    ```bash
    uv run alembic upgrade head
    ```

3.  **Ejecutar el servidor en modo desarrollo:**
    ```bash
    uv run fastapi dev main.py
    ```

La API estará disponible por defecto en `http://127.0.0.1:8000`.
Puedes acceder a la documentación interactiva (Swagger UI) visitando `http://127.0.0.1:8000/docs`.
