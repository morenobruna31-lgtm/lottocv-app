"""
Notificações — Telegram Bot + E-mail
Envia alertas quando o jackpot atinge valores críticos
"""

import os
import smtplib
import logging
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Configuração (via variáveis de ambiente)
# ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

EMAIL_REMETENTE    = os.getenv("EMAIL_REMETENTE", "")
EMAIL_PASSWORD     = os.getenv("EMAIL_PASSWORD", "")
EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO", "")
EMAIL_SMTP_HOST    = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_SMTP_PORT    = int(os.getenv("EMAIL_SMTP_PORT", "587"))

JACKPOT_CRITICO    = float(os.getenv("JACKPOT_CRITICO", "40000000"))  # 40M ECV


# ──────────────────────────────────────────────
# Telegram
# ──────────────────────────────────────────────
def enviar_telegram(mensagem: str) -> bool:
    """Envia mensagem via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("[Telegram] Token ou Chat ID não configurado.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        log.info("[Telegram] Mensagem enviada com sucesso.")
        return True
    except Exception as e:
        log.error(f"[Telegram] Erro: {e}")
        return False


# ──────────────────────────────────────────────
# E-mail
# ──────────────────────────────────────────────
def enviar_email(assunto: str, corpo: str) -> bool:
    """Envia e-mail via SMTP (Gmail ou outro)."""
    if not EMAIL_REMETENTE or not EMAIL_PASSWORD:
        log.warning("[Email] Credenciais não configuradas.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"]    = EMAIL_REMETENTE
    msg["To"]      = EMAIL_DESTINATARIO
    msg.attach(MIMEText(corpo, "plain", "utf-8"))

    try:
        with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
            server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
        log.info("[Email] Enviado com sucesso.")
        return True
    except Exception as e:
        log.error(f"[Email] Erro: {e}")
        return False


# ──────────────────────────────────────────────
# Lógica de Notificação
# ──────────────────────────────────────────────
def verificar_e_notificar(resultado: dict):
    """
    Analisa o resultado do scraping e envia alertas se necessário.
    """
    jackpot = resultado.get("jackpot_totoloto", 0.0)

    if jackpot <= 0:
        return

    jackpot_contos = jackpot / 1_000
    emoji = "🔥🔥🔥" if jackpot >= JACKPOT_CRITICO else "💰"

    if jackpot >= JACKPOT_CRITICO:
        # Alerta crítico — jackpot alto!
        from scraper.decision_engine import recomendar_estrategia
        rec = recomendar_estrategia()
        combos_texto = "\n".join(
            [f"  Chave {i+1}: {' - '.join(map(str, c))}" for i, c in enumerate(rec['combinacoes'])]
        )

        msg_telegram = (
            f"{emoji} *JACKPOT CRÍTICO — TOTOLOTO CV!* {emoji}\n\n"
            f"💎 Prémio acumulado: *{jackpot_contos:,.0f} Contos ECV*\n"
            f"📊 Modo recomendado: *{rec['modo']}*\n"
            f"💳 Orçamento a usar: *{rec['orcamento_usar']} ECV*\n\n"
            f"🎲 Combinações sugeridas:\n{combos_texto}\n\n"
            f"🔥 Números quentes: {rec['numeros_quentes']}\n"
            f"❄️ Números frios: {rec['numeros_frios']}\n\n"
            f"⚠️ _Lembra-te: jogar com responsabilidade!_"
        )

        assunto_email = f"🎰 JACKPOT TOTOLOTO CV — {jackpot_contos:,.0f} Contos!"
        corpo_email = msg_telegram.replace("*", "").replace("_", "")

        enviar_telegram(msg_telegram)
        enviar_email(assunto_email, corpo_email)

    else:
        # Atualização normal — só log
        log.info(f"[Notificação] Jackpot atual: {jackpot_contos:,.0f} contos. "
                 f"Abaixo do limiar crítico ({JACKPOT_CRITICO/1_000:,.0f} contos).")


def notificar_novos_resultados(novos_totoloto: int, novos_joker: int):
    """Notifica quando há novos resultados disponíveis."""
    if novos_totoloto == 0 and novos_joker == 0:
        return

    msg = (
        f"📋 *Novos resultados — Jogos CV*\n\n"
        f"🎯 Totoloto: {novos_totoloto} novo(s) sorteio(s)\n"
        f"🃏 Joker: {novos_joker} novo(s) sorteio(s)\n\n"
        f"_Acede ao dashboard para ver os detalhes._"
    )
    enviar_telegram(msg)


if __name__ == '__main__':
    # Teste: envia mensagem de teste
    print("A testar notificações...")
    ok = enviar_telegram("🤖 *LottoCV Bot* iniciado com sucesso! Tudo a funcionar.")
    print(f"Telegram: {'✅ OK' if ok else '❌ Falhou (verifica o token/chat_id)'}")
