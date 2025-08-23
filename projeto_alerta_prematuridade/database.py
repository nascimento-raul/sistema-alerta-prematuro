import aiosqlite
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any

DATABASE_FILE = "alertas.db"

async def init_db():
    """Inicializa o banco de dados e cria a tabela se não existir"""
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                municipio TEXT NOT NULL,
                semanas INTEGER NOT NULL,
                urgencia TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                hospital TEXT NOT NULL,
                data_nascimento TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    print("✅ Banco de dados inicializado")

async def insert_alert(alerta_data: Dict[str, Any]) -> int:
    async with aiosqlite.connect(DATABASE_FILE) as db:
        cursor = await db.execute("""
            INSERT INTO alertas (municipio, semanas, urgencia, timestamp, hospital, data_nascimento)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            alerta_data["municipio"],
            alerta_data["semanas"], 
            alerta_data["urgency"],  # ← Python usa "urgency"
            alerta_data["timestamp"],
            alerta_data["hospital"],
            alerta_data["data_nascimento"]
        ))
        await db.commit()
        return cursor.lastrowid

async def get_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DATABASE_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT municipio, semanas, urgencia as urgency, timestamp, hospital, data_nascimento
            FROM alertas 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_alerts_filtered(periodo: Optional[str] = None, 
                            urgencia: Optional[str] = None,
                            municipio: Optional[str] = None,
                            limit: int = 50) -> List[Dict[str, Any]]:
    """Retorna alertas filtrados do banco de dados"""
    query = "SELECT municipio, semanas, urgencia as urgency, timestamp, hospital, data_nascimento FROM alertas WHERE 1=1"
    params = []
    
    if periodo:
        if periodo == "24h":
            query += " AND datetime(timestamp) >= datetime('now', '-1 day')"
        elif periodo == "7dias":
            query += " AND datetime(timestamp) >= datetime('now', '-7 days')"
        elif periodo == "mes":
            query += " AND datetime(timestamp) >= datetime('now', '-1 month')"
        elif periodo == "ano":
            query += " AND datetime(timestamp) >= datetime('now', '-1 year')"
    
    if urgencia:
        query += " AND urgencia = ?"
        params.append(urgencia)
    
    if municipio:
        query += " AND municipio = ?"
        params.append(municipio)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    async with aiosqlite.connect(DATABASE_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
