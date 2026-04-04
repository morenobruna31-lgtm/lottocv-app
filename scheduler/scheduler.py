"""
Scheduler — Executa o scraping automaticamente
Corre às 3ª e 6ª feira (dias de sorteio em CV) + verifica jackpot diariamente
"""

import schedule
import time
import logging
from datetime import datetime

log = logging.getLogger(__name__)


def job_scraping():
    """Job principal: scraping completo."""
    log.info(f"[Scheduler] A iniciar scraping — {datetime.now()}")
    from scraper.scraper import executar_scraping
    from scraper.notificacoes import verificar_e_notificar
    
    resultado = executar_scraping()
    verificar_e_notificar(resultado)


def job_verificar_jackpot():
    """Verifica jackpot diariamente e notifica se crítico."""
    from scraper.notificacoes import verificar_e_notificar
    from scraper.scraper import scrape_jackpot_totoloto
    from database.models import atualizar_jackpot
    
    jp = scrape_jackpot_totoloto()
    if jp:
        atualizar_jackpot("totoloto", jp["valor"], jp["concurso"], jp["data_sorteio"])
        verificar_e_notificar({"jackpot_totoloto": jp["valor"]})


def iniciar_scheduler():
    """Configura e arranca o scheduler."""
    
    # Sorteios do Totoloto em CV: Terça (19h) e Sexta (19h)
    schedule.every().tuesday.at("19:30").do(job_scraping)
    schedule.every().friday.at("19:30").do(job_scraping)
    
    # Verificação diária do jackpot às 09:00
    schedule.every().day.at("09:00").do(job_verificar_jackpot)
    
    log.info("✅ Scheduler iniciado.")
    log.info("   • Scraping: Terças e Sextas às 19:30")
    log.info("   • Verificação jackpot: diária às 09:00")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(message)s')
    iniciar_scheduler()
