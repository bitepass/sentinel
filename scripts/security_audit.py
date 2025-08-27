#!/usr/bin/env python3
# 🔐 SCRIPT DE AUDITORÍA DE SEGURIDAD AUTOMATIZADA - SISTEMA SENTINEL
# ⚠️  EJECUTAR REGULARMENTE PARA VERIFICAR SEGURIDAD

import os
import sys
import json
import requests
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import docker
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityAuditor:
    """Auditor de seguridad automatizado para el sistema Sentinel"""
    
    def __init__(self):
        load_dotenv()
        self.audit_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_score": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "checks": [],
            "recommendations": []
        }
        
        # Configuración de seguridad
        self.required_env_vars = [
            "API_TOKEN", "REDIS_PASSWORD", "FLOWER_USER", "FLOWER_PASSWORD",
            "N8N_USER", "N8N_PASSWORD", "N8N_SESSION_SECRET"
        ]
        
        self.security_endpoints = {
            "persistence": "http://localhost:8001/health",
            "classification": "http://localhost:8002/health",
            "redis": "localhost:6379",
            "flower": "http://localhost:5555/flower/",
            "n8n": "http://localhost:5678/"
        }
    
    def run_full_audit(self) -> Dict:
        """Ejecuta auditoría completa de seguridad"""
        logger.info("🚀 Iniciando auditoría de seguridad completa...")
        
        try:
            # 1. Verificar variables de entorno
            self.check_environment_security()
            
            # 2. Verificar servicios en ejecución
            self.check_running_services()
            
            # 3. Verificar autenticación de endpoints
            self.check_endpoint_authentication()
            
            # 4. Verificar configuración de Docker
            self.check_docker_security()
            
            # 5. Verificar logs de seguridad
            self.check_security_logs()
            
            # 6. Calcular puntuación general
            self.calculate_overall_score()
            
            # 7. Generar recomendaciones
            self.generate_recommendations()
            
        except Exception as e:
            logger.error(f"Error durante la auditoría: {e}")
            self.audit_results["error"] = str(e)
        
        return self.audit_results
    
    def check_environment_security(self):
        """Verifica la configuración de variables de entorno"""
        logger.info("🔍 Verificando variables de entorno de seguridad...")
        
        missing_vars = []
        weak_vars = []
        
        for var_name in self.required_env_vars:
            value = os.getenv(var_name)
            
            if not value:
                missing_vars.append(var_name)
                self.add_issue("CRÍTICA", f"Variable de entorno faltante: {var_name}")
            elif len(value) < 16:
                weak_vars.append(var_name)
                self.add_issue("ALTA", f"Variable de entorno débil: {var_name} (muy corta)")
        
        if not missing_vars and not weak_vars:
            self.add_check("✅ Variables de entorno", "PASS", "Todas las variables están configuradas correctamente")
        else:
            self.add_check("❌ Variables de entorno", "FAIL", f"Problemas encontrados: {len(missing_vars)} faltantes, {len(weak_vars)} débiles")
    
    def check_running_services(self):
        """Verifica que los servicios estén ejecutándose"""
        logger.info("🔍 Verificando servicios en ejecución...")
        
        try:
            client = docker.from_env()
            containers = client.containers.list()
            
            required_containers = [
                "sentinel_redis", "sentinel_persistence", "sentinel_classification",
                "sentinel_flower", "sentinel_n8n"
            ]
            
            running_containers = [c.name for c in containers]
            missing_containers = [name for name in required_containers if name not in running_containers]
            
            if not missing_containers:
                self.add_check("✅ Servicios ejecutándose", "PASS", f"Todos los servicios están activos: {', '.join(running_containers)}")
            else:
                self.add_issue("ALTA", f"Servicios faltantes: {', '.join(missing_containers)}")
                self.add_check("❌ Servicios ejecutándose", "FAIL", f"Faltan servicios: {', '.join(missing_containers)}")
                
        except Exception as e:
            self.add_issue("MEDIA", f"No se pudo verificar Docker: {e}")
    
    def check_endpoint_authentication(self):
        """Verifica que los endpoints requieran autenticación"""
        logger.info("🔍 Verificando autenticación de endpoints...")
        
        # Verificar endpoint de clasificación (debe requerir token)
        try:
            response = requests.get(self.security_endpoints["classification"], timeout=5)
            if response.status_code == 401:
                self.add_check("✅ Autenticación API", "PASS", "Endpoint requiere autenticación")
            else:
                self.add_issue("CRÍTICA", "Endpoint de clasificación no requiere autenticación")
                self.add_check("❌ Autenticación API", "FAIL", "Endpoint accesible sin autenticación")
        except Exception as e:
            self.add_issue("MEDIA", f"No se pudo verificar endpoint de clasificación: {e}")
        
        # Verificar Redis (debe requerir password)
        try:
            result = subprocess.run(
                ["redis-cli", "-h", "localhost", "-p", "6379", "ping"],
                capture_output=True, text=True, timeout=5
            )
            if "NOAUTH" in result.stderr:
                self.add_check("✅ Autenticación Redis", "PASS", "Redis requiere autenticación")
            else:
                self.add_issue("CRÍTICA", "Redis no requiere autenticación")
                self.add_check("❌ Autenticación Redis", "FAIL", "Redis accesible sin password")
        except Exception as e:
            self.add_issue("MEDIA", f"No se pudo verificar Redis: {e}")
    
    def check_docker_security(self):
        """Verifica configuración de seguridad de Docker"""
        logger.info("🔍 Verificando configuración de seguridad de Docker...")
        
        try:
            client = docker.from_env()
            
            # Verificar que los containers no se ejecuten como root
            root_containers = []
            for container in client.containers.list():
                try:
                    exec_result = container.exec_run("whoami")
                    if "root" in exec_result.output.decode():
                        root_containers.append(container.name)
                except:
                    pass
            
            if not root_containers:
                self.add_check("✅ Usuarios no-root", "PASS", "Todos los containers ejecutan como usuarios no-root")
            else:
                self.add_issue("ALTA", f"Containers ejecutándose como root: {', '.join(root_containers)}")
                self.add_check("❌ Usuarios no-root", "FAIL", f"Containers como root: {', '.join(root_containers)}")
                
        except Exception as e:
            self.add_issue("MEDIA", f"No se pudo verificar configuración de Docker: {e}")
    
    def check_security_logs(self):
        """Verifica logs de seguridad"""
        logger.info("🔍 Verificando logs de seguridad...")
        
        try:
            # Verificar que existan logs recientes
            log_files = [
                "logs/security.log",
                "logs/audit.log",
                "logs/access.log"
            ]
            
            existing_logs = []
            for log_file in log_files:
                if os.path.exists(log_file):
                    existing_logs.append(log_file)
            
            if existing_logs:
                self.add_check("✅ Logs de seguridad", "PASS", f"Logs encontrados: {', '.join(existing_logs)}")
            else:
                self.add_issue("MEDIA", "No se encontraron logs de seguridad")
                self.add_check("⚠️ Logs de seguridad", "WARN", "No se encontraron logs de seguridad")
                
        except Exception as e:
            self.add_issue("BAJA", f"No se pudo verificar logs: {e}")
    
    def add_issue(self, severity: str, description: str):
        """Agrega un problema de seguridad"""
        if severity == "CRÍTICA":
            self.audit_results["critical_issues"] += 1
        elif severity == "ALTA":
            self.audit_results["high_issues"] += 1
        elif severity == "MEDIA":
            self.audit_results["medium_issues"] += 1
        elif severity == "BAJA":
            self.audit_results["low_issues"] += 1
    
    def add_check(self, name: str, status: str, description: str):
        """Agrega resultado de verificación"""
        self.audit_results["checks"].append({
            "name": name,
            "status": status,
            "description": description,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def calculate_overall_score(self):
        """Calcula puntuación general de seguridad"""
        total_issues = (
            self.audit_results["critical_issues"] * 10 +
            self.audit_results["high_issues"] * 5 +
            self.audit_results["medium_issues"] * 2 +
            self.audit_results["low_issues"] * 1
        )
        
        # Puntuación base: 100
        # Restar puntos por problemas
        score = max(0, 100 - total_issues)
        self.audit_results["overall_score"] = score
        
        # Clasificar nivel de seguridad
        if score >= 90:
            level = "DIAMANTE"
        elif score >= 80:
            level = "ORO"
        elif score >= 70:
            level = "PLATA"
        elif score >= 60:
            level = "BRONCE"
        else:
            level = "PAPEL MOJADO"
        
        self.audit_results["security_level"] = level
    
    def generate_recommendations(self):
        """Genera recomendaciones de seguridad"""
        recommendations = []
        
        if self.audit_results["critical_issues"] > 0:
            recommendations.append("🚨 CORREGIR INMEDIATAMENTE todas las vulnerabilidades críticas")
        
        if self.audit_results["high_issues"] > 0:
            recommendations.append("⚠️ Resolver vulnerabilidades de alta prioridad en las próximas 24 horas")
        
        if self.audit_results["medium_issues"] > 0:
            recommendations.append("🔧 Planificar corrección de vulnerabilidades medias en la próxima semana")
        
        if self.audit_results["low_issues"] > 0:
            recommendations.append("📝 Documentar y monitorear vulnerabilidades de baja prioridad")
        
        # Recomendaciones generales
        recommendations.extend([
            "🔄 Ejecutar este script diariamente en producción",
            "📊 Monitorear logs de seguridad continuamente",
            "🔐 Rotar contraseñas cada 90 días",
            "🛡️ Implementar HTTPS en producción",
            "🚪 Configurar firewall del sistema operativo"
        ])
        
        self.audit_results["recommendations"] = recommendations
    
    def save_results(self, filename: str = None):
        """Guarda resultados de la auditoría"""
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"security_audit_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.audit_results, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Resultados guardados en: {filename}")
        except Exception as e:
            logger.error(f"Error al guardar resultados: {e}")
    
    def print_summary(self):
        """Imprime resumen de la auditoría"""
        print("\n" + "="*80)
        print("🔐 RESUMEN DE AUDITORÍA DE SEGURIDAD - SISTEMA SENTINEL")
        print("="*80)
        
        print(f"📅 Fecha: {self.audit_results['timestamp']}")
        print(f"🏆 Nivel de Seguridad: {self.audit_results.get('security_level', 'N/A')}")
        print(f"📊 Puntuación General: {self.audit_results['overall_score']}/100")
        print()
        
        print("🚨 PROBLEMAS CRÍTICOS:")
        print(f"   Críticos: {self.audit_results['critical_issues']}")
        print(f"   Altos: {self.audit_results['high_issues']}")
        print(f"   Medios: {self.audit_results['medium_issues']}")
        print(f"   Bajos: {self.audit_results['low_issues']}")
        print()
        
        print("✅ VERIFICACIONES:")
        for check in self.audit_results['checks']:
            status_icon = "✅" if check['status'] == "PASS" else "❌" if check['status'] == "FAIL" else "⚠️"
            print(f"   {status_icon} {check['name']}: {check['description']}")
        print()
        
        print("💡 RECOMENDACIONES:")
        for rec in self.audit_results['recommendations']:
            print(f"   {rec}")
        print()
        
        if self.audit_results['overall_score'] >= 80:
            print("🎉 ¡SISTEMA SEGURO! El nivel de seguridad es aceptable.")
        elif self.audit_results['overall_score'] >= 60:
            print("⚠️ SISTEMA EN RIESGO. Se requieren correcciones urgentes.")
        else:
            print("🚨 SISTEMA COMPLETAMENTE VULNERABLE. NO DESPLEGAR EN PRODUCCIÓN.")
        
        print("="*80)

def main():
    """Función principal"""
    print("🔐 AUDITORÍA DE SEGURIDAD AUTOMATIZADA - SISTEMA SENTINEL")
    print("="*60)
    
    try:
        auditor = SecurityAuditor()
        results = auditor.run_full_audit()
        
        # Imprimir resumen
        auditor.print_summary()
        
        # Guardar resultados
        auditor.save_results()
        
        # Código de salida basado en problemas críticos
        if results["critical_issues"] > 0:
            sys.exit(1)  # Error crítico
        elif results["high_issues"] > 0:
            sys.exit(2)  # Advertencia alta
        else:
            sys.exit(0)  # Éxito
            
    except KeyboardInterrupt:
        print("\n❌ Auditoría interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error fatal durante la auditoría: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
