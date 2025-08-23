# Sistema de Alerta Precoce de Prematuridade

Projeto em FastAPI que coleta dados SINASC, gera alertas de prematuridade e disponibiliza filtros via API.

---

## 1. Deploy no Railway

1. Crie uma conta em https://railway.app e instale o CLI:

npm install -g railway

2. No terminal, dentro da pasta do projeto, execute: railway up ou conecte o repositório GitHub pelo Dashboard do Railway.

3. Em **Settings → Variables** do Railway, adicione:


PYTHON_VERSION = 3.9


4. Certifique-se de que o `requirements.txt` contenha apenas:


fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
aiosqlite==0.18.0

5. Para forçar rebuild, faça:


git add requirements.txt
git commit -m "Force rebuild: ajustar dependências Railway"
git push origin main

6. Aguarde o novo deploy e abra a URL de produção fornecida pelo Railway.

---

## 2. Como Usar a Swagger UI

1. No navegador, abra: https://<SEU-RAILWAY-URL>/docs
2. Encontre o endpoint **GET /api/alerts** e clique para expandir.
3. Preencha os filtros:
- `periodo`: `24h` | `7dias` | `mes` | `ano`
- `urgencia`: `EXTREMA` | `ALTA` | `MÉDIA` | `BAIXA`
- `municipio`: `São Paulo` | `Rio de Janeiro` | `Belo Horizonte` | `Curitiba` | `Salvador`
4. Clique em **Execute** e observe o JSON de resposta.

---

## 3. Tag de Release

Depois de testar e validar tudo, crie e publique a tag de versão:

git tag v1.0-deploy
git push origin v1.0-deploy

undefined
