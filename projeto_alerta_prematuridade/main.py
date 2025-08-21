from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)