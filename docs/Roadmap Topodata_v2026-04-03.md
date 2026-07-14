OFFICIAL 

## Roadmap Topodata 

## Fase 1: Gestión y Fundamentos 

- Contar como máx 33% jornada, ¿o cual es la estimación? 

- ¿Cuánto hay ya heho? Más o menos de cada fase 

- ¿Hasta qué iteración mínima hay que desarrollar para poder tener algo utilizable? ¿F 

- ¿Optimista? 

Iteración 1 (semanas 1 y 2): gestión de proyectos. 

- ➢ **Backend** : refinamiento de los endpoints de la entidad _Project_ . 

- ➢ **Frontend** : creación del dashboard principal y enrutamiento base. UI para crear, listar, modificar y eliminar proyectos. 

- Tecnologías ¿??? 

- ✓ **Entregable** : aplicacióon web funcional donde se puedan organizar y administrar proyectos. 

Iteración 2 (semanas 3 y 4): estructura de sesiones y estacionamientos. 

- ➢ **Backend** : lógica de vinculación completa entre proyectos, sesiones de importación y estacionamientos. 

   - API, token + usuario 

- ➢ **Frontend** : interfaz en árbol o tabla anidada para gestionar las sesiiones de medición y estacionamientos. 

   - CSS, multiidioma, usuario, permisos 

   - Previsión integración: Usuario + projectos (presas) + permisos 

- ✓ **Entregable** : vistas de las importaciones y estacionamientos para alojar los datos crudos. 

## Fase 2: ingesta de datos y exploración 

OFFICIAL 

Iteración 3 (semanas 5 y 6): carga de ficheros GKA. 

- ➢ **Backend** : pulir el parser para la lectura de ficheros _‘.gka’_ . Extracción automática de observaciones. 

- ➢ **Frontend** : componente de subida de ficheros asociado a un proyecto. 

- Creación automática de la sesión de importación, estacionamientos y observaciones crudas. Implementación de los indicadores de progreso y feedback de errores de formato. 

- ✓ **Entregable** : el sistema permite importar masivamente el contenido de un fichero GKA. 

## Iteración 4 (semanas 7 y 8): exploración y reducción de Bessel 

- ➢ **Backend** : pulir la lógica de cálculo automatizado de los promedios en círculo directo e inverso y generación automática de las entidades _BesselObservation_ . 

- ➢ **Frontend** : tablas de datos interactivas y reactivas para revisar las observaciones brutas ( _RawObservation_ ) y observaciones promediadas. Opciones de filtrado. 

- ✓ **Entregable** : el usuario puede visualizar en forma de tabla todas las mediciones importadas y revisar que los cálculos son coherentes. 

## Fase 3: cálculos previos 

Iteración 5 (semanas 9 y 10): gestión de coordenadas de referencia 

- ➢ **Backend** : implementar los endpoints para _ReferenceCoordinate_ e inyección en los proyectos. 

- ➢ **Frontend** : interfaz para introducir manualmente y masivamente bases de referencia. 

- ✓ **Entregable** : el usuario puede vincular la medición local al sistema de referencia. 

## Iteración 6 (semanas 11 y 12): cálculo previo 

- ➢ **Backend** : motor matemático preliminar para calcular las coordenadas aproximadas ( _ApproximateCoordinate_ ). 

OFFICIAL 

- ➢ **Frontend** : vista de resultados de cálculos previos, que resalte semafóricamente cierres angulares y en distancia, y errores groseros detectados. 

- ✓ **Entregable** : el usuario puede verificar si los datos son aceptables previamente al ajuste. 

## Fase 4: Motor de ajustes 

Iteración 7 (semanas 13 y 14): matrices, ecuaciones y parámetros del ajuste 

- ➢ **Backend** : diseño de las matrices con librerías matriciales como NumPy o SciPy. Formulación de ecuaciones. 

- ➢ **Frontend** : pantalla de configuración del cálculo: definición a priori de 

- errores e iteraciones. 

- ✓ **Entregable** : interfaz para configurar los cálculos. 

Iteración 8 (semanas 15 y 16): resolución matricial 

- ➢ **Backend** : resolución de las ecuaciones matriciales. 

- ➢ **Frontend** : botón accionable del cálculo. Vista de progreso. Vista de tabla de resulados. 

- ✓ **Entregable** : motor de ajuste completo. 

Iteración 9 (semanas 17 y 18): análisis de calidad y tests estadísticos 

- ➢ **Backend** : generación de información _a posteriori_ : cálculo de matrices de varianza-covarianza y ejecución de tests estadísticos para determinar la calidad. 

- ➢ **Frontend** : dashboard tabular avanzado. Identificación de datos 

- problemáticos y aceptación de residuos altos. 

- ✓ **Entregable** : el usuario puede verificar todo el proceso de ajuste. 

OFFICIAL 

Iteración 10 (semanas 19 y 20): visor gráfico 2D 

- ➢ **Backend** : endpoints para la obtención de la topología de la red. 

- ➢ **Frontend** : integración de un canvas 2D fluido con d3.js y SVG. 

- ✓ **Entregable** : el usuario puede visualizar los puntos, estaciones y líneas de visuales para comprender debilidades de la red. 

## Fase 5: estaciones totales automáticas 

Iteración 11 (semanas 21 y 22): ampliación del sistema para ETRs 

- ➢ **Backend** : adaptación de la base de datos, modelos y esquemas para permitir ciclos de lecturas automáticas. 

- ➢ **Frontend** : pantalla de configuración de un proyecto de ETR. 

- ✓ **Entregable** : el usuario puede configurar una ETR en un proyecto. 

Iteración 12 (semanas 23 y 24): parsing otros formatos 

- ➢ **Backend** : parser de ETRs e importación programada. 

- ➢ **Frontend** : pantallas y tablas para la visualización de datos brutos en directo. 

- ✓ **Entregable** : el sistema adquiere ficheros provenientes de ETRs y se visualizan los datos brutos. 

Iteración 13 (semanas 25 y 26): dashboards de auscultación 

- ➢ **Backend** : cálculo de movimientos acumulados con respecto a las referencias. 

- ➢ **Frontend** : implementación de gráficos de auscultación. 

- ✓ **Entregable** : módulo de auscultación donde se ve de forma gráfica el movimiento de los puntos. 

## Fase 6: funcionalidades accesorias 

OFFICIAL 

Iteración 14 (semanas 27, 28, 29 y 30): sistema de reportes 

- ➢ **Backend** : generación de reportes de expedientes y cálculos. 

- ➢ **Frontend** : panel de informes y flujos de descarga. 

- ✓ **Entregable** : módulo de informes. 

