"""
Scheduler de Alertas — combina scraping + alertas Telegram
Corre em paralelo com o bot ou de forma autónoma
"""

import sys, os, time, logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import schedule

log = logging.getLogger(__name__)


def job_scrape_e_alertar():
    """Scraping completo + verificação de alertas."""
    log.info(f"[Scheduler] A correr — {datetime.now().strftime('%H:%M')}")
    try:
        from scraper.scraper import executar_scraping
        resultado = executar_scraping()

        from telegram_bot.bot import verificar_e_alertar
        verificar_e_alertar()

        log.info(f"[Scheduler] OK — Totoloto: {resultado['novos_totoloto']} novos, "
                 f"Jackpot: {resultado['jackpot_totoloto']/1000:.0f} contos")
    except Exception as e:
        log.error(f"[Scheduler] Erro: {e}")


def job_alerta_diario():
    """Só verifica o jackpot e alerta (sem scraping completo)."""
    try:
        from scraper.scraper import scrape_jackpot_totoloto
        from database.models import atualizar_jackpot
        from telegram_bot.bot import verificar_e_alertar

        jp = scrape_jackpot_totoloto()
        if jp and jp["valor"] > 0:
            atualizar_jackpot("totoloto", jp["valor"], jp["concurso"], jp["data_sorteio"])
        verificar_e_alertar()
    except Exception as e:
        log.error(f"[Alerta diário] Erro: {e}")


def iniciar(modo: str = "standalone"):
    """
    Inicia o scheduler.
    modo='standalone': só o scheduler (sem bot)
    modo='integrado': chama o bot em thread separada
    """
    # Terça e Sexta às 19:30 (após sorteios)
    schedule.every().tuesday.at("19:30").do(job_scrape_e_alertar)
    schedule.every().friday.at("19:30").do(job_scrape_e_alertar)

    # Verificação de jackpot às 09:00 todos os dias
    schedule.every().day.at("09:00").do(job_alerta_diario)
    schedule.every().day.at("14:00").do(job_alerta_diario)

    log.info("✅ Scheduler de alertas iniciado:")
    log.info("   • Scraping: Terças e Sextas 19:30")
    log.info("   • Alerta jackpot: diário 09:00 e 14:00")

    if modo == "integrado":
        import threading
        from telegram_bot.bot import run_bot
        t = threading.Thread(target=run_bot, daemon=True)
        t.start()
        log.info("   • Bot Telegram: a correr em thread separada")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(message)s')
    modo = sys.argv[1] if len(sys.argv) > 1 else "standalone"
    iniciar(modo)
