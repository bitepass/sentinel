# Arquitectura General del Proyecto Sentinel

Este documento describe la arquitectura de alto nivel para un sistema de clasificación delictiva. El sistema sigue los principios SOLID para garantizar modularidad y mantenibilidad.

## Componentes Principales:
1.  **Orquestador (n8n):** Gestiona el flujo de trabajo completo. No contiene lógica de negocio.
2.  **Servicio de Persistencia:** Microservicio responsable de TODAS las interacciones con bases de datos (PostgreSQL) y archivos (Google Sheets, Excel, Word). Es el único guardián de los datos.
3.  **Servicio de Clasificación:** Microservicio que recibe datos, los divide en lotes y gestiona a los trabajadores que aplican la lógica de clasificación.

## Flujo de Datos Principal:
1.  **n8n** recibe una solicitud (ej. desde Discord).
2.  **n8n** le ordena al **Servicio de Persistencia** que lea la planilla y la prepare en PostgreSQL.
3.  **n8n** le ordena al **Servicio de Clasificación** que procese los datos preparados.
4.  El **Servicio de Clasificación** pide los datos por lotes al **Servicio de Persistencia**, los clasifica y le pide al mismo servicio que los guarde.
5.  Una vez finalizado, **n8n** le ordena al **Servicio de Persistencia** que genere la planilla "DELEGACION" final.