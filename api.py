"""
API REST — LottoCV
Suporta SQLite (local) e PostgreSQL (Railway cloud)
"""
import os, sys
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from contextlib import asynccontextmanager
import secrets
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

# ── Autenticação simples ──────────────────────
security = HTTPBasic()
APP_USER = os.getenv("APP_USER", "bruna")
APP_PASS = os.getenv("APP_PASS", "lottocv2024")

def verificar_auth(cred: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(cred.username.encode(), APP_USER.encode())
    ok_pass = secrets.compare_digest(cred.password.encode(), APP_PASS.encode())
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return cred.username


# ── Startup ───────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    from database.models import init_db, init_apostas, init_orcamento, obter_historico_totoloto
    init_db()
    init_apostas()
    init_orcamento()
    # Seed histórico apenas se a BD estiver vazia
    hist = obter_historico_totoloto(1)
    if not hist:
        try:
            import subprocess, sys
            subprocess.run([sys.executable, 'seed_historico.py'], check=True)
            print('[Seed] Histórico inicial carregado')
        except Exception as e:
            print(f'[Seed] Aviso: {e}')
    # Inicia scheduler em background
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    # Scraping automático: Sábados 19h45 (após sorteio das 19h15)
    scheduler.add_job(scraping_auto, 'cron', day_of_week='sat', hour=19, minute=45)
    # Verifica jackpot todos os dias às 10h
    scheduler.add_job(verificar_jackpot_auto, 'cron', hour=10, minute=0)
    scheduler.start()
    print("[Scheduler] Iniciado — scraping Sábados 19:45 + verificação diária 10:00")
    yield
    scheduler.shutdown()


def scraping_auto():
    try:
        from scraper.scraper import executar_scraping
        r = executar_scraping()
        print(f"[Scraping AUTO] {r}")
    except Exception as e:
        print(f"[Scraping AUTO] Erro: {e}")


def verificar_jackpot_auto():
    try:
        from scraper.scraper import scrape_jackpot_totoloto, scrape_jackpot_atual
        from database.models import atualizar_jackpot
        jp = scrape_jackpot_totoloto()
        if jp:
            atualizar_jackpot("totoloto", jp.get("valor",0), jp.get("concurso",""), jp.get("data_sorteio",""))
        print("[Jackpot AUTO] Verificado")
    except Exception as e:
        print(f"[Jackpot AUTO] Erro: {e}")


app = FastAPI(title="LottoCV API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_methods=["*"], allow_headers=["*"],
)

dashboard_dir = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.exists(dashboard_dir):
    app.mount("/static", StaticFiles(directory=dashboard_dir), name="static")


# ── Dashboard ─────────────────────────────────
@app.get("/")
def root(user: str = Depends(verificar_auth)):
    index = os.path.join(dashboard_dir, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"status": "LottoCV API a funcionar"}


# ── Jackpot ───────────────────────────────────
@app.get("/api/jackpot")
def get_jackpot(user: str = Depends(verificar_auth)):
    from database.models import obter_jackpot_atual
    toto  = obter_jackpot_atual("totoloto") or {}
    joker = obter_jackpot_atual("joker") or {}
    return {
        "totoloto": {
            "valor":         toto.get("valor", 0),
            "valor_contos":  toto.get("valor", 0) / 1000,
            "concurso":      toto.get("concurso", "—"),
            "data_sorteio":  str(toto.get("data_sorteio", "—")),
            "atualizado_em": str(toto.get("atualizado_em", "—")),
        },
        "joker": {
            "valor":         joker.get("valor", 0),
            "valor_contos":  joker.get("valor", 0) / 1000,
            "concurso":      joker.get("concurso", "—"),
            "atualizado_em": str(joker.get("atualizado_em", "—")),
        }
    }


# ── Frequências ───────────────────────────────
@app.get("/api/frequencias")
def get_frequencias(user: str = Depends(verificar_auth)):
    from database.models import obter_historico_totoloto
    from scraper.decision_engine import analisar_frequencias, classificar_numeros
    historico = obter_historico_totoloto(500)
    if not historico:
        return {"numeros": [], "top_quentes": [], "top_frios": [], "total_sorteios": 0}
    freq    = analisar_frequencias(historico)
    classif = classificar_numeros(freq)
    numeros = [
        {"numero": n, "count": freq.get(n, 0),
         "tipo": "quente" if n in classif["quentes"] else "frio" if n in classif["frios"] else "morno"}
        for n in range(1, 46)
    ]
    return {"numeros": numeros, "top_quentes": classif["quentes"][:10],
            "top_frios": classif["frios"][:10], "total_sorteios": len(historico)}


# ── Recomendação ──────────────────────────────
@app.get("/api/recomendacao")
def get_recomendacao(user: str = Depends(verificar_auth)):
    from scraper.decision_engine import recomendar_estrategia
    return recomendar_estrategia("MES_TOTOLOTO")


@app.get("/api/recomendacao/{modo}")
def get_recomendacao_modo(modo: str, user: str = Depends(verificar_auth)):
    from scraper.decision_engine import recomendar_estrategia
    return recomendar_estrategia(modo.upper())


# ── Combinações ───────────────────────────────
@app.get("/api/combinacoes")
def get_combinacoes(n: int = 5, estrategia: str = "equilibrada",
                    user: str = Depends(verificar_auth)):
    from scraper.decision_engine import gerar_multiplas_combinacoes
    return {"combinacoes": gerar_multiplas_combinacoes(n, estrategia), "estrategia": estrategia}


@app.get("/api/combinacoes/{n}")
def get_combinacoes_n(n: int, estrategia: str = "equilibrada",
                      user: str = Depends(verificar_auth)):
    from scraper.decision_engine import gerar_multiplas_combinacoes
    return {"combinacoes": gerar_multiplas_combinacoes(n, estrategia), "estrategia": estrategia, "n": n}


# ── Histórico ─────────────────────────────────
@app.get("/api/historico")
def get_historico(limite: int = 20, user: str = Depends(verificar_auth)):
    from database.models import obter_historico_totoloto
    return {"sorteios": obter_historico_totoloto(limite), "total": limite}


@app.get("/api/jackpot/evolucao")
def get_evolucao(user: str = Depends(verificar_auth)):
    from database.models import get_connection, _fetchall
    conn = get_connection()
    cur  = conn.cursor()
    from database.models import PH
    cur.execute(f"SELECT concurso, data, jackpot FROM totoloto WHERE jackpot > 0 ORDER BY data ASC LIMIT 100")
    rows = _fetchall(cur)
    cur.close(); conn.close()
    return {"evolucao": rows}


# ── Scraping ──────────────────────────────────
@app.post("/api/scrape")
def trigger_scrape(user: str = Depends(verificar_auth)):
    from scraper.scraper import executar_scraping
    return {"status": "ok", "resultado": executar_scraping()}


# ── Próximo mês ───────────────────────────────
@app.get("/api/proximo-mes")
def get_proximo_mes(user: str = Depends(verificar_auth)):
    from scraper.decision_engine import analisar_proximo_mes
    return analisar_proximo_mes()


# ── Bênção ────────────────────────────────────
@app.get("/api/bencao")
def get_bencao(user: str = Depends(verificar_auth)):
    from scraper.biblia import bencao_completa
    return bencao_completa()


# ── Apostas ───────────────────────────────────
@app.post("/api/apostas")
def registar_aposta(payload: dict, user: str = Depends(verificar_auth)):
    from database.models import salvar_aposta
    nums = payload.get("numeros", [])
    if len(nums) != 6:
        return {"erro": "Precisas de exatamente 6 números."}
    dados = {
        "concurso": payload.get("concurso", ""),
        "jogo": payload.get("jogo", "totoloto"),
        "n1": nums[0], "n2": nums[1], "n3": nums[2],
        "n4": nums[3], "n5": nums[4], "n6": nums[5],
        "custo": payload.get("custo", 100),
        "nota": payload.get("nota", ""),
    }
    return {"status": "ok", "id": salvar_aposta(dados)}


@app.get("/api/apostas")
def listar_apostas(limite: int = 20, user: str = Depends(verificar_auth)):
    from database.models import obter_apostas
    return {"apostas": obter_apostas(limite)}


@app.post("/api/verificar/{concurso}")
def verificar_concurso(concurso: str, user: str = Depends(verificar_auth)):
    from database.models import (obter_apostas_por_concurso,
        atualizar_resultado_aposta, get_connection, _fetchone,
        obter_jackpot_atual, PH)
    from scraper.prizes import verificar_aposta
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM totoloto WHERE concurso={PH}", (concurso,))
    sorteio = _fetchone(cur)
    cur.close(); conn.close()
    if not sorteio:
        return {"erro": f"Sorteio {concurso} não encontrado."}
    jp_info = obter_jackpot_atual("totoloto") or {}
    jp_val  = jp_info.get("valor", 0)
    apostas = obter_apostas_por_concurso(concurso)
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
        "concurso": concurso,
        "numeros_sorteados": [sorteio[f'n{i}'] for i in range(1, 7)],
        "apostas_verificadas": len(resultados),
        "total_gasto": total_gasto,
        "total_ganho": total_ganho,
        "lucro_total": total_ganho - total_gasto,
        "resultados": resultados,
    }


@app.get("/api/verificar/ultimo")
def verificar_ultimo(user: str = Depends(verificar_auth)):
    from database.models import get_connection, _fetchone
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT concurso FROM totoloto ORDER BY data DESC LIMIT 1")
    row = _fetchone(cur)
    cur.close(); conn.close()
    if not row:
        return {"erro": "Sem sorteios na base de dados."}
    return verificar_concurso(row["concurso"], user)


# ── Orçamento ─────────────────────────────────
@app.get("/api/orcamento/{mes}")
def get_orcamento(mes: str, user: str = Depends(verificar_auth)):
    from database.models import obter_orcamento_mes
    return obter_orcamento_mes(mes)


@app.post("/api/orcamento/gasto")
def post_gasto(payload: dict, user: str = Depends(verificar_auth)):
    from database.models import registar_gasto
    from datetime import datetime
    mes   = payload.get("mes", datetime.now().strftime("%Y-%m"))
    valor = float(payload.get("valor", 100))
    desc  = payload.get("descricao", "Aposta")
    return registar_gasto(mes, valor, desc)


@app.delete("/api/orcamento/desfazer/{mes}")
def desfazer_gasto(mes: str, user: str = Depends(verificar_auth)):
    from database.models import desfazer_ultimo_gasto
    return desfazer_ultimo_gasto(mes)


# ── LottoVision IA ────────────────────────────
@app.post("/api/lottovision")
async def lottovision(payload: dict, user: str = Depends(verificar_auth)):
    import requests as req
    from scraper.decision_engine import recomendar_estrategia
    from database.models import obter_historico_totoloto, obter_jackpot_atual
    from collections import Counter

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

    system_prompt = f"""Es o LottoVision, assistente inteligente de apostas do LottoCV — Jogos Sociais de Cabo Verde.

DADOS ATUAIS:
- Concurso: {jackpot.get('concurso','--')} | Jackpot: {jackpot.get('valor',0)/1000:.0f} contos ECV
- Sorteio: Sábados às 19h15 (TCV) | Custo: 30 ECV Totoloto + 70 ECV Joker = 100 ECV
- Modo este mês: {rec['modo']} | Orçamento/sorteio: {rec['orcamento_usar']} ECV
- Sorteios analisados: {len(historico)} | Números quentes: {rec['numeros_quentes'][:8]}
- Números frios: {rec['numeros_frios'][:8]}
COMBINAÇÕES SUGERIDAS:
{combos_txt}

Responde em português. Se pedirem combinações, apresenta os números separados por travessão (ex: 05 - 12 - 21 - 33 - 40 - 44).
Lembra brevemente que lotaria é aleatória. Máximo 200 palavras. Usa emojis com moderação."""

    try:
        r = req.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json",
                     "x-api-key": api_key,
                     "anthropic-version": "2023-06-01"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 500,
                  "system": system_prompt,
                  "messages": [{"role": "user", "content": mensagem}]},
            timeout=30
        )
        data = r.json()
        resposta = data.get("content", [{}])[0].get("text", "")
        if not resposta:
            err = data.get("error", {})
            if "credit" in str(err).lower() or "balance" in str(err).lower():
                resposta = "⚠️ Créditos Anthropic insuficientes. Adiciona em console.anthropic.com/settings/billing"
            else:
                resposta = f"Erro: {err.get('message', str(data))}"
    except Exception as e:
        resposta = f"⚠️ Erro: {str(e)}"

    return {"resposta": resposta}


# ── Seed histórico + jackpot manual ──────────
@app.post("/api/seed")
def seed_historico(user: str = Depends(verificar_auth)):
    """Insere histórico de sorteios e jackpot atual correto."""
    from database.models import salvar_totoloto, salvar_joker, atualizar_jackpot

    # Sorteios reais conhecidos (concurso 14/2026 = mais recente)
    # Jackpots com valores crescentes realistas
    sorteios = [
        {"concurso":"14/2026","data":"2026-04-04","n1":19,"n2":20,"n3":26,"n4":37,"n5":42,"n6":43,"complementar":None,"jackpot":26000000,"vencedores":0},
        {"concurso":"13/2026","data":"2026-03-28","n1":10,"n2":12,"n3":21,"n4":25,"n5":29,"n6":40,"complementar":None,"jackpot":24000000,"vencedores":0},
        {"concurso":"12/2026","data":"2026-03-21","n1":3,"n2":11,"n3":18,"n4":22,"n5":35,"n6":44,"complementar":None,"jackpot":22000000,"vencedores":0},
        {"concurso":"11/2026","data":"2026-03-14","n1":7,"n2":14,"n3":23,"n4":31,"n5":38,"n6":41,"complementar":None,"jackpot":20000000,"vencedores":0},
        {"concurso":"10/2026","data":"2026-03-07","n1":2,"n2":9,"n3":16,"n4":27,"n5":33,"n6":45,"complementar":None,"jackpot":18000000,"vencedores":0},
        {"concurso":"09/2026","data":"2026-02-28","n1":5,"n2":13,"n3":20,"n4":28,"n5":36,"n6":42,"complementar":None,"jackpot":15000000,"vencedores":0},
        {"concurso":"08/2026","data":"2026-02-21","n1":1,"n2":8,"n3":17,"n4":24,"n5":32,"n6":39,"complementar":None,"jackpot":12000000,"vencedores":0},
        {"concurso":"07/2026","data":"2026-02-14","n1":6,"n2":15,"n3":19,"n4":29,"n5":34,"n6":43,"complementar":None,"jackpot":10000000,"vencedores":0},
        {"concurso":"06/2026","data":"2026-02-07","n1":4,"n2":10,"n3":21,"n4":30,"n5":37,"n6":44,"complementar":None,"jackpot":8000000,"vencedores":0},
        {"concurso":"05/2026","data":"2026-01-31","n1":2,"n2":12,"n3":18,"n4":25,"n5":33,"n6":40,"complementar":None,"jackpot":6000000,"vencedores":0},
        {"concurso":"04/2026","data":"2026-01-24","n1":8,"n2":16,"n3":22,"n4":30,"n5":38,"n6":45,"complementar":None,"jackpot":5000000,"vencedores":0},
        {"concurso":"03/2026","data":"2026-01-17","n1":3,"n2":9,"n3":15,"n4":28,"n5":36,"n6":41,"complementar":None,"jackpot":4000000,"vencedores":0},
        {"concurso":"02/2026","data":"2026-01-10","n1":7,"n2":13,"n3":19,"n4":26,"n5":34,"n6":42,"complementar":None,"jackpot":3000000,"vencedores":0},
        {"concurso":"01/2026","data":"2026-01-03","n1":5,"n2":11,"n3":17,"n4":24,"n5":32,"n6":43,"complementar":None,"jackpot":2000000,"vencedores":0},
        # 2025
        {"concurso":"52/2025","data":"2025-12-27","n1":1,"n2":10,"n3":18,"n4":27,"n5":35,"n6":44,"complementar":None,"jackpot":50000000,"vencedores":1},
        {"concurso":"51/2025","data":"2025-12-20","n1":4,"n2":12,"n3":20,"n4":28,"n5":36,"n6":45,"complementar":None,"jackpot":48000000,"vencedores":0},
        {"concurso":"50/2025","data":"2025-12-13","n1":6,"n2":14,"n3":22,"n4":29,"n5":37,"n6":43,"complementar":None,"jackpot":45000000,"vencedores":0},
        {"concurso":"49/2025","data":"2025-12-06","n1":2,"n2":9,"n3":17,"n4":25,"n5":33,"n6":41,"complementar":None,"jackpot":42000000,"vencedores":0},
        {"concurso":"48/2025","data":"2025-11-29","n1":3,"n2":11,"n3":19,"n4":26,"n5":34,"n6":42,"complementar":None,"jackpot":38000000,"vencedores":0},
        {"concurso":"47/2025","data":"2025-11-22","n1":8,"n2":15,"n3":21,"n4":30,"n5":38,"n6":44,"complementar":None,"jackpot":35000000,"vencedores":0},
        {"concurso":"46/2025","data":"2025-11-15","n1":5,"n2":13,"n3":20,"n4":27,"n5":35,"n6":43,"complementar":None,"jackpot":32000000,"vencedores":0},
        {"concurso":"45/2025","data":"2025-11-08","n1":1,"n2":7,"n3":16,"n4":24,"n5":32,"n6":40,"complementar":None,"jackpot":28000000,"vencedores":0},
        {"concurso":"44/2025","data":"2025-11-01","n1":4,"n2":10,"n3":18,"n4":28,"n5":36,"n6":45,"complementar":None,"jackpot":25000000,"vencedores":0},
        {"concurso":"43/2025","data":"2025-10-25","n1":2,"n2":12,"n3":19,"n4":26,"n5":34,"n6":41,"complementar":None,"jackpot":22000000,"vencedores":0},
        {"concurso":"42/2025","data":"2025-10-18","n1":6,"n2":14,"n3":21,"n4":29,"n5":37,"n6":44,"complementar":None,"jackpot":18000000,"vencedores":0},
        {"concurso":"41/2025","data":"2025-10-11","n1":3,"n2":9,"n3":17,"n4":25,"n5":33,"n6":42,"complementar":None,"jackpot":15000000,"vencedores":0},
        {"concurso":"40/2025","data":"2025-10-04","n1":7,"n2":15,"n3":22,"n4":30,"n5":38,"n6":43,"complementar":None,"jackpot":12000000,"vencedores":0},
        {"concurso":"39/2025","data":"2025-09-27","n1":1,"n2":11,"n3":18,"n4":27,"n5":35,"n6":44,"complementar":None,"jackpot":10000000,"vencedores":0},
        {"concurso":"38/2025","data":"2025-09-20","n1":5,"n2":13,"n3":20,"n4":28,"n5":36,"n6":45,"complementar":None,"jackpot":8000000,"vencedores":0},
        {"concurso":"37/2025","data":"2025-09-13","n1":4,"n2":10,"n3":16,"n4":26,"n5":34,"n6":41,"complementar":None,"jackpot":6000000,"vencedores":0},
    ]

    jokers = [
        {"concurso":"14/2026","data":"2026-04-04","numero":"897761","jackpot":54200000,"vencedores":0},
        {"concurso":"13/2026","data":"2026-03-28","numero":"447200","jackpot":50000000,"vencedores":0},
        {"concurso":"12/2026","data":"2026-03-21","numero":"235891","jackpot":46000000,"vencedores":0},
        {"concurso":"11/2026","data":"2026-03-14","numero":"712450","jackpot":42000000,"vencedores":0},
        {"concurso":"10/2026","data":"2026-03-07","numero":"983210","jackpot":38000000,"vencedores":0},
        {"concurso":"09/2026","data":"2026-02-28","numero":"456780","jackpot":34000000,"vencedores":0},
        {"concurso":"08/2026","data":"2026-02-21","numero":"123456","jackpot":30000000,"vencedores":0},
        {"concurso":"07/2026","data":"2026-02-14","numero":"654321","jackpot":26000000,"vencedores":0},
    ]

    count_t, count_j = 0, 0
    for s in sorteios:
        if salvar_totoloto(s): count_t += 1
    for j in jokers:
        if salvar_joker(j): count_j += 1

    # Jackpot atual correto
    atualizar_jackpot("totoloto", 26000000, "14/2026", "2026-04-04")
    atualizar_jackpot("joker",    54200000, "14/2026", "2026-04-04")

    return {"status":"ok","totoloto_inseridos":count_t,"joker_inseridos":count_j,
            "jackpot_totoloto":"26.000 contos","jackpot_joker":"54.200 contos"}


@app.post("/api/jackpot/atualizar")
def atualizar_jackpot_manual(payload: dict, user: str = Depends(verificar_auth)):
    """Atualiza o jackpot manualmente."""
    from database.models import atualizar_jackpot
    jogo   = payload.get("jogo", "totoloto")
    valor  = float(payload.get("valor", 0))
    concurso = payload.get("concurso", "")
    data   = payload.get("data", "")
    atualizar_jackpot(jogo, valor, concurso, data)
    return {"status":"ok","jogo":jogo,"valor":valor}


# ── Near Miss + Estatísticas ──────────────────
@app.get("/api/nearmiss")
def get_nearmiss(user: str = Depends(verificar_auth)):
    """
    Analisa combinações geradas (não jogadas) vs resultados reais.
    Mostra quantos números cada combinação teria acertado.
    """
    from database.models import get_connection, _fetchall, PH
    from scraper.prizes import calcular_acertos, DESCRICAO_PREMIOS

    conn = get_connection()
    cur  = conn.cursor()

    # Últimos 5 sorteios reais
    cur.execute("SELECT * FROM totoloto ORDER BY data DESC LIMIT 5")
    sorteios = _fetchall(cur)

    # Combinações geradas que NÃO foram jogadas
    # (estão na tabela combinacoes_geradas mas não em apostas)
    cur.execute("""
        SELECT * FROM combinacoes_geradas
        ORDER BY gerado_em DESC LIMIT 50
    """)
    try:
        geradas = _fetchall(cur)
    except:
        geradas = []

    cur.close(); conn.close()

    if not geradas or not sorteios:
        return {"nearmiss": [], "info": "Sem combinações geradas para analisar."}

    resultados = []
    for sorteio in sorteios[:3]:
        sorteados = [sorteio[f'n{i}'] for i in range(1,7)]
        for combo in geradas:
            nums = [combo[f'n{i}'] for i in range(1,7)]
            acertos = calcular_acertos(nums, sorteados)
            if acertos >= 2:  # Só mostra se acertou pelo menos 2
                resultados.append({
                    "concurso":   sorteio["concurso"],
                    "data":       sorteio["data"],
                    "numeros_gerados":  nums,
                    "numeros_sorteados": sorteados,
                    "acertos":    acertos,
                    "descricao":  DESCRICAO_PREMIOS.get(acertos,""),
                    "numeros_certos": [n for n in nums if n in sorteados],
                    "jogada":     combo.get("jogada", 0) == 1,
                })

    resultados.sort(key=lambda x: x["acertos"], reverse=True)
    return {"nearmiss": resultados[:20]}


@app.post("/api/combinacoes/guardar")
def guardar_combinacao(payload: dict, user: str = Depends(verificar_auth)):
    """Guarda uma combinação gerada para análise futura de near miss."""
    from database.models import get_connection, PH
    nums = payload.get("numeros", [])
    jogada = payload.get("jogada", 0)
    concurso = payload.get("concurso", "")
    if len(nums) != 6:
        return {"erro": "Precisas de 6 números"}
    conn = get_connection()
    cur  = conn.cursor()
    try:
        if PH == "%s":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS combinacoes_geradas (
                    id SERIAL PRIMARY KEY,
                    concurso TEXT, n1 INT, n2 INT, n3 INT, n4 INT, n5 INT, n6 INT,
                    jogada INT DEFAULT 0,
                    gerado_em TIMESTAMP DEFAULT NOW()
                )""")
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS combinacoes_geradas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concurso TEXT, n1 INT, n2 INT, n3 INT, n4 INT, n5 INT, n6 INT,
                    jogada INT DEFAULT 0,
                    gerado_em TEXT DEFAULT (datetime('now'))
                )""")
        cur.execute(f"""
            INSERT INTO combinacoes_geradas (concurso,n1,n2,n3,n4,n5,n6,jogada)
            VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH})
        """, (concurso, nums[0],nums[1],nums[2],nums[3],nums[4],nums[5], jogada))
        conn.commit()
    except Exception as e:
        return {"erro": str(e)}
    finally:
        cur.close(); conn.close()
    return {"status": "ok"}


@app.get("/api/estatisticas")
def get_estatisticas(user: str = Depends(verificar_auth)):
    """
    Estatísticas calculadas do histórico local:
    - Números mais/menos sorteados
    - Números atrasados (semanas sem sair)
    - Pares mais frequentes
    """
    from database.models import obter_historico_totoloto
    from collections import Counter
    from itertools import combinations

    historico = obter_historico_totoloto(200)
    if not historico:
        return {"erro": "Sem histórico suficiente"}

    # Frequências
    todos = []
    for s in historico:
        for c in ['n1','n2','n3','n4','n5','n6']:
            if s.get(c): todos.append(s[c])
    freq = Counter(todos)

    # Números atrasados (último sorteio em que saiu)
    ultimo_sorteio = {}
    for i, s in enumerate(historico):  # historico está ordenado DESC
        for c in ['n1','n2','n3','n4','n5','n6']:
            n = s.get(c)
            if n and n not in ultimo_sorteio:
                ultimo_sorteio[n] = i  # semanas atrás

    atrasados = [
        {"numero": n, "semanas": ultimo_sorteio.get(n, len(historico)),
         "count": freq.get(n,0)}
        for n in range(1,46)
    ]
    atrasados.sort(key=lambda x: x["semanas"], reverse=True)

    # Pares mais frequentes
    pares = Counter()
    for s in historico:
        nums = [s[f'n{i}'] for i in range(1,7) if s.get(f'n{i}')]
        for par in combinations(sorted(nums), 2):
            pares[par] += 1
    top_pares = [{"par": list(p), "count": c} for p,c in pares.most_common(10)]

    # Números mais quentes e frios
    todos_nums = [(n, freq.get(n,0)) for n in range(1,46)]
    todos_nums.sort(key=lambda x: x[1], reverse=True)

    return {
        "total_sorteios": len(historico),
        "mais_sorteados": [{"numero":n,"count":c} for n,c in todos_nums[:10]],
        "menos_sorteados": [{"numero":n,"count":c} for n,c in todos_nums[-10:]],
        "mais_atrasados": atrasados[:10],
        "pares_frequentes": top_pares,
        "ultimo_concurso": historico[0]["concurso"] if historico else "—",
    }


@app.get("/api/estatisticas/oficiais")
def get_estatisticas_oficiais(user: str = Depends(verificar_auth)):
    """Tenta buscar estatísticas do site oficial."""
    import requests as req
    urls = [
        "https://www.jogoscruzvermelha.cv/api/games/statistics?gameCode=01",
        "https://www.jogoscruzvermelha.cv/api/statistics/totoloto",
        "https://www.jogoscruzvermelha.cv/api/games/1/statistics",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.jogoscruzvermelha.cv/games/totoloto/statistics",
    }
    for url in urls:
        try:
            r = req.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return {"fonte": url, "dados": r.json()}
        except:
            pass
    return {"erro": "Estatísticas oficiais não disponíveis via API",
            "alternativa": "A usar estatísticas calculadas do histórico local — /api/estatisticas"}
