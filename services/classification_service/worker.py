#!/usr/bin/env python3
"""
Worker de Celery para el Servicio de Clasificación
Ejecutar con: python worker.py
"""

import os
import sys
from dotenv import load_dotenv

# Agregar el directorio app al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Cargar variables de entorno
load_dotenv()

# Importar la aplicación de Celery
from app.celery_app import celery_app

if __name__ == "__main__":
    # Configurar logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
    )
    
    # Iniciar worker
    celery_app.worker_main([
        'worker',
        '--loglevel=INFO',
        '--concurrency=2',  # Número de workers concurrentes
        '--queues=classification',  # Cola específica
        '--hostname=worker@%h',  # Nombre del worker
        '--without-gossip',  # Deshabilitar gossip para desarrollo
        '--without-mingle',  # Deshabilitar mingle para desarrollo
        '--without-heartbeat'  # Deshabilitar heartbeat para desarrollo
    ])
