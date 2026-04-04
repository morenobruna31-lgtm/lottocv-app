"""
Scraper â€” jogoscruzvermelha.cv
Usa a API JSON oficial do site (descoberta via Network tab)
"""

import requests
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

BASE_URL = "https://www.jogoscruzvermelha.cv"
API = {
    "ultimo_sorteio": f"{BASE_URL}/api/games/results",
    "jackpot_atual":  f"{BASE_URL}/api/games?context=currentDraw",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "pt-PT,pt;q=0.9",
    "Referer": f"{BASE_URL}/games/totoloto",
}


def fetch_json(url, retries=3):
    for i in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.warning(f"Tentativa {i}/{retries} falhou ({url}): {e}")
            if i < retries:
                time.sleep(3 * i)
    return None


def scrape_ultimo_sorteio():
    data = fetch_json(API["ultimo_sorteio"])
    if data:
        log.info(f"[API] Ãšltimo sorteio: concurso {data.get('totoloto',{}).get('drawCode','?')}")
    return data


def scrape_jackpot_atual():
    return fetch_json(API["jackpot_atual"])


def parse_totoloto(raw):
    t = raw.get("totoloto")
    if not t:
        return None
    nums = [int(n) for n in t.get("selection", [])]
    if len(nums) < 6:
        return None
    return {
        "concurso": t.get("drawCode", ""),
        "data":     t.get("drawDate", "")[:10],
        "n1": nums[0], "n2": nums[1], "n3": nums[2],
        "n4": nums[3], "n5": nums[4], "n6": nums[5],
        "complementar": nums[6] if len(nums) > 6 else None,
        "jackpot": 0.0, "vencedores": 0,
    }


def parse_joker(raw):
    j = raw.get("joker")
    if not j:
        return None
    return {
        "concurso":   j.get("drawCode", ""),
        "data":       j.get("drawDate", "")[:10],
        "numero":     "".join(str(n) for n in j.get("selection", [])),
        "jackpot":    0.0,
        "vencedores": 0,
    }


def parse_jackpot(data):
    resultado = {"totoloto": 0.0, "joker": 0.0}
    if not data:
        return resultado
    for jogo in ["totoloto", "joker"]:
        bloco = data.get(f"lastDrawOnSale_{jogo}", {})
        if isinstance(bloco, dict):
            val = bloco.get("estimatedJackpotValue", 0)
            if val:
                try:
                    resultado[jogo] = float(val)
                except ValueError:
                    pass
    return resultado


def executar_scraping():
    from database.models import salvar_totoloto, salvar_joker, atualizar_jackpot, registar_log

    log.info("=== InÃ­cio do Scraping (API JSON) ===")
    resumo = {"jackpot_totoloto": 0.0, "jackpot_joker": 0.0, "novos_totoloto": 0, "novos_joker": 0}

    try:
        raw = scrape_ultimo_sorteio()
        if raw:
            toto = parse_totoloto(raw)
            if toto:
                if salvar_totoloto(toto):
                    resumo["novos_totoloto"] += 1
                    log.info(f"[Totoloto] Guardado: {toto['concurso']} â€” {[toto[f'n{i}'] for i in range(1,7)]}")

            joker = parse_joker(raw)
            if joker:
                if salvar_joker(joker):
                    resumo["novos_joker"] += 1
                    log.info(f"[Joker] Guardado: {joker['concurso']} â€” {joker['numero']}")

            # Jackpot atual
            jp_data = scrape_jackpot_atual()
            if jp_data:
                jp = parse_jackpot(jp_data)
                resumo["jackpot_totoloto"] = jp["totoloto"]
                resumo["jackpot_joker"]    = jp["joker"]
                toto_draw = jp_data.get("lastDrawOnSale_totoloto", {})
                joker_draw = jp_data.get("lastDrawOnSale_joker", {})
                atualizar_jackpot("totoloto", jp["totoloto"],
                                  toto_draw.get("drawCode",""), toto_draw.get("drawDate","")[:10])
                atualizar_jackpot("joker", jp["joker"],
                                  joker_draw.get("drawCode",""), joker_draw.get("drawDate","")[:10])
            else:
                t_info = raw.get("totoloto", {})
                atualizar_jackpot("totoloto", 0.0,
                                  t_info.get("drawCode",""), t_info.get("drawDate","")[:10])
                j_info = raw.get("joker", {})
                atualizar_jackpot("joker", 0.0,
                                  j_info.get("drawCode",""), j_info.get("drawDate","")[:10])

        concurso = raw.get("totoloto",{}).get("drawCode","?") if raw else "?"
        msg = f"OK â€” Concurso: {concurso} | Novos: Totoloto={resumo['novos_totoloto']}, Joker={resumo['novos_joker']}"
        log.info(msg)
        registar_log("OK", msg, resumo["novos_totoloto"] + resumo["novos_joker"])

    except Exception as e:
        msg = f"ERRO: {e}"
        log.error(msg)
        registar_log("ERRO", msg)

    log.info("=== Fim do Scraping ===")
    return resumo


def scrape_jackpot_totoloto():
    raw = scrape_ultimo_sorteio()
    if not raw:
        return None
    t = raw.get("totoloto", {})
    return {"jogo": "totoloto", "valor": 0.0,
            "concurso": t.get("drawCode",""), "data_sorteio": t.get("drawDate","")[:10]}


if __name__ == '__main__':
    r = executar_scraping()
    print("\nðŸ“Š Resumo:")
    for k, v in r.items():
        print(f"  {k}: {v}")


