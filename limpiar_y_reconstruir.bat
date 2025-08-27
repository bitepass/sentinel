@echo off
echo ========================================
echo LIMPIEZA Y RECONSTRUCCIÓN DOCKER
echo ========================================

echo.
echo 1. Deteniendo todos los servicios...
docker-compose down

echo.
echo 2. Limpiando contenedores, imágenes y volúmenes...
docker system prune -f
docker volume prune -f

echo.
echo 3. Construyendo imágenes sin cache...
docker-compose build --no-cache

echo.
echo 4. Levantando todos los servicios...
docker-compose up -d

echo.
echo 5. Verificando estado de los servicios...
docker-compose ps

echo.
echo 6. Mostrando logs de construcción...
docker-compose logs --tail=20

echo.
echo ========================================
echo RECONSTRUCCIÓN COMPLETADA
echo ========================================
echo.
echo Servicios disponibles:
echo - Redis: localhost:6379
echo - Persistencia: localhost:8001
echo - Clasificación: localhost:8002
echo - Flower: localhost:5555
echo - n8n: localhost:5678
echo.
echo Para ver logs en tiempo real:
echo docker-compose logs -f
echo.
pause
