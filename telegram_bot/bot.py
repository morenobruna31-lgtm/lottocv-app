"""
Bot Telegram — LottoCV
Comandos disponíveis:
  /start        — Boas-vindas e menu principal
  /jackpot      — Ver jackpot atual
  /recomendar   — Recomendação de aposta com combinações
  /combinacoes  — Gerar novas combinações
  /frequencias  — Top 10 quentes e frios
  /historico    — Últimos 5 sorteios
  /ativar       — Ativar alertas automáticos
  /desativar    — Desativar alertas automáticos
  /ajuda        — Ajuda e instruções
"""

import os, sys, json, logging, asyncio
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from database.models import (
    init_db, get_connection,
    obter_jackpot_atual, obter_historico_totoloto
)
from scraper.decision_engine import (
    recomendar_estrategia, gerar_multiplas_combinacoes,
    analisar_frequencias, classificar_numeros
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [BOT] %(levelname)s %(message)s'
)
log = logging.getLogger(__name__)

TOKEN      = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_URL    = f"https://api.telegram.org/bot{TOKEN}"
SUBS_FILE  = Path(__file__).parent / "subscribers.json"


# ──────────────────────────────────────────────
# Gestão de subscritores
# ──────────────────────────────────────────────
def load_subs() -> set:
    if SUBS_FILE.exists():
        return set(json.loads(SUBS_FILE.read_text()))
    return set()

def save_subs(subs: set):
    SUBS_FILE.write_text(json.dumps(list(subs)))

subscribers: set = load_subs()


# ──────────────────────────────────────────────
# Helpers Telegram API (polling simples — sem library externa)
# ──────────────────────────────────────────────
def tg_post(method: str, payload: dict) -> dict:
    try:
        r = requests.post(f"{API_URL}/{method}", json=payload, timeout=10)
        return r.json()
    except Exception as e:
        log.error(f"[TG] {method} falhou: {e}")
        return {}

def send(chat_id: int | str, text: str, parse_mode: str = "Markdown",
         reply_markup: dict | None = None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    tg_post("sendMessage", payload)


# ──────────────────────────────────────────────
# Teclado principal
# ──────────────────────────────────────────────
MENU_KEYBOARD = {
    "keyboard": [
        [{"text": "💰 Jackpot"}, {"text": "🎲 Recomendar"}],
        [{"text": "🔢 Combinações"}, {"text": "🔥 Frequências"}],
        [{"text": "📋 Histórico"},   {"text": "🔔 Ativar alertas"}],
    ],
    "resize_keyboard": True,
    "one_time_keyboard": False,
}


# ──────────────────────────────────────────────
# Formatadores de mensagens
# ──────────────────────────────────────────────
def fmt_num(n): return f"{int(n):,}".replace(",", ".")

def msg_jackpot() -> str:
    jp = obter_jackpot_atual("totoloto") or {}
    jj = obter_jackpot_atual("joker") or {}
    val_t = jp.get("valor", 0)
    val_j = jj.get("valor", 0)
    pct   = min(100, val_t / 50_000_000 * 100)
    bar_n = int(pct / 10)
    bar   = "🟡" * bar_n + "⬜" * (10 - bar_n)

    modo = "🔥 JACKPOT CRÍTICO — APOSTAS CONCENTRADAS" if val_t >= 40_000_000 else "📅 Modo semanal recomendado"

    return (
        f"💎 *JACKPOT TOTOLOTO CV*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎰 Totoloto: *{fmt_num(val_t / 1000)} contos*\n"
        f"🃏 Joker:    *{fmt_num(val_j / 1000)} contos*\n\n"
        f"{bar} `{pct:.0f}%`\n"
        f"_do máximo de 50.000 contos_\n\n"
        f"📊 {modo}\n\n"
        f"🕐 Concurso: {jp.get('concurso', '—')}\n"
        f"📅 Data: {jp.get('data_sorteio', '—')}"
    )


def msg_recomendacao() -> str:
    rec = recomendar_estrategia()
    combos_txt = "\n".join([
        f"  `Chave {i+1}:` *{' — '.join(f'{n:02d}' for n in c)}*"
        for i, c in enumerate(rec["combinacoes"])
    ])
    quentes = " · ".join(f"`{n:02d}`" for n in rec["numeros_quentes"][:8])
    frios   = " · ".join(f"`{n:02d}`" for n in rec["numeros_frios"][:8])

    modo_emoji = "🔥" if rec["modo"] == "CONCENTRADO" else "📅"

    return (
        f"🎯 *RECOMENDAÇÃO DE APOSTA*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Modo: *{rec['modo']}* {modo_emoji}\n"
        f"💳 Orçamento: *{fmt_num(rec['orcamento_usar'])} ECV*\n\n"
        f"_{rec['justificacao']}_\n\n"
        f"🎲 *Combinações sugeridas:*\n{combos_txt}\n\n"
        f"🔥 *Quentes:* {quentes}\n"
        f"❄️ *Frios:*  {frios}\n\n"
        f"📈 Baseado em *{rec['total_sorteios_analisados']}* sorteios históricos\n\n"
        f"⚠️ _Joga com responsabilidade e dentro das tuas possibilidades._"
    )


def msg_combinacoes(n: int = 5) -> str:
    combos = gerar_multiplas_combinacoes(n, "equilibrada")
    linhas = "\n".join([
        f"  🎱 *{' — '.join(f'{num:02d}' for num in c)}*"
        for c in combos
    ])
    return (
        f"🎲 *NOVAS COMBINAÇÕES*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_{n} chaves geradas por análise de frequência:_\n\n"
        f"{linhas}\n\n"
        f"💡 Usa /recomendar para ver a estratégia completa."
    )


def msg_frequencias() -> str:
    hist = obter_historico_totoloto(200)
    if not hist:
        return "⚠️ Sem histórico disponível. Usa /scrape para atualizar os dados."
    freq = analisar_frequencias(hist)
    cl   = classificar_numeros(freq)

    quentes = [(n, freq[n]) for n in cl["quentes"][:10]]
    frios   = [(n, freq[n]) for n in cl["frios"][:10]]

    q_txt = "\n".join(f"  🔥 `{n:02d}` — sorteado *{c}×*" for n, c in quentes)
    f_txt = "\n".join(f"  ❄️ `{n:02d}` — sorteado *{c}×*" for n, c in frios)

    return (
        f"📊 *ANÁLISE DE FREQUÊNCIA*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_Baseado em {len(hist)} sorteios_\n\n"
        f"🔥 *10 Mais sorteados:*\n{q_txt}\n\n"
        f"❄️ *10 Menos sorteados:*\n{f_txt}\n\n"
        f"⚠️ _Nota: Lotaria é aleatória. Frequências passadas não preveem o futuro._"
    )


def msg_historico() -> str:
    hist = obter_historico_totoloto(5)
    if not hist:
        return "⚠️ Sem histórico. Usa /scrape para obter os dados mais recentes."

    linhas = []
    for s in hist:
        nums = [s.get(f'n{i}', 0) for i in range(1, 7)]
        nums_str = " · ".join(f"`{n:02d}`" for n in nums if n)
        jp  = f"{fmt_num(s['jackpot']/1000)} contos" if s.get("jackpot") else "—"
        linhas.append(
            f"🎫 *{s['concurso']}* _{s.get('data','')}_\n"
            f"   {nums_str}\n"
            f"   💰 {jp}"
        )

    return (
        f"📋 *ÚLTIMOS SORTEIOS*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        + "\n\n".join(linhas)
    )


def msg_ajuda() -> str:
    return (
        f"🤖 *LOTTOCV BOT — AJUDA*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*Comandos disponíveis:*\n\n"
        f"💰 /jackpot — Jackpot atual\n"
        f"🎯 /recomendar — Estratégia de aposta\n"
        f"🎲 /combinacoes — Gerar combinações\n"
        f"📊 /frequencias — Números quentes/frios\n"
        f"📋 /historico — Últimos sorteios\n"
        f"🔔 /ativar — Ativar alertas automáticos\n"
        f"🔕 /desativar — Desativar alertas\n\n"
        f"*Alertas automáticos:*\n"
        f"Recebes uma notificação quando o jackpot "
        f"atingir os 40.000 contos, com combinações prontas.\n\n"
        f"⚠️ _Joga com responsabilidade._"
    )


# ──────────────────────────────────────────────
# Router de mensagens
# ──────────────────────────────────────────────
def handle_message(update: dict):
    msg  = update.get("message") or update.get("edited_message", {})
    if not msg:
        return

    chat_id = msg["chat"]["id"]
    text    = msg.get("text", "").strip()

    # Normaliza texto do teclado
    text_map = {
        "💰 Jackpot":        "/jackpot",
        "🎲 Recomendar":     "/recomendar",
        "🔢 Combinações":    "/combinacoes",
        "🔥 Frequências":    "/frequencias",
        "📋 Histórico":      "/historico",
        "🔔 Ativar alertas": "/ativar",
    }
    text = text_map.get(text, text)

    log.info(f"[{chat_id}] → {text[:60]}")

    if text in ("/start", "/inicio"):
        nome = msg.get("from", {}).get("first_name", "jogador")
        send(chat_id,
            f"👋 Olá, *{nome}*! Bem-vindo ao *LottoCV Bot*.\n\n"
            f"O teu assistente inteligente para os Jogos Sociais de Cabo Verde.\n\n"
            f"Usa o menu abaixo ou escreve um comando:",
            reply_markup=MENU_KEYBOARD
        )

    elif text == "/jackpot":
        send(chat_id, msg_jackpot())

    elif text == "/recomendar":
        send(chat_id, "⏳ A calcular recomendação...")
        send(chat_id, msg_recomendacao())

    elif text == "/combinacoes":
        send(chat_id, msg_combinacoes(5))

    elif text == "/frequencias":
        send(chat_id, msg_frequencias())

    elif text == "/historico":
        send(chat_id, msg_historico())

    elif text == "/ativar":
        subscribers.add(chat_id)
        save_subs(subscribers)
        send(chat_id,
            f"🔔 *Alertas ativados!*\n\n"
            f"Vais receber uma notificação quando o jackpot "
            f"atingir os *40.000 contos* ou mais.\n\n"
            f"_Usa /desativar para parar os alertas._"
        )

    elif text == "/desativar":
        subscribers.discard(chat_id)
        save_subs(subscribers)
        send(chat_id, "🔕 Alertas desativados. Usa /ativar para os reativar.")

    elif text == "/ajuda":
        send(chat_id, msg_ajuda(), reply_markup=MENU_KEYBOARD)

    else:
        send(chat_id,
            f"Não reconheço esse comando. Usa /ajuda para ver os comandos disponíveis.",
            reply_markup=MENU_KEYBOARD
        )


# ──────────────────────────────────────────────
# Sistema de alertas automáticos
# ──────────────────────────────────────────────
_ultimo_alerta_valor = 0.0

def verificar_e_alertar():
    """Verifica jackpot e notifica subscritores se crítico."""
    global _ultimo_alerta_valor

    jp = obter_jackpot_atual("totoloto")
    if not jp:
        return

    valor = jp.get("valor", 0)
    LIMIAR = float(os.getenv("JACKPOT_CRITICO", "40000000"))

    if valor >= LIMIAR and abs(valor - _ultimo_alerta_valor) > 1_000_000:
        _ultimo_alerta_valor = valor
        rec = recomendar_estrategia()
        combos_txt = "\n".join([
            f"  🎱 `{' — '.join(f'{n:02d}' for n in c)}`"
            for c in rec["combinacoes"]
        ])
        alerta = (
            f"🚨 *ALERTA JACKPOT CRÍTICO!* 🚨\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 *{fmt_num(valor / 1000)} contos ECV*\n\n"
            f"O jackpot atingiu um valor crítico!\n"
            f"💳 Usar *{fmt_num(rec['orcamento_usar'])} ECV* de uma só vez.\n\n"
            f"🎲 *Combinações recomendadas:*\n{combos_txt}\n\n"
            f"⚠️ _Joga com responsabilidade._"
        )
        for cid in list(subscribers):
            send(cid, alerta)
        log.info(f"[Alerta] Enviado a {len(subscribers)} subscritores — {valor/1000:.0f} contos")


# ──────────────────────────────────────────────
# Polling loop
# ──────────────────────────────────────────────
def run_bot():
    if not TOKEN:
        log.error("TELEGRAM_BOT_TOKEN não definido no .env!")
        return

    init_db()
    log.info("🤖 Bot LottoCV iniciado. A aguardar mensagens...")

    offset = 0
    while True:
        try:
            data = tg_post("getUpdates", {
                "offset": offset,
                "timeout": 30,
                "allowed_updates": ["message"]
            })
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                handle_message(upd)
        except KeyboardInterrupt:
            log.info("Bot parado pelo utilizador.")
            break
        except Exception as e:
            log.error(f"Erro no loop: {e}")
            import time; time.sleep(5)


if __name__ == "__main__":
    run_bot()
