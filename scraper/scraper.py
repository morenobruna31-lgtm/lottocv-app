"""
Scraper — jogoscruzvermelha.cv
API JSON oficial
"""
import requests, time, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

BASE_URL = "https://www.jogoscruzvermelha.cv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "pt-PT,pt;q=0.9",
    "Referer": f"{BASE_URL}/games/totoloto",
}


def fetch_json(url, retries=3):
    for i in range(1, retries+1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.warning(f"Tentativa {i}/{retries} falhou ({url}): {e}")
            if i < retries: time.sleep(3*i)
    return None


def scrape_ultimo_sorteio():
    data = fetch_json(f"{BASE_URL}/api/games/results")
    if data:
        log.info(f"[API] Último sorteio: {data.get('totoloto',{}).get('drawCode','?')}")
    return data


def scrape_jackpot_atual():
    """
    Tenta obter jackpot do próximo sorteio.
    O endpoint context=currentDraw pode estar bloqueado — usamos fallback.
    """
    data = fetch_json(f"{BASE_URL}/api/games?context=currentDraw")
    if data:
        log.info(f"[API] Jackpot atual obtido via currentDraw")
        return data
    log.warning("[API] currentDraw bloqueado — a usar jackpot conhecido")
    return None


def extrair_jackpot(data):
    """
    Extrai jackpot do endpoint /api/games?context=currentDraw
    Estrutura: { "totoloto": { "estimatedJackpotValue": 26000000, ... }, "joker": {...} }
    """
    resultado = {"totoloto": 0.0, "joker": 0.0,
                 "concurso_totoloto": "", "data_totoloto": "",
                 "concurso_joker": "", "data_joker": ""}
    if not data:
        return resultado

    for jogo in ["totoloto", "joker"]:
        bloco = data.get(jogo)
        if not isinstance(bloco, dict):
            continue
        val = bloco.get("estimatedJackpotValue", 0)
        try:
            resultado[jogo] = float(val)
            resultado[f"concurso_{jogo}"] = bloco.get("drawCode", "")
            resultado[f"data_{jogo}"] = bloco.get("drawDate", "")[:10]
            log.info(f"[Jackpot] {jogo}: {resultado[jogo]:,.0f} ECV | concurso: {resultado[f'concurso_{jogo}']}")
        except (ValueError, TypeError):
            pass

    return resultado


def parse_totoloto(raw):
    t = raw.get("totoloto")
    if not t: return None
    nums = [int(n) for n in t.get("selection", [])]
    if len(nums) < 6: return None
    return {
        "concurso": t.get("drawCode",""),
        "data":     t.get("drawDate","")[:10],
        "n1":nums[0],"n2":nums[1],"n3":nums[2],
        "n4":nums[3],"n5":nums[4],"n6":nums[5],
        "complementar": nums[6] if len(nums)>6 else None,
        "jackpot": 0.0, "vencedores": 0,
    }


def parse_joker(raw):
    j = raw.get("joker")
    if not j: return None
    return {
        "concurso": j.get("drawCode",""),
        "data":     j.get("drawDate","")[:10],
        "numero":   "".join(str(n) for n in j.get("selection",[])),
        "jackpot":  0.0, "vencedores": 0,
    }


def scrape_jackpot_totoloto():
    """Compatibilidade com código antigo."""
    raw = scrape_ultimo_sorteio()
    if not raw: return None
    t = raw.get("totoloto",{})
    return {"jogo":"totoloto","valor":0.0,
            "concurso":t.get("drawCode",""),
            "data_sorteio":t.get("drawDate","")[:10]}


def executar_scraping():
    from database.models import (salvar_totoloto, salvar_joker,
        atualizar_jackpot, registar_log)

    log.info("=== Início do Scraping ===")
    resumo = {"jackpot_totoloto":0.0,"jackpot_joker":0.0,
              "novos_totoloto":0,"novos_joker":0}
    try:
        raw = scrape_ultimo_sorteio()
        if raw:
            toto = parse_totoloto(raw)
            if toto and salvar_totoloto(toto):
                resumo["novos_totoloto"] += 1
                log.info(f"[Totoloto] Novo: {toto['concurso']} — {[toto[f'n{i}'] for i in range(1,7)]}")

            joker = parse_joker(raw)
            if joker and salvar_joker(joker):
                resumo["novos_joker"] += 1
                log.info(f"[Joker] Novo: {joker['concurso']} — {joker['numero']}")

            # Tenta obter jackpot real
            jp_data = scrape_jackpot_atual()
            jp = extrair_jackpot(jp_data) if jp_data else {"totoloto":0.0,"joker":0.0}
            resumo["jackpot_totoloto"] = jp["totoloto"]
            resumo["jackpot_joker"]    = jp["joker"]

            # Usa dados do currentDraw (próximo sorteio) se disponíveis
            t_info = raw.get("totoloto",{})
            j_info = raw.get("joker",{})
            t_conc = jp.get("concurso_totoloto") or t_info.get("drawCode","")
            t_data = jp.get("data_totoloto") or t_info.get("drawDate","")[:10]
            j_conc = jp.get("concurso_joker") or j_info.get("drawCode","")
            j_data = jp.get("data_joker") or j_info.get("drawDate","")[:10]
            atualizar_jackpot("totoloto", jp["totoloto"], t_conc, t_data)
            atualizar_jackpot("joker",    jp["joker"],    j_conc, j_data)

        concurso = raw.get("totoloto",{}).get("drawCode","?") if raw else "?"
        msg = f"OK — Concurso: {concurso} | Novos: T={resumo['novos_totoloto']} J={resumo['novos_joker']}"
        log.info(msg)
        registar_log("OK", msg, resumo["novos_totoloto"]+resumo["novos_joker"])

    except Exception as e:
        msg = f"ERRO: {e}"
        log.error(msg)
        registar_log("ERRO", msg)

    log.info("=== Fim do Scraping ===")
    return resumo
