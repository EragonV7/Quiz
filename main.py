from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

app = FastAPI()

# Configuração do CORS para aceitar requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexão com o Supabase
SUPABASE_URL = "https://azqtgvonviekeivefqde.supabase.co"
SUPABASE_KEY = "sb_publishable_U-C_YPVKJL48zEPdaQQGeg_nrE_F3Jm"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.post("/calcular-pontuacao")
def calcular_pontuacao(pergunta_id: str, alternativa_correta: str):
    jogadores = supabase.table("jogadores").select("*").execute().data
    respostas = supabase.table("respostas_rodada").select("*").eq("pergunta_id", pergunta_id).execute().data

    N = len(jogadores)
    respostas_map = {r["jogador_id"]: r for r in respostas}
    
    acertos = sum(1 for r in respostas if r["alternativa"] == alternativa_correta)
    A = acertos
    
    pontos_base = 0
    if 0 < A < N:
        pontos_base = (N - A) + 1

    jogadores_ordenados = sorted(jogadores, key=lambda x: x["pontuacao_total"])
    primeiro_lugar_id = jogadores_ordenados[-1]["id"] if jogadores else None
    ultimo_lugar_id = jogadores_ordenados[0]["id"] if jogadores else None

    saldo_pontos = {j["id"]: 0 for j in jogadores}

    if A == 0 and ultimo_lugar_id:
        saldo_pontos[ultimo_lugar_id] += 1
    
    elif A > 0 and A < N:
        for j_id, resposta in respostas_map.items():
            acertou = (resposta["alternativa"] == alternativa_correta)
            buff = resposta["buff_usado"]

            if acertou:
                if buff == "dobro_ou_nada":
                    saldo_pontos[j_id] += (pontos_base * 2)
                elif buff == "vampiro":
                    saldo_pontos[j_id] += (pontos_base + 1)
                    if primeiro_lugar_id and primeiro_lugar_id != j_id:
                        saldo_pontos[primeiro_lugar_id] -= 1
                elif buff == "maria":
                    saldo_pontos[j_id] += (pontos_base // 2)
                else:
                    saldo_pontos[j_id] += pontos_base
            else:
                if buff == "dobro_ou_nada":
                    saldo_pontos[j_id] -= 2
                elif buff == "escudo":
                    saldo_pontos[j_id] += 1
                
    for jogador in jogadores:
        j_id = jogador["id"]
        if saldo_pontos[j_id] != 0:
            nova_pontuacao = max(0, jogador["pontuacao_total"] + saldo_pontos[j_id])
            supabase.table("jogadores").update({"pontuacao_total": nova_pontuacao}).eq("id", j_id).execute()

    return {"status": "sucesso", "acertos": A, "jogadores": N}