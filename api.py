"""
API REST â€” LottoCV Dashboard
"""
import os, sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    from database.models import init_db, init_apostas, init_orcamento
    init_db()
    init_apostas()
    init_orcamento()
    yield


app = FastAPI(title="LottoCV API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

dashboard_dir = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.exists(dashboard_dir):
    app.mount("/static", StaticFiles(directory=dashboard_dir), name="static")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Dashboard
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/")
def root():
    index = os.path.join(dashboard_dir, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"status": "LottoCV API a funcionar", "docs": "/docs"}


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Jackpot
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/api/jackpot")
def get_jackpot():
    from database.models import obter_jackpot_atual
    toto  = obter_jackpot_atual("totoloto") or {}
    joker = obter_jackpot_atual("joker") or {}
    return {
        "totoloto": {
            "valor":         toto.get("valor", 0),
            "valor_contos":  toto.get("valor", 0) / 1000,
            "concurso":      toto.get("concurso", "â€”"),
            "data_sorteio":  toto.get("data_sorteio", "â€”"),
            "atualizado_em": toto.get("atualizado_em", "â€”"),
        },
        "joker": {
            "valor":         joker.get("valor", 0),
            "valor_contos":  joker.get("valor", 0) / 1000,
            "concurso":      joker.get("concurso", "â€”"),
            "atualizado_em": joker.get("atualizado_em", "â€”"),
        }
    }


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# FrequÃªncias
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/api/frequencias")
def get_frequencias():
    from database.models import obter_historico_totoloto
    from scraper.decision_engine import analisar_frequencias, classificar_numeros
    historico = obter_historico_totoloto(500)
    if not historico:
        return {"numeros": [], "top_quentes": [], "top_frios": [], "total_sorteios": 0}
    freq    = analisar_frequencias(historico)
    classif = classificar_numeros(freq)
    numeros = [
        {
            "numero": n,
            "count":  freq.get(n, 0),
            "tipo":   "quente" if n in classif["quentes"] else "frio" if n in classif["frios"] else "morno"
        }
        for n in range(1, 46)
    ]
    return {
        "numeros":       numeros,
        "top_quentes":   classif["quentes"][:10],
        "top_frios":     classif["frios"][:10],
        "total_sorteios": len(historico),
    }


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# RecomendaÃ§Ã£o
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/api/recomendacao")
def get_recomendacao():
    from scraper.decision_engine import recomendar_estrategia
    return recomendar_estrategia("MES_TOTOLOTO")


@app.get("/api/recomendacao/{modo}")
def get_recomendacao_modo(modo: str):
    from scraper.decision_engine import recomendar_estrategia
    return recomendar_estrategia(modo.upper())


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CombinaÃ§Ãµes
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/api/combinacoes")
def get_combinacoes(n: int = 5, estrategia: str = "equilibrada"):
    from scraper.decision_engine import gerar_multiplas_combinacoes
    return {"combinacoes": gerar_multiplas_combinacoes(n, estrategia), "estrategia": estrategia}


@app.get("/api/combinacoes/{n}")
def get_combinacoes_n(n: int, estrategia: str = "equilibrada"):
    from scraper.decision_engine import gerar_multiplas_combinacoes
    return {"combinacoes": gerar_multiplas_combinacoes(n, estrategia), "estrategia": estrategia, "n": n}


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# HistÃ³rico
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/api/historico")
def get_historico(limite: int = 20):
    from database.models import obter_historico_totoloto
    historico = obter_historico_totoloto(limite)
    return {"sorteios": historico, "total": len(historico)}


@app.get("/api/jackpot/evolucao")
def get_evolucao_jackpot():
    from database.models import get_connection, USE_POSTGRES, _fetchall
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT concurso, data, jackpot FROM totoloto WHERE jackpot > 0 ORDER BY data ASC LIMIT 100")
    rows = _fetchall(cur)
    conn.close()
    return {"evolucao": rows}


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Scraping
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.post("/api/scrape")
def trigger_scrape():
    from scraper.scraper import executar_scraping
    return {"status": "ok", "resultado": executar_scraping()}


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# PrÃ³ximo mÃªs
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/api/proximo-mes")
def get_proximo_mes():
    from scraper.decision_engine import analisar_proximo_mes
    return analisar_proximo_mes()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# BÃªnÃ§Ã£o & BÃ­blia
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/api/bencao")
def get_bencao():
    from scraper.biblia import bencao_completa
    return bencao_completa()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Apostas
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.post("/api/apostas")
def registar_aposta(payload: dict):
    from database.models import salvar_aposta
    nums = payload.get("numeros", [])
    if len(nums) != 6:
        return {"erro": "Precisas de exatamente 6 nÃºmeros."}
    dados = {
        "concurso": payload.get("concurso", ""),
        "jogo":     payload.get("jogo", "totoloto"),
        "n1": nums[0], "n2": nums[1], "n3": nums[2],
        "n4": nums[3], "n5": nums[4], "n6": nums[5],
        "custo": payload.get("custo", 100),
        "nota":  payload.get("nota", ""),
    }
    return {"status": "ok", "id": salvar_aposta(dados)}


@app.get("/api/apostas")
def listar_apostas(limite: int = 20):
    from database.models import obter_apostas
    return {"apostas": obter_apostas(limite)}


@app.post("/api/verificar/{concurso}")
def verificar_concurso(concurso: str):
    from database.models import obter_apostas_por_concurso, atualizar_resultado_aposta, get_connection, obter_jackpot_atual
    from scraper.prizes import verificar_aposta
    conn = get_connection()
    sorteio = conn.execute("SELECT * FROM totoloto WHERE concurso = ?", (concurso,)).fetchone()
    conn.close()
    if not sorteio:
        return {"erro": f"Sorteio {concurso} nÃ£o encontrado."}
    sorteio   = dict(sorteio)
    jp_info   = obter_jackpot_atual("totoloto") or {}
    jp_val    = jp_info.get("valor", 0)
    apostas   = obter_apostas_por_concurso(concurso)
    if not apostas:
        return {"info": f"Sem apostas por verificar para {concurso}."}
    resultados, total_gasto, total_ganho = [], 0, 0
    for aposta in apostas:
        numeros = [aposta[f'n{i}'] for i in range(1, 7)]
        res = verificar_aposta(numeros, sorteio, jp_val)
        atualizar_resultado_aposta(aposta["id"], res["acertos"], res["ganho"])
        total_gasto += aposta["custo"]
        total_ganho += res["ganho"]
        resultados.append({"aposta_id": aposta["id"], "numeros_jogados": numeros, **res})
    return {
        "concurso":            concurso,
        "numeros_sorteados":   [sorteio[f'n{i}'] for i in range(1, 7)],
        "apostas_verificadas": len(resultados),
        "total_gasto":         total_gasto,
        "total_ganho":         total_ganho,
        "lucro_total":         total_ganho - total_gasto,
        "resultados":          resultados,
    }


@app.get("/api/verificar/ultimo")
def verificar_ultimo():
    from database.models import get_connection
    conn = get_connection()
    row = conn.execute("SELECT concurso FROM totoloto ORDER BY data DESC LIMIT 1").fetchone()
    conn.close()
    if not row:
        return {"erro": "Sem sorteios na base de dados."}
    return verificar_concurso(row["concurso"])


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# OrÃ§amento
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/api/orcamento/{mes}")
def get_orcamento(mes: str):
    from database.models import obter_orcamento_mes
    return obter_orcamento_mes(mes)


@app.post("/api/orcamento/gasto")
def post_gasto(payload: dict):
    from database.models import registar_gasto
    from datetime import datetime
    mes   = payload.get("mes", datetime.now().strftime("%Y-%m"))
    valor = float(payload.get("valor", 100))
    desc  = payload.get("descricao", "Aposta")
    return registar_gasto(mes, valor, desc)


@app.delete("/api/orcamento/desfazer/{mes}")
def desfazer_gasto(mes: str):
    from database.models import desfazer_ultimo_gasto
    return desfazer_ultimo_gasto(mes)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# LottoVision IA
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.post("/api/lottovision")
async def lottovision(payload: dict):
    import requests as req
    from dotenv import load_dotenv
    from scraper.decision_engine import recomendar_estrategia
    from database.models import obter_historico_totoloto, obter_jackpot_atual
    from collections import Counter

    load_dotenv()
    api_key  = os.getenv("ANTHROPIC_API_KEY", "")
    mensagem = payload.get("mensagem", "")

    historico = obter_historico_totoloto(100)
    jackpot   = obter_jackpot_atual("totoloto") or {}
    rec       = recomendar_estrategia("MES_TOTOLOTO")

    freq_txt = ""
    if historico:
        todos = []
        for s in historico:
            for c in ['n1','n2','n3','n4','n5','n6']:
                if s.get(c): todos.append(s[c])
        top = Counter(todos).most_common(10)
        freq_txt = ", ".join(f"{n}({c}x)" for n,c in top)

    combos_txt = "\n".join([
        f"Chave {i+1}: {' - '.join(f'{n:02d}' for n in c)}"
        for i, c in enumerate(rec['combinacoes'])
    ])

    system_prompt = f"""Es o LottoVision, assistente inteligente de apostas do LottoCV â€” Jogos Sociais de Cabo Verde.

DADOS ATUAIS:
- Concurso: {jackpot.get('concurso','--')} | Jackpot: {jackpot.get('valor',0)/1000:.0f} contos ECV
- Sorteio: SÃ¡bados Ã s 19h15 (TCV) | Custo: 30 ECV Totoloto + 70 ECV Joker = 100 ECV
- Modo este mÃªs: {rec['modo']} | OrÃ§amento/sorteio: {rec['orcamento_usar']} ECV
- Sorteios analisados: {len(historico)} | NÃºmeros quentes: {rec['numeros_quentes'][:8]}
- NÃºmeros frios: {rec['numeros_frios'][:8]}
COMBINAÃ‡Ã•ES SUGERIDAS:
{combos_txt}

Responde em portuguÃªs. Se pedirem combinaÃ§Ãµes, gera novas e apresenta-as bem formatadas com os nÃºmeros separados por travessÃ£o (ex: 05 - 12 - 21 - 33 - 40 - 44).
Lembra brevemente que lotaria Ã© aleatÃ³ria. MÃ¡ximo 200 palavras. Usa emojis com moderaÃ§Ã£o."""

    try:
        r = req.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "system": system_prompt,
                "messages": [{"role": "user", "content": mensagem}]
            },
            timeout=30
        )
        data = r.json()
        resposta = data.get("content", [{}])[0].get("text", "")
        if not resposta:
            err = data.get("error", {})
            if "credit" in str(err).lower() or "balance" in str(err).lower():
                resposta = "âš ï¸ A tua conta Anthropic nÃ£o tem crÃ©ditos suficientes. Adiciona crÃ©ditos em console.anthropic.com/settings/billing para usar o LottoVision."
            else:
                resposta = f"Erro: {err.get('message', str(data))}"
    except Exception as e:
        resposta = f"âš ï¸ Erro de ligaÃ§Ã£o ao LottoVision: {str(e)}"

    return {"resposta": resposta}

@app.post("/api/seed")
def seed_historico():
    from database.models import salvar_totoloto, atualizar_jackpot
    sorteios = [
        {"concurso":"14/2026","data":"2026-04-04","n1":19,"n2":20,"n3":26,"n4":37,"n5":42,"n6":43,"complementar":None,"jackpot":22500000,"vencedores":0},
        {"concurso":"13/2026","data":"2026-03-28","n1":10,"n2":12,"n3":21,"n4":25,"n5":29,"n6":40,"complementar":None,"jackpot":20000000,"vencedores":0},
        {"concurso":"12/2026","data":"2026-03-21","n1":3,"n2":11,"n3":18,"n4":22,"n5":35,"n6":44,"complementar":None,"jackpot":17000000,"vencedores":0},
        {"concurso":"11/2026","data":"2026-03-14","n1":7,"n2":14,"n3":23,"n4":31,"n5":38,"n6":41,"complementar":None,"jackpot":15000000,"vencedores":0},
        {"concurso":"10/2026","data":"2026-03-07","n1":2,"n2":9,"n3":16,"n4":27,"n5":33,"n6":45,"complementar":None,"jackpot":12000000,"vencedores":0},
        {"concurso":"09/2026","data":"2026-02-28","n1":5,"n2":13,"n3":20,"n4":28,"n5":36,"n6":42,"complementar":None,"jackpot":10000000,"vencedores":0},
        {"concurso":"08/2026","data":"2026-02-21","n1":1,"n2":8,"n3":17,"n4":24,"n5":32,"n6":39,"complementar":None,"jackpot":8000000,"vencedores":0},
        {"concurso":"07/2026","data":"2026-02-14","n1":6,"n2":15,"n3":19,"n4":29,"n5":34,"n6":43,"complementar":None,"jackpot":6000000,"vencedores":0},
        {"concurso":"06/2026","data":"2026-02-07","n1":4,"n2":10,"n3":21,"n4":30,"n5":37,"n6":44,"complementar":None,"jackpot":5000000,"vencedores":0},
        {"concurso":"05/2026","data":"2026-01-31","n1":2,"n2":12,"n3":18,"n4":25,"n5":33,"n6":40,"complementar":None,"jackpot":4000000,"vencedores":0},
    ]
    count = 0
    for s in sorteios:
        if salvar_totoloto(s):
            count += 1
    atualizar_jackpot("totoloto", 22500000, "14/2026", "2026-04-04")
    atualizar_jackpot("joker", 51600000, "14/2026", "2026-04-04")
    return {"status": "ok", "inseridos": count}

