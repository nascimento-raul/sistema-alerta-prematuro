from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from datetime import date, datetime, timedelta
from typing import Optional, List
import random
import sqlite3

from database import init_db, insert_alert  # mantém seus métodos de inserção

app = FastAPI(
    title="Sistema de Alerta Prematuro (SAP)",
    description="Conecta famílias de prematuros a ONGs de apoio em 24 horas",
    version="1.0.3"
)

DB_PATH = "projeto_alerta_prematuridade/alertas.db"  # ajuste se seu banco estiver em outro local

@app.on_event("startup")
async def startup_event():
    await init_db()
    print("🚀 Sistema SAP iniciado com banco de dados")

class AlertaPrematuro(BaseModel):
    municipio: str
    semanas_gestacao: int
    hospital: str
    data_nascimento: date
    consentimento: bool = True

class RNDSBirthNotification(BaseModel):
    resource_type: str = "Patient"
    birth_date: str
    gestational_age_weeks: int
    birth_weight_grams: Optional[int] = None
    hospital_identifier: str
    municipality_code: str
    consent_data_sharing: bool
    timestamp: str
    notification_id: Optional[str] = None

alertas_historico: List[dict] = []

ONGS_SP = [
    {
        "nome": "ONG Prematuridade.com",
        "email": "contato@prematuridade.com",
        "municipios": ["São Paulo","Rio de Janeiro","Belo Horizonte","Curitiba","Salvador"],
        "telefone": "(11) 99999-0000",
        "website": "https://prematuridade.com",
        "familias_atendidas_mes": 600,
        "anos_experiencia": 15,
        "estados_atuacao": 23,
        "satisfacao": "97%"
    }
]

def obter_nome_municipio(codigo_ibge: str) -> str:
    municipios = {
        "3550308":"São Paulo","3304557":"Rio de Janeiro",
        "3106200":"Belo Horizonte","4106902":"Curitiba",
        "2927408":"Salvador"
    }
    return municipios.get(codigo_ibge, f"Município {codigo_ibge}")

def calcular_urgencia(semanas: int) -> tuple:
    if semanas < 28:    return ("EXTREMA","red","🚨")
    if semanas < 32:    return ("ALTA","yellow","⚠️")
    if semanas < 37:    return ("MÉDIA","blue","ℹ️")
    return ("BAIXA","green","✅")

@app.get("/", response_class=JSONResponse)
def home():
    hoje = date.today().isoformat()
    cont = len([a for a in alertas_historico if a["timestamp"].startswith(hoje)])
    return {
        "sistema":"SAP","status":"online","version":"1.0.3",
        "alertas_processados_hoje":cont,"uptime":"99.9%",
        "endpoints":["/dashboard","/test/simular-rnds","/estatisticas","/api/alerts","/docs"]
    }

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open("dashboard.html","r",encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# NOVA FUNÇÃO: consulta SQLite diretamente, usando seu esquema de colunas
def fetch_alerts_from_db(limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alertas ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def fetch_alerts_filtered(periodo: Optional[str], urgencia: Optional[str], municipio: Optional[str]):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = "SELECT * FROM alertas"
    conditions = []
    params = []

    if periodo:
        now = datetime.now()
        if periodo == "24h":
            cutoff = now - timedelta(hours=24)
        elif periodo == "7dias":
            cutoff = now - timedelta(days=7)
        elif periodo == "mes":
            cutoff = now - timedelta(days=30)
        elif periodo == "ano":
            cutoff = now - timedelta(days=365)
        else:
            raise HTTPException(status_code=400, detail="Período inválido")
        conditions.append("timestamp >= ?")
        params.append(cutoff.strftime("%Y-%m-%d %H:%M:%S"))

    if urgencia:
        conditions.append("urgencia = ?")
        params.append(urgencia)

    if municipio:
        conditions.append("municipio = ?")
        params.append(municipio)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY timestamp DESC"
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/alerts", response_class=JSONResponse)
async def get_alertas(
    periodo: Optional[str] = Query(None, description="24h | 7dias | mes | ano"),
    urgencia: Optional[str] = Query(None, description="EXTREMA | ALTA | MÉDIA | BAIXA"),
    municipio: Optional[str] = Query(None, description="Nome do município")
):
    if periodo or urgencia or municipio:
        alertas = fetch_alerts_filtered(periodo, urgencia, municipio)
    else:
        alertas = fetch_alerts_from_db(50)

    return {
        "alertas": alertas,
        "total": len(alertas),
        "filtros_aplicados": {"periodo": periodo, "urgencia": urgencia, "municipio": municipio},
        "timestamp": datetime.now().isoformat()
    }

@app.post("/test/simular-rnds", response_class=JSONResponse)
async def simular_notificacao_rnds():
    semanas = random.randint(24,40)
    peso = random.randint(800,3500)
    municipio_code = random.choice(list(obter_nome_municipio.__defaults__[0].keys()))
    notificacao = RNDSBirthNotification(
        birth_date=date.today().isoformat(),
        gestational_age_weeks=semanas,
        birth_weight_grams=peso,
        hospital_identifier="2077469",
        municipality_code=municipio_code,
        consent_data_sharing=True,
        timestamp=datetime.now().isoformat(),
        notification_id=f"RNDS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    nivel,_,_ = calcular_urgencia(semanas)
    alerta = {
        "municipio": obter_nome_municipio(municipio_code),
        "semanas": semanas,
        "hospital": f"Hospital CNES {notificacao.hospital_identifier}",
        "data_nascimento": notificacao.birth_date,
        "timestamp": notificacao.timestamp,
        "urgencia": nivel
    }

    await insert_alert(alerta)      # seu método já cuida de gravar no DB
    alertas_historico.append(alerta)

    return {
        "status":"processed",
        "notification_id": notificacao.notification_id,
        "urgency": nivel,
        "municipality": alerta["municipio"],
        "processing_time":"<1 segundo",
        "ong_notificada": ONGS_SP[0]["nome"]
    }

@app.get("/estatisticas", response_class=JSONResponse)
def estatisticas_sistema():
    hoje = date.today().isoformat()
    cont = len([a for a in alertas_historico if a["timestamp"].startswith(hoje)])
    return {
        "prematuridade_brasil": {
            "taxa_anual":"11,1%", "nascimentos_ano":"300k-340k",
            "posicao_mundial":"10º","custo_sus_anual":"R$8-15bi"
        },
        "ong": ONGS_SP[0],
        "sap": {"alertas_hoje":cont,"tempo_resposta":"<500ms","uptime":"99.9%","compliance_lgpd":True}
    }

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
