# main.py

import os
import sqlite3
import random
from datetime import datetime, timedelta, date
from typing import Optional, List

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from database import init_db, insert_alert  # mantém seu código de banco original

app = FastAPI(
    title="Sistema de Alerta Prematuro (SAP)",
    description="Conecta famílias de prematuros a ONGs de apoio em 24 horas",
    version="1.0.3"
)

#
# CONFIGURAÇÃO DO BANCO LOCAL
#
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "alertas.db")

#
# MODELOS Pydantic
#
class Alerta(BaseModel):
    id: int
    municipio: str
    semanas: int
    urgencia: str
    timestamp: datetime
    hospital: Optional[str]
    data_nascimento: date

class AlertasResponse(BaseModel):
    alertas: List[Alerta]
    total: int
    filtros_aplicados: dict
    timestamp: datetime

#
# FUNÇÕES ETL PARA POPULAR ALERTAS EXEMPLO
#
def create_sample_alerts(n=50):
    municipios = ["São Paulo","Rio de Janeiro","Belo Horizonte","Salvador","Curitiba"]
    urgencias  = ["EXTREMA","ALTA","MÉDIA","BAIXA"]
    hospitais  = ["Hospital A","Hospital B","Hospital C"]
    alertas = []
    for _ in range(n):
        dt = datetime.now() - timedelta(days=random.randint(0,30))
        alertas.append({
            "municipio": random.choice(municipios),
            "semanas": random.randint(24,36),
            "urgencia": random.choice(urgencias),
            "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "hospital": random.choice(hospitais),
            "data_nascimento": dt.strftime("%Y-%m-%d")
        })
    return alertas

def save_to_database(alertas, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Cria tabela se não existir
    c.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            municipio TEXT,
            semanas INTEGER,
            urgencia TEXT,
            timestamp TEXT,
            hospital TEXT,
            data_nascimento TEXT
        )
    """)
    # Limpa dados anteriores
    c.execute("DELETE FROM alertas")
    # Insere novos alertas
    for a in alertas:
        c.execute("""
            INSERT INTO alertas
            (municipio,semanas,urgencia,timestamp,hospital,data_nascimento)
            VALUES (?,?,?,?,?,?)
        """, (
            a["municipio"],
            a["semanas"],
            a["urgencia"],
            a["timestamp"],
            a["hospital"],
            a["data_nascimento"]
        ))
    conn.commit()
    conn.close()
    print(f"✅ Banco populado com {len(alertas)} alertas em {db_path}")

#
# EVENTO DE STARTUP: inicializa DB e popula alertas
#
@app.on_event("startup")
async def startup_event():
    # Popular banco de alertas de exemplo
    sample = create_sample_alerts(50)
    save_to_database(sample)
    # Inicializar esquema original (outras tabelas) se necessário
    await init_db()
    print("🚀 Sistema SAP iniciado, banco pronto")

#
# FUNÇÕES DE CONSULTA
#
def fetch_alerts_from_db(limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM alertas ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def fetch_alerts_filtered(periodo: Optional[str], urgencia: Optional[str], municipio: Optional[str]):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    sql = "SELECT * FROM alertas"
    conds, params = [], []
    if periodo:
        now = datetime.now()
        if periodo=="24h": cutoff = now - timedelta(hours=24)
        elif periodo=="7dias": cutoff = now - timedelta(days=7)
        elif periodo=="mes": cutoff = now - timedelta(days=30)
        elif periodo=="ano": cutoff = now - timedelta(days=365)
        else: raise HTTPException(400,"Período inválido")
        conds.append("timestamp>=?")
        params.append(cutoff.strftime("%Y-%m-%d %H:%M:%S"))
    if urgencia:
        conds.append("urgencia=?")
        params.append(urgencia)
    if municipio:
        conds.append("municipio=?")
        params.append(municipio)
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY timestamp DESC"
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

#
# ENDPOINTS
#
@app.get("/api/alerts", response_model=AlertasResponse)
async def get_alerts(
    periodo: Optional[str] = Query(None, description="24h|7dias|mes|ano"),
    urgencia: Optional[str] = Query(None, description="EXTREMA|ALTA|MÉDIA|BAIXA"),
    municipio: Optional[str] = Query(None)
):
    if periodo or urgencia or municipio:
        data = fetch_alerts_filtered(periodo, urgencia, municipio)
    else:
        data = fetch_alerts_from_db(50)
    return {
        "alertas": data,
        "total": len(data),
        "filtros_aplicados": {"periodo":periodo,"urgencia":urgencia,"municipio":municipio},
        "timestamp": datetime.now()
    }

@app.get("/", response_class=JSONResponse)
def home():
    return {"status":"online","version":"1.0.3"}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(open("dashboard.html","r",encoding="utf-8").read())

# mantenha outros endpoints (simular-rnds, estatisticas) inalterados

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
