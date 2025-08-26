import json
from pathlib import Path
from typing import Dict, Any, List

BASE = Path(__file__).resolve().parents[2]  # raíz del repo
CONFIG_DIR = BASE / "config"


def load_rules():
    dicc = json.loads((CONFIG_DIR / "diccionario_policial.json").read_text(encoding="utf-8"))
    criterios = (CONFIG_DIR / "criterios.txt").read_text(encoding="utf-8").splitlines()
    return dicc, criterios


def classify_rows(rows: List[Dict[str, Any]], strategy: str = "rules") -> List[Dict[str, Any]]:
    """
    Clasifica filas usando algoritmo de puntuación por coincidencias múltiples.
    Evalúa TODOS los delitos del diccionario y elige el que tenga más coincidencias.
    """
    dicc, criterios = load_rules()
    out = []
    
    for row in rows:
        texto = " ".join([str(v) for v in row.values() if isinstance(v, (str, int, float))]).lower()
        
        # Sistema de puntuación para cada delito
        delito_scores = {}
        
        # Evaluar cada delito del diccionario
        for delito_info in dicc.get("delitos", []):
            calificacion = delito_info.get("calificacion", "")
            modalidades = delito_info.get("modalidades", [])
            
            # Puntuación base del delito principal
            score = 0
            for keyword in [calificacion.lower()] + [word.lower() for word in calificacion.split()]:
                if keyword in texto:
                    score += 2  # Puntuación alta por coincidencia exacta
            
            # Evaluar modalidades específicas
            for modalidad in modalidades:
                modalidad_score = 0
                criterios_modalidad = modalidad.get("criterios", [])
                
                for criterio in criterios_modalidad:
                    if criterio.lower() in texto:
                        modalidad_score += 1
                
                # Si hay modalidad específica, dar bonus
                if modalidad_score > 0:
                    score += modalidad_score * 1.5
                    break  # Solo una modalidad por delito
            
            # Guardar puntuación del delito
            if score > 0:
                delito_scores[calificacion] = {
                    "score": score,
                    "modalidades": modalidades,
                    "base_legal": delito_info.get("base_legal", "")
                }
        
        # Elegir el delito con mayor puntuación
        categoria = None
        subtipo = None
        observaciones = None
        
        if delito_scores:
            # Ordenar por puntuación descendente
            mejor_delito = max(delito_scores.items(), key=lambda x: x[1]["score"])
            delito_nombre, delito_info = mejor_delito
            
            # Solo clasificar si la puntuación es suficientemente alta
            if delito_info["score"] >= 2:  # Umbral mínimo de confianza
                categoria = delito_nombre
                
                # Buscar modalidad específica si existe
                for modalidad in delito_info["modalidades"]:
                    modalidad_score = 0
                    for criterio in modalidad.get("criterios", []):
                        if criterio.lower() in texto:
                            modalidad_score += 1
                    
                    if modalidad_score > 0:
                        subtipo = modalidad.get("nombre")
                        break
                
                observaciones = f"Clasificado por reglas (puntuación: {delito_info['score']})"
            else:
                observaciones = f"Puntuación insuficiente para clasificación automática ({delito_info['score']})"
        else:
            observaciones = "No se encontraron coincidencias en el diccionario"
        
        out.append({
            "row_id": row.get("row_id"),
            "categoria": categoria,
            "subtipo": subtipo,
            "observaciones": observaciones,
        })
    
    return out
