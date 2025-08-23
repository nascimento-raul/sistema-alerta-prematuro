from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List
import random
from database import init_db, insert_alert, get_alerts, get_alerts_filtered

app = FastAPI(
    title="Sistema de Alerta Prematuro (SAP)",
    description="Conecta famílias de prematuros a ONGs de apoio em 24 horas",
    version="1.0.3"
)

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
        "endpoints":["/dashboard","/test/simular-rnds","/estatisticas","/docs"]
    }

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open("dashboard.html","r",encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

from fastapi import Query

@app.get("/api/alerts", response_class=JSONResponse)
async def get_alertas(
    periodo: Optional[str] = Query(None, description="Filtro por período: 24h, 7dias, mes, ano"),
    urgencia: Optional[str] = Query(None, description="Filtro por urgência: EXTREMA, ALTA, MÉDIA, BAIXA"),
    municipio: Optional[str] = Query(None, description="Filtro por município")
):
    if periodo or urgencia or municipio:
        # Usar filtros
        alertas = await get_alerts_filtered(periodo=periodo, urgencia=urgencia, municipio=municipio, limit=50)
    else:
        # Sem filtros - todos os dados
        alertas = await get_alerts(50)
    
    return {
        "alertas": alertas,
        "total": len(alertas),
        "filtros_aplicados": {
            "periodo": periodo,
            "urgencia": urgencia, 
            "municipio": municipio
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/test/simular-rnds", response_class=JSONResponse)
async def simular_notificacao_rnds():
    semanas = random.randint(24,40)
    peso = random.randint(800,3500)
    municipio = random.choice(["3550308","3304557","3106200","4106902","2927408"])
    notificacao = RNDSBirthNotification(
        birth_date=date.today().isoformat(),
        gestational_age_weeks=semanas,
        birth_weight_grams=peso,
        hospital_identifier="2077469",
        municipality_code=municipio,
        consent_data_sharing=True,
        timestamp=datetime.now().isoformat(),
        notification_id=f"RNDS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    nivel,_,_ = calcular_urgencia(semanas)
    alerta = {
    "municipio":obter_nome_municipio(municipio),
    "semanas":semanas,
    "hospital":f"Hospital CNES {notificacao.hospital_identifier}",
    "data_nascimento":notificacao.birth_date,
    "timestamp":notificacao.timestamp,
    "urgency":nivel  # ← AQUI: urgency (Python) vira urgencia (SQL)
    }
    
    # Salvar no banco E na memória
    await insert_alert(alerta)
    alertas_historico.append(alerta)
    
    return {
        "status":"processed",
        "notification_id":notificacao.notification_id,
        "urgency":nivel,
        "municipality":alerta["municipio"],
        "processing_time":"<1 segundo",
        "ong_notificada":"ONG Prematuridade.com"
    }

@app.get("/estatisticas", response_class=JSONResponse)
def estatisticas_sistema():
    hoje = date.today().isoformat()
    cont = len([a for a in alertas_historico if a["timestamp"].startswith(hoje)])
    return {
        "prematuridade_brasil":{"taxa_anual":"11,1%","nascimentos_ano":"300k-340k","posicao_mundial":"10º","custo_sus_anual":"R$8-15bi"},
        "ong":ONGS_SP[0],
        "sap":{"alertas_hoje":cont,"tempo_resposta":"<500ms","uptime":"99.9%","compliance_lgpd":True}
    }

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=8000)
