from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
from datetime import datetime    # ← ADICIONAR ESTA LINHA
from typing import Optional      # ← ADICIONAR ESTA LINHA

app = FastAPI(
    title="Sistema de Alerta Prematuro (SAP)",
    description="Conecta famílias de prematuros a ONGs de apoio",
    version="0.1.0"
)

class AlertaPrematuro(BaseModel):
    municipio: str
    semanas_gestacao: int
    hospital: str
    data_nascimento: date
    consentimento: bool = True

# ← AQUI ADICIONAR A NOVA CLASSE RNDSBirthNotification
class RNDSBirthNotification(BaseModel):
    """Simulação de notificação RNDS - formato FHIR simplificado"""
    resource_type: str = "Patient"
    birth_date: str
    gestational_age_weeks: int
    birth_weight_grams: Optional[int] = None
    hospital_identifier: str  # Código CNES
    municipality_code: str    # Código IBGE
    consent_data_sharing: bool
    timestamp: str
    notification_id: Optional[str] = None

ONGS_SP = [
    {
        "nome": "ONG Prematuridade.com",
        "email": "contato@prematuridade.com",
        "municipios": ["São Paulo", "Santo André", "São Bernardo"],
        "telefone": "(11) 99999-0000"
    },
    {
        "nome": "Viver e Sorrir - UNIFESP",
        "email": "viversorrir@unifesp.br",
        "municipios": ["São Paulo"],
        "telefone": "(11) 88888-0000"
    }
]

# ← AQUI ADICIONAR AS FUNÇÕES AUXILIARES
def obter_nome_municipio(codigo_ibge: str) -> str:
    """Converte código IBGE para nome município"""
    municipios = {
        "3550308": "São Paulo",
        "3304557": "Rio de Janeiro", 
        "3106200": "Belo Horizonte",
        "4106902": "Curitiba",
        "2927408": "Salvador",
        "2611606": "Recife"
    }
    return municipios.get(codigo_ibge, f"Município {codigo_ibge}")

def calcular_urgencia(semanas: int) -> str:
    """Calcula urgência baseado na prematuridade"""
    if semanas < 28:
        return "EXTREMA"  # Prematuro extremo
    elif semanas < 32:
        return "ALTA"     # Muito prematuro
    elif semanas < 37:
        return "MÉDIA"    # Prematuro limítrofe
    else:
        return "BAIXA"    # Termo

@app.get("/")
def home():
    return {
        "sistema": "Sistema de Alerta Prematuro (SAP)",
        "status": "funcionando",
        "ongs_cadastradas": len(ONGS_SP),
        "version": "0.1.0"
    }

@app.post("/alerta")
def receber_alerta(alerta: AlertaPrematuro):
    if alerta.semanas_gestacao >= 37:
        return {"status": "ignorado", "motivo": "não é prematuro"}
    if not alerta.consentimento:
        return {"status": "ignorado", "motivo": "sem consentimento"}

    ongs_encontradas = [
        ong for ong in ONGS_SP
        if alerta.municipio in ong["municipios"]
    ]

    for ong in ongs_encontradas:
        print(f"🚨 ALERTA ENVIADO PARA: {ong['nome']}")
        print(f"   📧 Email: {ong['email']}")
        print(f"   📍 Local: {alerta.municipio}")
        print(f"   ⏱️  {alerta.semanas_gestacao} semanas gestação")
        print(f"   🏥 Hospital: {alerta.hospital}")
        print(f"   📞 Contato: {ong['telefone']}")
        print("-" * 50)

    return {
        "status": "sucesso",
        "ongs_notificadas": len(ongs_encontradas),
        "detalhes": [ong["nome"] for ong in ongs_encontradas]
    }

@app.get("/test")
def testar_sistema():
    alerta_teste = AlertaPrematuro(
        municipio="São Paulo",
        semanas_gestacao=34,
        hospital="Hospital Municipal Test",
        data_nascimento=date.today(),
        consentimento=True
    )
    return receber_alerta(alerta_teste)

@app.get("/ongs")
def listar_ongs():
    return {"ongs": ONGS_SP, "total": len(ONGS_SP)}

# ← AQUI ADICIONAR OS NOVOS ENDPOINTS RNDS
@app.post("/rnds/webhook")
def receber_notificacao_rnds(notificacao: RNDSBirthNotification):
    """
    Simula webhook que receberia notificação da RNDS
    sobre nascimento prematuro
    """
    print("🔔 NOTIFICAÇÃO RNDS RECEBIDA (SIMULADA)")
    print("=" * 50)
    print(f"   📅 Data: {notificacao.birth_date}")
    print(f"   ⏱️  Gestação: {notificacao.gestational_age_weeks} semanas")
    print(f"   🏥 Hospital: {notificacao.hospital_identifier}")
    print(f"   📍 Município: {obter_nome_municipio(notificacao.municipality_code)}")
    print(f"   ⚖️  Peso: {notificacao.birth_weight_grams}g" if notificacao.birth_weight_grams else "   ⚖️  Peso: não informado")
    print(f"   ✅ Consentimento: {'SIM' if notificacao.consent_data_sharing else 'NÃO'}")
    print(f"   🆔 ID: {notificacao.notification_id}")
    
    # Verificar se é realmente prematuro
    if notificacao.gestational_age_weeks >= 37:
        print("   ℹ️  STATUS: Ignorado - não é prematuro")
        return {
            "status": "ignored", 
            "reason": "not_premature",
            "gestational_weeks": notificacao.gestational_age_weeks
        }
    
    # Verificar consentimento
    if not notificacao.consent_data_sharing:
        print("   ℹ️  STATUS: Ignorado - sem consentimento")
        return {
            "status": "ignored", 
            "reason": "no_consent"
        }
    
    # Converter para formato do sistema atual
    alerta = AlertaPrematuro(
        municipio=obter_nome_municipio(notificacao.municipality_code),
        semanas_gestacao=notificacao.gestational_age_weeks,
        hospital=f"Hospital CNES: {notificacao.hospital_identifier}",
        data_nascimento=datetime.fromisoformat(notificacao.birth_date).date(),
        consentimento=notificacao.consent_data_sharing
    )
    
    # Processar normalmente
    resultado = receber_alerta(alerta)
    
    urgencia = calcular_urgencia(notificacao.gestational_age_weeks)
    
    print(f"   🚨 URGÊNCIA: {urgencia}")
    print("=" * 50)
    
    return {
        "status": "processed",
        "rnds_notification_id": notificacao.notification_id,
        "urgency_level": urgencia,
        "municipality": obter_nome_municipio(notificacao.municipality_code),
        "sap_result": resultado,
        "processing_timestamp": datetime.now().isoformat()
    }

@app.post("/test/simular-rnds")
def simular_notificacao_rnds():
    """Endpoint para simular notificação RNDS"""
    notificacao_simulada = RNDSBirthNotification(
        birth_date="2025-08-21",
        gestational_age_weeks=34,        # PREMATURO!
        birth_weight_grams=2100,
        hospital_identifier="2077469",    # CNES Hospital São Paulo
        municipality_code="3550308",      # São Paulo IBGE
        consent_data_sharing=True,       # Família autorizou
        timestamp=datetime.now().isoformat(),
        notification_id=f"RNDS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    
    return receber_notificacao_rnds(notificacao_simulada)

@app.post("/test/simular-rnds-extremo")
def simular_rnds_extremo():
    """Simula caso de prematuridade extrema"""
    notificacao_extrema = RNDSBirthNotification(
        birth_date="2025-08-21",
        gestational_age_weeks=26,        # EXTREMO!
        birth_weight_grams=850,
        hospital_identifier="2077469",
        municipality_code="3550308",
        consent_data_sharing=True,
        timestamp=datetime.now().isoformat(),
        notification_id=f"RNDS-EXTREMO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    
    return receber_notificacao_rnds(notificacao_extrema)

@app.get("/test/simular-multiplos")
def simular_multiplos_nascimentos():
    """Simula múltiplos nascimentos para teste"""
    casos = [
        {"semanas": 36, "peso": 2400, "municipio": "3550308", "urgencia": "MÉDIA"},
        {"semanas": 30, "peso": 1200, "municipio": "3304557", "urgencia": "ALTA"},
        {"semanas": 25, "peso": 750, "municipio": "3106200", "urgencia": "EXTREMA"}
    ]
    
    resultados = []
    for caso in casos:
        notificacao = RNDSBirthNotification(
            birth_date="2025-08-21",
            gestational_age_weeks=caso["semanas"],
            birth_weight_grams=caso["peso"],
            hospital_identifier="2077469",
            municipality_code=caso["municipio"],
            consent_data_sharing=True,
            timestamp=datetime.now().isoformat(),
            notification_id=f"RNDS-MULTI-{len(resultados)+1}"
        )
        
        resultado = receber_notificacao_rnds(notificacao)
        resultados.append(resultado)
    
    return {
        "total_notifications": len(resultados),
        "results": resultados,
        "summary": f"Processados {len(resultados)} casos simulados"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
