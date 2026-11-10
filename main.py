import os
import uvicorn
from urllib.parse import quote_plus
import pymongo
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Sistema-de-Gest-o-Escolar-com-Intelig-ncia-Preditiva-TCC-UNIVESP")

# Libera o acesso CORS para web e mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# String de Conexão MongoDB Atlas (Pega da variável de ambiente do Render ou usa a padrão)
MONGO_URI = os.getenv("MONGO_URI", "")

if not MONGO_URI:
    usuario = "mr_gama_jr"
    senha_trata = quote_plus("6348Seg@")
    MONGO_URI = f"mongodb+srv://{usuario}:{senha_trata}@gama.vfnpqze.mongodb.net/edugestao_db?retryWrites=true&w=majority"

client = pymongo.MongoClient(MONGO_URI)
db = client["edugestao_db"]
collection = db["alunos"]

# Credenciais do Administrador / Gestor Pedagógico
ADMIN_USER = "admin"
ADMIN_PASS = "univesp2026"

# Carga inicial padrão
ALUNOS_INICIAIS = [
    {"id": "1", "name": "Marcos Henrique Higashi", "subject": "Engenharia da Computação", "media": 8.5, "freq": 92.0, "atrasos": 1, "ocorrencias": 0, "risk": "Baixo", "status": "Pendente", "note": ""},
    {"id": "2", "name": "Pedro Henrique Faria Cruz", "subject": "Sistemas de Informação", "media": 4.2, "freq": 65.0, "atrasos": 8, "ocorrencias": 3, "risk": "Alto", "status": "Pendente", "note": ""},
    {"id": "3", "name": "Danilo Felix Portugal", "subject": "Algoritmos e Estrutura de Dados", "media": 5.9, "freq": 78.0, "atrasos": 3, "ocorrencias": 1, "risk": "Médio", "status": "Pendente", "note": ""},
    {"id": "4", "name": "Edson Luiz Nascimento", "subject": "Matemática Discreta", "media": 7.8, "freq": 88.0, "atrasos": 2, "ocorrencias": 0, "risk": "Baixo", "status": "Pendente", "note": ""},
    {"id": "5", "name": "João Veríssimo Ferreira", "subject": "Engenharia da Computação", "media": 3.8, "freq": 58.0, "atrasos": 12, "ocorrencias": 4, "risk": "Alto", "status": "Pendente", "note": ""},
    {"id": "6", "name": "Luiz Silva Gama Júnior", "subject": "Sistemas de Informação", "media": 9.1, "freq": 95.0, "atrasos": 0, "ocorrencias": 0, "risk": "Baixo", "status": "Em Acompanhamento", "note": "Estudante com excelente assiduidade"},
    {"id": "7", "name": "Pedro Henrique Mendes", "subject": "Algoritmos e Estrutura de Dados", "media": 5.2, "freq": 71.0, "atrasos": 5, "ocorrencias": 2, "risk": "Alto", "status": "Pendente", "note": ""},
    {"id": "8", "name": "Reginaldo Egashira", "subject": "Matemática Discreta", "media": 6.8, "freq": 82.0, "atrasos": 2, "ocorrencias": 1, "risk": "Baixo", "status": "Pendente", "note": ""},
    {"id": "9", "name": "Ana Carolina Silva", "subject": "Engenharia da Computação", "media": 4.0, "freq": 61.5, "atrasos": 9, "ocorrencias": 3, "risk": "Alto", "status": "Pendente", "note": ""},
    {"id": "10", "name": "Bruno Castro Souza", "subject": "Sistemas de Informação", "media": 8.2, "freq": 90.0, "atrasos": 1, "ocorrencias": 0, "risk": "Baixo", "status": "Pendente", "note": ""}
]

class Aluno(BaseModel):
    name: str
    subject: str
    media: float
    freq: float
    atrasos: int
    ocorrencias: int
    risk: str = "Pendente"
    status: str = "Pendente"
    note: str = ""

class LoginRequest(BaseModel):
    username: str
    password: str

def calcular_risco(freq: float, media: float, atrasos: int, ocorrencias: int) -> str:
    score = 0
    if freq < 70: score += 40
    elif freq < 75: score += 20

    if media < 5.0: score += 35
    elif media < 6.5: score += 15

    if ocorrencias >= 3: score += 20
    elif ocorrencias >= 1: score += 10

    if atrasos > 5: score += 10

    if score >= 45: return "Alto"
    if score >= 20: return "Médio"
    return "Baixo"

@app.post("/login")
def login_sistema(dados: LoginRequest):
    if dados.username == ADMIN_USER and dados.password == ADMIN_PASS:
        return {"status": "sucesso", "token": "token-sessao-valido-tcc2026", "nome": "Prof. Luiz Gama (Gestor)"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas. Verifique usuário e senha."
    )

@app.get("/alunos")
def listar_alunos():
    if collection.count_documents({}) == 0:
        collection.insert_many(ALUNOS_INICIAIS)
    return list(collection.find({}, {"_id": 0}))

@app.post("/alunos")
def criar_aluno(aluno: Aluno):
    aluno_dict = aluno.model_dump() if hasattr(aluno, "model_dump") else aluno.dict()
    aluno_dict["risk"] = calcular_risco(aluno.freq, aluno.media, aluno.atrasos, aluno.ocorrencias)
    aluno_dict["id"] = str(collection.count_documents({}) + 1)
    collection.insert_one(aluno_dict)
    if "_id" in aluno_dict: del aluno_dict["_id"]
    return {"status": "sucesso", "aluno": aluno_dict}

@app.put("/alunos/{aluno_id}")
def atualizar_intervencao(aluno_id: str, dados: dict):
    collection.update_one(
        {"id": aluno_id},
        {"$set": {"note": dados.get("note", ""), "status": "Em Acompanhamento"}}
    )
    return {"status": "atualizado"}

# Bloco de execução local (Fica sempre no final do arquivo)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)