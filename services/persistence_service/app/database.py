import os
import sqlite3
from contextlib import contextmanager
from typing import Dict, Iterable, List, Optional, Tuple

import psycopg2
import psycopg2.extras


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./persistence.db")


def _is_postgres() -> bool:
    return DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")


def _sqlite_path() -> str:
    # sqlite:///./persistence.db -> ./persistence.db
    if DATABASE_URL.startswith("sqlite///"):
        return DATABASE_URL[len("sqlite///") :]
    if DATABASE_URL.startswith("sqlite:///"):
        return DATABASE_URL[len("sqlite:///") :]
    if DATABASE_URL.startswith("sqlite://"):
        return DATABASE_URL[len("sqlite://") :]
    return "./persistence.db"


@contextmanager
def get_connection():
    if _is_postgres():
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        path = _sqlite_path()
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            conn.execute("PRAGMA foreign_keys=ON;")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_db() -> None:
    if _is_postgres():
        create_raw = """
        CREATE TABLE IF NOT EXISTS raw_incidents (
            id SERIAL PRIMARY KEY,
            document_id VARCHAR(64) NOT NULL,
            row_index INTEGER NOT NULL,
            source_path TEXT,
            col_a TEXT, col_b TEXT, col_c TEXT, col_d TEXT, col_e TEXT, col_f TEXT, col_g TEXT, col_h TEXT,
            col_i TEXT, col_j TEXT, col_k TEXT, col_l TEXT, col_m TEXT, col_n TEXT, col_o TEXT, col_p TEXT, col_q TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_raw_document_row UNIQUE (document_id, row_index)
        );
        CREATE INDEX IF NOT EXISTS ix_raw_document_row ON raw_incidents(document_id, row_index);
        """
        create_classified = """
        CREATE TABLE IF NOT EXISTS classified_incidents (
            id SERIAL PRIMARY KEY,
            document_id VARCHAR(64) NOT NULL,
            raw_incident_id INTEGER NOT NULL REFERENCES raw_incidents(id) ON DELETE CASCADE,
            col_r TEXT, col_s TEXT, col_t TEXT, col_u TEXT, col_v TEXT, col_w TEXT, col_x TEXT, col_y TEXT, col_z TEXT,
            col_aa TEXT, col_ab TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_classified_raw UNIQUE (raw_incident_id)
        );
        CREATE INDEX IF NOT EXISTS ix_classified_document_raw ON classified_incidents(document_id, raw_incident_id);
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_raw)
                cur.execute(create_classified)
    else:
        create_raw = """
        CREATE TABLE IF NOT EXISTS raw_incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT NOT NULL,
            row_index INTEGER NOT NULL,
            source_path TEXT,
            col_a TEXT, col_b TEXT, col_c TEXT, col_d TEXT, col_e TEXT, col_f TEXT, col_g TEXT, col_h TEXT,
            col_i TEXT, col_j TEXT, col_k TEXT, col_l TEXT, col_m TEXT, col_n TEXT, col_o TEXT, col_p TEXT, col_q TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            CONSTRAINT uq_raw_document_row UNIQUE (document_id, row_index)
        );
        CREATE INDEX IF NOT EXISTS ix_raw_document_row ON raw_incidents(document_id, row_index);
        """
        create_classified = """
        CREATE TABLE IF NOT EXISTS classified_incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT NOT NULL,
            raw_incident_id INTEGER NOT NULL,
            col_r TEXT, col_s TEXT, col_t TEXT, col_u TEXT, col_v TEXT, col_w TEXT, col_x TEXT, col_y TEXT, col_z TEXT,
            col_aa TEXT, col_ab TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            CONSTRAINT uq_classified_raw UNIQUE (raw_incident_id),
            FOREIGN KEY (raw_incident_id) REFERENCES raw_incidents(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS ix_classified_document_raw ON classified_incidents(document_id, raw_incident_id);
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.executescript(create_raw)
            cur.executescript(create_classified)


def insert_raw_incident(document_id: str, row_index: int, source_path: Optional[str], values_a_q: List[Optional[str]]) -> None:
    if _is_postgres():
        sql = (
            "INSERT INTO raw_incidents (document_id, row_index, source_path, col_a, col_b, col_c, col_d, col_e, col_f, col_g, col_h, col_i, col_j, col_k, col_l, col_m, col_n, col_o, col_p, col_q) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
        )
        params = [document_id, row_index, source_path] + values_a_q
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
    else:
        sql = (
            "INSERT OR IGNORE INTO raw_incidents (document_id, row_index, source_path, col_a, col_b, col_c, col_d, col_e, col_f, col_g, col_h, col_i, col_j, col_k, col_l, col_m, col_n, col_o, col_p, col_q) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        )
        params = [document_id, row_index, source_path] + values_a_q
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)


def fetch_unclassified_chunk(document_id: str, limit: int) -> List[Dict]:
    if _is_postgres():
        sql = (
            "SELECT r.* FROM raw_incidents r WHERE r.document_id=%s AND NOT EXISTS (SELECT 1 FROM classified_incidents c WHERE c.raw_incident_id=r.id) "
            "ORDER BY r.row_index ASC LIMIT %s"
        )
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, (document_id, limit))
                rows = cur.fetchall()
                return [dict(row) for row in rows]
    else:
        sql = (
            "SELECT r.* FROM raw_incidents r WHERE r.document_id=? AND NOT EXISTS (SELECT 1 FROM classified_incidents c WHERE c.raw_incident_id=r.id) "
            "ORDER BY r.row_index ASC LIMIT ?"
        )
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(sql, (document_id, limit))
            return [dict(row) for row in cur.fetchall()]


def insert_classified_items(document_id: str, items: List[Dict]) -> int:
    """
    Inserta items clasificados en una transacción atómica.
    Si falla cualquier INSERT, se hace ROLLBACK de todo el lote.
    """
    if not items:
        return 0
    
    saved = 0
    
    if _is_postgres():
        sql = (
            "INSERT INTO classified_incidents (document_id, raw_incident_id, col_r, col_s, col_t, col_u, col_v, col_w, col_x, col_y, col_z, col_aa, col_ab) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (raw_incident_id) DO NOTHING"
        )
        
        # Crear conexión manual para control de transacción
        conn = psycopg2.connect(DATABASE_URL)
        try:
            with conn.cursor() as cur:
                # Iniciar transacción
                cur.execute("BEGIN")
                
                for it in items:
                    params = (
                        document_id,
                        it["raw_incident_id"],
                        it.get("col_r"), it.get("col_s"), it.get("col_t"), it.get("col_u"), it.get("col_v"),
                        it.get("col_w"), it.get("col_x"), it.get("col_y"), it.get("col_z"), it.get("col_aa"), it.get("col_ab"),
                    )
                    cur.execute(sql, params)
                    saved += cur.rowcount and 1 or 0
                
                # Commit de toda la transacción
                conn.commit()
                
        except Exception as e:
            # ROLLBACK automático en caso de error
            conn.rollback()
            raise Exception(f"Error en transacción atómica: {str(e)}. Se hizo ROLLBACK de {len(items)} items.")
        finally:
            conn.close()
            
    else:
        sql = (
            "INSERT OR IGNORE INTO classified_incidents (document_id, raw_incident_id, col_r, col_s, col_t, col_u, col_v, col_w, col_x, col_y, col_z, col_aa, col_ab) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
        )
        
        # Crear conexión manual para control de transacción
        path = _sqlite_path()
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            conn.execute("PRAGMA foreign_keys=ON;")
            cur = conn.cursor()
            
            # Iniciar transacción
            cur.execute("BEGIN TRANSACTION")
            
            for it in items:
                params = (
                    document_id,
                    it["raw_incident_id"],
                    it.get("col_r"), it.get("col_s"), it.get("col_t"), it.get("col_u"), it.get("col_v"),
                    it.get("col_w"), it.get("col_x"), it.get("col_y"), it.get("col_z"), it.get("col_aa"), it.get("col_ab"),
                )
                cur.execute(sql, params)
                saved += 1 if cur.rowcount else 0
            
            # Commit de toda la transacción
            conn.commit()
            
        except Exception as e:
            # ROLLBACK automático en caso de error
            conn.rollback()
            raise Exception(f"Error en transacción atómica: {str(e)}. Se hizo ROLLBACK de {len(items)} items.")
        finally:
            conn.close()
    
    return saved


def fetch_raws(document_id: str) -> List[Dict]:
    if _is_postgres():
        sql = "SELECT * FROM raw_incidents WHERE document_id=%s ORDER BY row_index ASC"
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, (document_id,))
                return [dict(r) for r in cur.fetchall()]
    else:
        sql = "SELECT * FROM raw_incidents WHERE document_id=? ORDER BY row_index ASC"
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(sql, (document_id,))
            return [dict(r) for r in cur.fetchall()]


def fetch_classified_map(document_id: str) -> Dict[int, Dict]:
    if _is_postgres():
        sql = "SELECT * FROM classified_incidents WHERE document_id=%s"
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, (document_id,))
                rows = cur.fetchall()
                return {int(r["raw_incident_id"]): dict(r) for r in rows}
    else:
        sql = "SELECT * FROM classified_incidents WHERE document_id=?"
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(sql, (document_id,))
            rows = cur.fetchall()
            return {int(r["raw_incident_id"]): dict(r) for r in rows}


